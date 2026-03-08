"""
xeques/core/chain.py
────────────────────
Core Blockchain — Blocks, Ledger, Mempool, Tokenomics

XEQ Token:
    Total supply   : 1,000,000,000 XEQ (1 billion)
    Block reward   : 50 XEQ, halves every 210,000 blocks
    Min tx fee     : 0.001 XEQ
    Staking lock   : configurable (default 1000 blocks)
    Slashing       : 5% of stake for provable equivocation
    Governance     : quadratic voting (votes = √tokens_committed)
"""

import time
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from .crypto import sha3, sha3_hex, XequesWallet

# ── Constants ──────────────────────────────────────────────────────────────

TOTAL_SUPPLY    = 1_000_000_000   # XEQ
INITIAL_REWARD  = 50.0            # XEQ per block
HALVING_INTERVAL= 210_000         # blocks
MIN_TX_FEE      = 0.001           # XEQ
SLASH_RATE      = 0.05            # 5% of stake
BASE_APY        = 0.12            # 12% when staked_ratio → 0
STAKE_LOCK      = 1_000           # blocks


# ── Transaction ────────────────────────────────────────────────────────────

@dataclass
class Transaction:
    sender   : str      # 40-char hex address
    receiver : str      # 40-char hex address
    amount   : float
    fee      : float
    nonce    : int
    timestamp: float = field(default_factory=time.time)
    memo     : str   = ''
    signature: Optional[dict] = None

    def __post_init__(self):
        self._hash: Optional[str] = None

    @property
    def tx_hash(self) -> str:
        if self._hash is None:
            body = (f"{self.sender}:{self.receiver}:{self.amount}:{self.fee}:"
                    f"{self.nonce}:{self.timestamp}:{self.memo}")
            self._hash = sha3_hex(body.encode())
        return self._hash

    def sign(self, wallet: XequesWallet):
        self.signature = wallet.sign(self.tx_hash.encode())

    def verify_signature(self) -> bool:
        if not self.signature:
            return False
        return XequesWallet.verify_bundle(self.tx_hash.encode(), self.signature)

    def is_valid_format(self) -> Tuple[bool, str]:
        if self.amount <= 0:
            return False, "Amount must be positive"
        if self.fee < MIN_TX_FEE:
            return False, f"Fee must be ≥ {MIN_TX_FEE} XEQ"
        if len(self.sender) != 40 or len(self.receiver) != 40:
            return False, "Invalid address format"
        if self.sender == self.receiver:
            return False, "Self-transfer not allowed"
        return True, "OK"

    def to_dict(self) -> dict:
        return {
            'sender'   : self.sender,
            'receiver' : self.receiver,
            'amount'   : self.amount,
            'fee'      : self.fee,
            'nonce'    : self.nonce,
            'timestamp': self.timestamp,
            'memo'     : self.memo,
            'sig'      : self.signature,
            'hash'     : self.tx_hash,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'Transaction':
        tx = cls(d['sender'], d['receiver'], d['amount'], d['fee'],
                 d['nonce'], d['timestamp'], d.get('memo', ''), d.get('sig'))
        return tx


# ── Block ──────────────────────────────────────────────────────────────────

@dataclass
class Block:
    height      : int
    prev_hash   : str
    transactions: List[Transaction]
    miner       : str        # address
    poqc_proof  : str        # sha3(solver_address + solution_bytes)
    difficulty  : int
    timestamp   : float = field(default_factory=time.time)
    extra       : dict  = field(default_factory=dict)

    def __post_init__(self):
        self._hash: Optional[str] = None

    @property
    def block_hash(self) -> str:
        if self._hash is None:
            tx_root = self._tx_merkle_root()
            body = (f"{self.height}:{self.prev_hash}:{tx_root}:{self.miner}:"
                    f"{self.poqc_proof}:{self.difficulty}:{self.timestamp}")
            self._hash = sha3_hex(body.encode())
        return self._hash

    def _tx_merkle_root(self) -> str:
        if not self.transactions:
            return sha3_hex(b'empty')
        from .crypto import MerkleTree
        leaves = [sha3(tx.tx_hash.encode()) for tx in self.transactions]
        return MerkleTree(leaves).root.hex()

    def to_dict(self) -> dict:
        return {
            'height'    : self.height,
            'prev_hash' : self.prev_hash,
            'txs'       : [tx.to_dict() for tx in self.transactions],
            'miner'     : self.miner,
            'poqc_proof': self.poqc_proof,
            'difficulty': self.difficulty,
            'timestamp' : self.timestamp,
            'hash'      : self.block_hash,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'Block':
        txs = [Transaction.from_dict(t) for t in d.get('txs', [])]
        b = cls(d['height'], d['prev_hash'], txs, d['miner'],
                d['poqc_proof'], d['difficulty'], d['timestamp'])
        b._hash = d.get('hash')
        return b


# ── Ledger ─────────────────────────────────────────────────────────────────

class Ledger:
    """In-memory world state: balances, nonces, transaction index."""

    def __init__(self):
        self.balances   : Dict[str, float] = {}
        self.nonces     : Dict[str, int]   = defaultdict(int)
        self.tx_index   : Dict[str, Transaction] = {}
        self.known_addrs: set = set()
        self.tx_history : List[str] = []   # list of tx_hashes in order
        self.last_ts    : Dict[str, float] = {}
        self.tx_rates   : Dict[str, int]   = defaultdict(int)
        self._total_amount = 0.0
        self._total_txs    = 0

    @property
    def avg_amount(self) -> float:
        return (self._total_amount / self._total_txs) if self._total_txs else 100.0

    def apply_tx(self, tx: Transaction, height: int) -> Tuple[bool, str]:
        ok, reason = tx.is_valid_format()
        if not ok:
            return False, reason
        sender_bal = self.balances.get(tx.sender, 0.0)
        total_cost = tx.amount + tx.fee
        if sender_bal < total_cost:
            return False, f"Insufficient balance: {sender_bal:.4f} < {total_cost:.4f}"
        if self.nonces[tx.sender] != tx.nonce:
            return False, f"Nonce mismatch: expected {self.nonces[tx.sender]}, got {tx.nonce}"
        # Apply
        self.balances[tx.sender]   = sender_bal - total_cost
        self.balances[tx.receiver] = self.balances.get(tx.receiver, 0.0) + tx.amount
        self.nonces[tx.sender]    += 1
        self.known_addrs.add(tx.receiver)
        self.tx_index[tx.tx_hash]  = tx
        self.tx_history.append(tx.tx_hash)
        self.last_ts[tx.sender]    = tx.timestamp
        self.tx_rates[tx.sender]  += 1
        self._total_amount += tx.amount
        self._total_txs    += 1
        return True, "OK"

    def credit(self, address: str, amount: float):
        """Credit XEQ (used for block rewards)."""
        self.balances[address] = self.balances.get(address, 0.0) + amount

    def network_state_for(self, sender: str) -> dict:
        """Package the network state for brain feature extraction."""
        return {
            'balances'   : self.balances,
            'known_addrs': self.known_addrs,
            'avg_amount' : self.avg_amount,
            'tx_rates'   : dict(self.tx_rates),
            'nonces'     : dict(self.nonces),
            'last_ts'    : dict(self.last_ts),
        }

    def snapshot(self) -> dict:
        return {
            'balances'   : dict(self.balances),
            'nonces'     : dict(self.nonces),
            'known_addrs': list(self.known_addrs),
            'total_txs'  : self._total_txs,
            'avg_amount' : self.avg_amount,
        }


# ── Staking ────────────────────────────────────────────────────────────────

@dataclass
class StakeRecord:
    validator : str
    amount    : float
    locked_at : int
    unlock_at : int

class StakingModule:
    def __init__(self):
        self.stakes: Dict[str, StakeRecord] = {}

    def stake(self, validator: str, amount: float, height: int,
              ledger: Ledger, lock: int = STAKE_LOCK) -> Tuple[bool, str]:
        if ledger.balances.get(validator, 0) < amount:
            return False, "Insufficient balance"
        ledger.balances[validator] = ledger.balances.get(validator, 0) - amount
        existing = self.stakes.get(validator)
        if existing:
            existing.amount   += amount
            existing.unlock_at = height + lock
        else:
            self.stakes[validator] = StakeRecord(validator, amount, height, height + lock)
        return True, "OK"

    def unstake(self, validator: str, height: int, ledger: Ledger) -> Tuple[bool, str]:
        rec = self.stakes.get(validator)
        if not rec:
            return False, "No stake found"
        if height < rec.unlock_at:
            return False, f"Locked until block {rec.unlock_at}"
        ledger.credit(validator, rec.amount)
        del self.stakes[validator]
        return True, "OK"

    def slash(self, validator: str, ledger: Ledger) -> float:
        rec = self.stakes.get(validator)
        if not rec:
            return 0.0
        slash_amt = rec.amount * SLASH_RATE
        rec.amount -= slash_amt
        return slash_amt

    @property
    def total_staked(self) -> float:
        return sum(r.amount for r in self.stakes.values())

    def current_apy(self) -> float:
        ratio = self.total_staked / TOTAL_SUPPLY
        return BASE_APY * (1 - ratio)

    def staking_snapshot(self) -> dict:
        return {
            'total_staked'   : self.total_staked,
            'n_validators'   : len(self.stakes),
            'current_apy_pct': round(self.current_apy() * 100, 4),
            'validators'     : {
                v: {'staked': r.amount, 'unlock_at': r.unlock_at}
                for v, r in self.stakes.items()
            }
        }


# ── Governance ─────────────────────────────────────────────────────────────

import math

@dataclass
class Proposal:
    pid      : int
    proposer : str
    title    : str
    body     : str
    height   : int
    vote_end : int   # block height when voting closes
    yes_raw  : float = 0.0
    no_raw   : float = 0.0
    executed : bool  = False

    @property
    def yes_votes(self): return math.sqrt(max(self.yes_raw, 0))
    @property
    def no_votes(self):  return math.sqrt(max(self.no_raw, 0))
    @property
    def passed(self):    return self.yes_votes > self.no_votes and self.yes_raw >= 1000

    def to_dict(self) -> dict:
        return {
            'pid'      : self.pid,
            'proposer' : self.proposer,
            'title'    : self.title,
            'body'     : self.body,
            'height'   : self.height,
            'vote_end' : self.vote_end,
            'yes_raw'  : self.yes_raw,
            'no_raw'   : self.no_raw,
            'yes_votes': round(self.yes_votes, 4),
            'no_votes' : round(self.no_votes, 4),
            'passed'   : self.passed,
            'executed' : self.executed,
        }

class GovernanceModule:
    def __init__(self):
        self.proposals: List[Proposal] = []
        self.votes: Dict[str, Dict[int, float]] = defaultdict(dict)
        self._pid = 0

    def submit(self, proposer: str, title: str, body: str,
               height: int, voting_period: int = 14400) -> Proposal:
        p = Proposal(self._pid, proposer, title, body, height, height + voting_period)
        self.proposals.append(p)
        self._pid += 1
        return p

    def vote(self, voter: str, pid: int, yes: bool,
             tokens: float) -> Tuple[bool, str, float]:
        if pid >= len(self.proposals):
            return False, "Proposal not found", 0.0
        if pid in self.votes[voter]:
            return False, "Already voted", 0.0
        p = self.proposals[pid]
        quad_votes = math.sqrt(tokens)
        if yes:
            p.yes_raw += tokens
        else:
            p.no_raw  += tokens
        self.votes[voter][pid] = tokens
        return True, "Vote recorded", quad_votes


# ── Blockchain ─────────────────────────────────────────────────────────────

class Blockchain:
    """
    Main chain object. Owns: chain[], ledger, staking, governance, mempool.
    """

    GENESIS_ACCOUNTS = {
        # address → initial balance for testnet
        # In mainnet these will be community/foundation allocations
    }

    def __init__(self, network_id: str = 'xeques-testnet-1'):
        self.network_id  = network_id
        self.chain      : List[Block]       = []
        self.ledger     : Ledger            = Ledger()
        self.staking    : StakingModule     = StakingModule()
        self.governance : GovernanceModule  = GovernanceModule()
        self.mempool    : List[Transaction] = []
        self.difficulty  = 3
        self._genesis()

    def _genesis(self):
        for addr, bal in self.GENESIS_ACCOUNTS.items():
            self.ledger.credit(addr, bal)
        genesis = Block(
            height=0, prev_hash='0' * 64,
            transactions=[], miner='GENESIS',
            poqc_proof='0' * 64, difficulty=0,
            timestamp=0.0)
        self.chain.append(genesis)

    @property
    def height(self) -> int:
        return len(self.chain) - 1

    @property
    def tip(self) -> Block:
        return self.chain[-1]

    def block_reward(self) -> float:
        halvings = self.height // HALVING_INTERVAL
        return INITIAL_REWARD / (2 ** halvings)

    def add_block(self, block: Block, brain=None) -> Tuple[bool, str]:
        """Validate and append a block."""
        if block.prev_hash != self.tip.block_hash:
            return False, f"Bad prev_hash: expected {self.tip.block_hash[:16]}…"
        if block.height != self.height + 1:
            return False, f"Bad height: expected {self.height + 1}"
        # Apply transactions
        fee_total = 0.0
        for tx in block.transactions:
            ok, reason = self.ledger.apply_tx(tx, block.height)
            if not ok:
                return False, f"TX {tx.tx_hash[:16]}… failed: {reason}"
            fee_total += tx.fee
            # Brain learning: confirmed tx → VALID
            if brain:
                ns = self.ledger.network_state_for(tx.sender)
                feats = brain.extract_features(tx.to_dict(), ns)
                brain.process(feats)
                brain.learn(0)   # confirmed = VALID
        # Block reward + fees to miner
        self.ledger.credit(block.miner, self.block_reward() + fee_total)
        self.chain.append(block)
        # Remove confirmed txs from mempool
        confirmed = {tx.tx_hash for tx in block.transactions}
        self.mempool = [tx for tx in self.mempool if tx.tx_hash not in confirmed]
        # Dynamic difficulty adjustment (every 100 blocks, target 10s/block)
        if block.height % 100 == 0 and block.height > 0:
            self._adjust_difficulty()
        return True, "OK"

    def _adjust_difficulty(self):
        """Simple difficulty adjustment: aim for 10s per block."""
        if len(self.chain) < 101:
            return
        recent = self.chain[-100:]
        elapsed = recent[-1].timestamp - recent[0].timestamp
        avg_block_time = elapsed / 99
        target = 10.0   # seconds
        if avg_block_time < target * 0.8:
            self.difficulty = min(self.difficulty + 1, 12)
        elif avg_block_time > target * 1.2:
            self.difficulty = max(self.difficulty - 1, 2)

    def submit_tx(self, tx: Transaction, brain=None) -> Tuple[bool, str]:
        """Add a transaction to the mempool after validation."""
        ok, reason = tx.is_valid_format()
        if not ok:
            return False, reason
        # Duplicate check
        if any(t.tx_hash == tx.tx_hash for t in self.mempool):
            return False, "Duplicate transaction"
        # Brain pre-screening
        if brain:
            ns = self.ledger.network_state_for(tx.sender)
            feats = brain.extract_features(tx.to_dict(), ns)
            label, conf, _, _ = brain.process(feats)
            if label == 2 and conf > 0.8:   # high-confidence FRAUDULENT
                return False, f"Brain rejected: FRAUDULENT (conf={conf:.2f})"
        self.mempool.append(tx)
        return True, "Accepted into mempool"

    def pending_txs(self, max_txs: int = 50) -> List[Transaction]:
        """Return top transactions by fee for inclusion in next block."""
        return sorted(self.mempool, key=lambda tx: tx.fee, reverse=True)[:max_txs]

    def stats(self) -> dict:
        return {
            'network_id'    : self.network_id,
            'height'        : self.height,
            'tip_hash'      : self.tip.block_hash,
            'difficulty'    : self.difficulty,
            'block_reward'  : self.block_reward(),
            'mempool_size'  : len(self.mempool),
            'total_txs'     : self.ledger._total_txs,
            'n_accounts'    : len(self.ledger.balances),
            'staking'       : self.staking.staking_snapshot(),
            'n_proposals'   : len(self.governance.proposals),
        }

    def export_chain(self) -> list:
        return [b.to_dict() for b in self.chain]
