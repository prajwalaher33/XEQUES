"""
xeques/core/pocc.py
───────────────────
Proof of Command Correctness (PoCC)

Every transaction in XEQUES is a *command* — an authorised instruction
from a wallet to the network. PoCC proves three things about every command:

  1. AUTHORISATION — it came from the wallet that claims to have sent it
                     (Lamport OTS + Merkle auth path, quantum-safe)

  2. ORDERING      — it arrived in the correct sequence for that wallet
                     (nonce + command chain hash: each command commits to
                     the hash of the previous one, forming a tamper-evident
                     chain per sender)

  3. INTEGRITY     — the command content has not been altered in transit
                     (SHA3-256 over the full command fields, bound into
                     the Lamport signature)

What PoCC is NOT:
  - It does not prove the command is economically valid (balance check
    is the ledger's job)
  - It does not produce the block (that is PoQC-VDF's job)
  - It does not evaluate fraud risk (that is the Brain AGI's job)

PoCC runs at mempool admission. A transaction that fails PoCC is rejected
before it touches the ledger, the brain, or the block candidate set.

Command chain:
  chain_hash[0]  = SHA3("GENESIS" + sender_address)
  chain_hash[n]  = SHA3(chain_hash[n-1] + command_hash[n])

This means every command is bound to every command before it.
Replaying, reordering, or dropping a command breaks the chain.
The current chain_hash is stored in the ledger per sender and
included in every PoCC proof.
"""

import time
from dataclasses import dataclass, field
from typing import Optional
from .crypto import sha3, sha3_hex, XequesWallet


# ── Command (the PoCC-wrapped transaction) ─────────────────────────────────

@dataclass
class Command:
    """
    A Command is a transaction with a PoCC proof attached.

    Fields that form the command body (all are signed):
        sender       : 40-char hex address
        receiver     : 40-char hex address
        amount       : XEQ to transfer
        fee          : XEQ to pay the block producer
        nonce        : sender's current command count (monotonic)
        prev_chain   : SHA3 of the previous command in this sender's chain
        timestamp    : unix float
        memo         : optional utf-8 string
    """
    sender     : str
    receiver   : str
    amount     : float
    fee        : float
    nonce      : int
    prev_chain : str          # chain_hash of the previous command from this sender
    timestamp  : float = field(default_factory=time.time)
    memo       : str   = ''
    pocc_proof : Optional[dict] = None   # set by attach_proof()

    def __post_init__(self):
        self._cmd_hash : Optional[str] = None
        self._chain_hash: Optional[str] = None

    # ── Hashes ──────────────────────────────────────────────────────────────

    @property
    def command_hash(self) -> str:
        """SHA3 of all command fields. This is what gets signed."""
        if self._cmd_hash is None:
            body = (
                f"{self.sender}:{self.receiver}:{self.amount}:{self.fee}:"
                f"{self.nonce}:{self.prev_chain}:{self.timestamp}:{self.memo}"
            )
            self._cmd_hash = sha3_hex(body.encode())
        return self._cmd_hash

    @property
    def chain_hash(self) -> str:
        """
        Hash that links this command into the sender's command chain.
        chain_hash[n] = SHA3(prev_chain_hash + command_hash)
        """
        if self._chain_hash is None:
            self._chain_hash = sha3_hex(
                (self.prev_chain + self.command_hash).encode()
            )
        return self._chain_hash

    # ── PoCC proof attachment ────────────────────────────────────────────────

    def attach_proof(self, wallet: XequesWallet):
        """
        Sign the command hash with the wallet's next Lamport key.
        The proof contains:
          - the Lamport signature over command_hash
          - the Merkle auth path proving the key belongs to this wallet
          - the chain_hash linking this command into the sender's history
        """
        bundle = wallet.sign(self.command_hash.encode())
        self.pocc_proof = {
            'version'   : 1,
            'cmd_hash'  : self.command_hash,
            'chain_hash': self.chain_hash,
            'sig_bundle': bundle,
        }

    # ── Verification ────────────────────────────────────────────────────────

    def verify_proof(self, expected_prev_chain: str) -> tuple:
        """
        Verify the PoCC proof. Three checks:
          1. prev_chain matches what the ledger has for this sender
          2. Lamport signature is valid over command_hash
          3. chain_hash is correctly derived

        Returns (ok: bool, reason: str)
        """
        if not self.pocc_proof:
            return False, "No PoCC proof attached"

        # Check 1: command ordering — prev_chain must match ledger state
        if self.prev_chain != expected_prev_chain:
            return False, (
                f"Command chain broken: expected prev_chain "
                f"{expected_prev_chain[:16]}… got {self.prev_chain[:16]}…"
            )

        # Check 2: Lamport signature over command_hash
        if not XequesWallet.verify_bundle(
            self.command_hash.encode(),
            self.pocc_proof['sig_bundle']
        ):
            return False, "PoCC signature invalid — command may have been tampered with"

        # Check 3: chain_hash derivation
        expected_chain = sha3_hex(
            (self.prev_chain + self.command_hash).encode()
        )
        if self.pocc_proof['chain_hash'] != expected_chain:
            return False, "chain_hash mismatch — command ordering cannot be verified"

        return True, "OK"

    # ── Serialisation ────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            'sender'    : self.sender,
            'receiver'  : self.receiver,
            'amount'    : self.amount,
            'fee'       : self.fee,
            'nonce'     : self.nonce,
            'prev_chain': self.prev_chain,
            'timestamp' : self.timestamp,
            'memo'      : self.memo,
            'pocc_proof': self.pocc_proof,
            'cmd_hash'  : self.command_hash,
            'chain_hash': self.chain_hash,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'Command':
        c = cls(
            d['sender'], d['receiver'], d['amount'], d['fee'],
            d['nonce'], d['prev_chain'], d['timestamp'],
            d.get('memo', ''), d.get('pocc_proof')
        )
        return c


# ── PoCC Registry ──────────────────────────────────────────────────────────

class PoCCRegistry:
    """
    Tracks the command chain state for every sender.

    Stored per address:
        nonce       : next expected command number
        chain_hash  : hash to include as prev_chain in the next command

    This is the ledger's source of truth for PoCC verification.
    A command that presents the wrong prev_chain is proof of either
    replay, reorder, or a missing command — all rejected.
    """

    def __init__(self):
        # address → {'nonce': int, 'chain_hash': str}
        self._state: dict = {}

    def genesis_hash(self, address: str) -> str:
        """The initial chain_hash for a new address."""
        return sha3_hex(('GENESIS' + address).encode())

    def get(self, address: str) -> dict:
        if address not in self._state:
            self._state[address] = {
                'nonce'     : 0,
                'chain_hash': self.genesis_hash(address),
            }
        return self._state[address]

    def expected_prev_chain(self, address: str) -> str:
        return self.get(address)['chain_hash']

    def expected_nonce(self, address: str) -> int:
        return self.get(address)['nonce']

    def advance(self, command: Command):
        """
        Advance the chain state after a command is confirmed on-chain.
        Called by the ledger after a command is applied to a block.
        """
        self._state[command.sender] = {
            'nonce'     : command.nonce + 1,
            'chain_hash': command.chain_hash,
        }

    def snapshot(self) -> dict:
        return dict(self._state)


# ── PoCC Verifier (stateless, used at mempool admission) ───────────────────

class PoCCVerifier:
    """
    Stateless verification helper. Pass the registry in.
    Used by the node before admitting a command to the mempool.
    """

    @staticmethod
    def verify(command: Command, registry: PoCCRegistry) -> tuple:
        """
        Full PoCC verification:
          1. Format sanity
          2. Nonce matches registry
          3. PoCC proof (signature + chain continuity + hash integrity)

        Returns (ok: bool, reason: str)
        """
        # Format
        if command.amount <= 0:
            return False, "Amount must be positive"
        if command.fee < 0.001:
            return False, "Fee below minimum (0.001 XEQ)"
        if len(command.sender) != 40 or len(command.receiver) != 40:
            return False, "Invalid address format"
        if command.sender == command.receiver:
            return False, "Self-transfer not permitted"

        # Nonce
        expected_nonce = registry.expected_nonce(command.sender)
        if command.nonce != expected_nonce:
            return False, (
                f"Nonce mismatch: expected {expected_nonce}, "
                f"got {command.nonce}"
            )

        # PoCC proof
        expected_prev = registry.expected_prev_chain(command.sender)
        ok, reason = command.verify_proof(expected_prev)
        if not ok:
            return False, reason

        return True, "PoCC verified"
