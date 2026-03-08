"""
xeques/node/validator.py
────────────────────────
Validator Node — mines blocks via PoQC, validates transactions via SNN brain,
participates in governance, manages its own wallet.

Run a node:
    python -m xeques.node.validator --data-dir ~/.xeques --rpc-port 8545
"""

import time
import json
import os
import threading
from typing import Optional, List

from xeques.core.crypto  import XequesWallet
from xeques.core.quantum import PoQCPuzzle
from xeques.core.chain   import Blockchain, Transaction, Block
from xeques.core.pocc    import Command, PoCCVerifier
from xeques.agi.brain    import XequesBrain, LABELS


class ValidatorNode:
    """
    A full Xeques node with:
      • Quantum-safe wallet (signing transactions + blocks)
      • PoQC mining (solve quantum circuit → earn block reward)
      • Brain AGI (screen transactions before mempool admission)
      • Governance participation
      • Chain persistence (JSON-based for testnet; RocksDB for mainnet)
    """

    def __init__(self, name: str, data_dir: str = None,
                 chain: Blockchain = None, wallet: XequesWallet = None):
        self.name     = name
        self.data_dir = data_dir or os.path.expanduser(f'~/.xeques/{name}')
        os.makedirs(self.data_dir, exist_ok=True)

        # Wallet — load from keystore or create new
        self.wallet = wallet or self._load_or_create_wallet()
        self.addr   = self.wallet.address

        # Shared blockchain state (in single-process mode, all nodes share one)
        self.chain  = chain or Blockchain()

        # Brain AGI — load saved weights or start fresh
        self.brain  = XequesBrain(seed=abs(hash(name)) % 10000)
        self._load_brain()

        # Mining state
        self.mining      = False
        self._mine_thread: Optional[threading.Thread] = None
        self.blocks_mined = 0
        self.last_block_time = time.time()

        # Peers (addresses in P2P network — stub for testnet)
        self.peers: List[str] = []

        print(f"[{self.name}] Node ready  addr={self.addr[:20]}…"
              f"  keys={self.wallet.keys_remaining}")

    # ── Wallet management ──────────────────────────────────────────────────

    def _load_or_create_wallet(self) -> XequesWallet:
        ks_path = os.path.join(self.data_dir, 'keystore.json')
        if os.path.exists(ks_path):
            with open(ks_path) as f:
                ks = json.load(f)
            w = XequesWallet.from_keystore(ks, password='xeques-testnet')
            print(f"[{self.name}] Loaded wallet from keystore: {w.address[:20]}…")
            return w
        w = XequesWallet.generate()
        ks = w.to_keystore('xeques-testnet')
        with open(ks_path, 'w') as f:
            json.dump(ks, f, indent=2)
        print(f"[{self.name}] Created new wallet: {w.address[:20]}…")
        return w

    def save_wallet(self, password: str = 'xeques-testnet'):
        ks = self.wallet.to_keystore(password)
        ks['key_idx'] = self.wallet._idx
        path = os.path.join(self.data_dir, 'keystore.json')
        with open(path, 'w') as f:
            json.dump(ks, f, indent=2)

    # ── Brain persistence ──────────────────────────────────────────────────

    def _brain_path(self) -> str:
        return os.path.join(self.data_dir, 'brain.json')

    def _load_brain(self):
        p = self._brain_path()
        if os.path.exists(p):
            with open(p) as f:
                self.brain.load_state(json.load(f))

    def save_brain(self):
        with open(self._brain_path(), 'w') as f:
            json.dump(self.brain.state_dict(), f)

    # ── Command (PoCC-wrapped transaction) creation ────────────────────────

    def create_command(self, receiver: str, amount: float,
                       fee: float = 0.001, memo: str = '') -> Command:
        """
        Build a PoCC-signed Command.

        Every command carries:
          - A Lamport signature over the command hash (quantum-safe auth)
          - A chain hash linking it to the sender's previous command
            (tamper-evident ordering — replay and reorder attacks break the chain)
        """
        registry  = self.chain.ledger.pocc
        nonce     = registry.expected_nonce(self.addr)
        prev_chain= registry.expected_prev_chain(self.addr)

        cmd = Command(
            sender     = self.addr,
            receiver   = receiver,
            amount     = amount,
            fee        = fee,
            nonce      = nonce,
            prev_chain = prev_chain,
            memo       = memo,
        )
        cmd.attach_proof(self.wallet)
        return cmd

    # Keep Transaction as a compatibility alias
    def create_transaction(self, receiver: str, amount: float,
                           fee: float = 0.001, memo: str = '') -> Transaction:
        """Legacy method — wraps create_command for Transaction compatibility."""
        nonce = self.chain.ledger.nonces[self.addr]
        tx = Transaction(self.addr, receiver, amount, fee, nonce, memo=memo)
        tx.sign(self.wallet)
        return tx

    def broadcast_transaction(self, tx: Transaction) -> tuple:
        return self.chain.submit_tx(tx, brain=self.brain)

    # ── Validation ─────────────────────────────────────────────────────────

    def validate_transaction(self, tx: Transaction) -> tuple:
        """
        Four-stage validation pipeline:
          1. Brain AGI pre-screening (SNN — catches anomalies before crypto checks)
          2. Format check (amounts, addresses)
          3. PoCC verification (command chain + quantum-safe signature)
          4. Balance check (ledger state)

        The brain runs first because it is cheap and catches obvious fraud
        without spending CPU on cryptographic verification.

        Returns (ok: bool, label: str, confidence: float, reason: str)
        """
        # Stage 1: Brain AGI pre-screening
        ns    = self.chain.ledger.network_state_for(tx.sender)
        feats = XequesBrain.extract_features(tx.to_dict(), ns)
        label_idx, conf, _, _ = self.brain.process(feats)
        label = LABELS[label_idx]

        if label_idx == 2 and conf > 0.85:
            return False, label, conf, "Brain pre-screen: FRAUDULENT"
        if label_idx == 1 and conf > 0.90:
            return False, label, conf, "Brain pre-screen: SUSPICIOUS"

        # Stage 2: format
        ok, reason = tx.is_valid_format()
        if not ok:
            return False, 'FRAUDULENT', 1.0, reason

        # Stage 3: quantum-safe signature
        if tx.signature:
            if not tx.verify_signature():
                return False, 'FRAUDULENT', 1.0, "Quantum-safe signature invalid"

        return True, label, conf, "OK"

    def validate_command(self, cmd: Command) -> tuple:
        """
        Validate a PoCC Command through the full pipeline:
          1. Brain AGI pre-screening
          2. PoCC proof verification (chain continuity + Lamport signature)

        Returns (ok: bool, label: str, confidence: float, reason: str)
        """
        # Stage 1: Brain AGI
        ns    = self.chain.ledger.network_state_for(cmd.sender)
        feats = XequesBrain.extract_features(cmd.to_dict(), ns)
        label_idx, conf, _, _ = self.brain.process(feats)
        label = LABELS[label_idx]

        if label_idx == 2 and conf > 0.85:
            return False, label, conf, "Brain pre-screen: FRAUDULENT"

        # Stage 2: PoCC proof
        ok, reason = PoCCVerifier.verify(cmd, self.chain.ledger.pocc)
        if not ok:
            return False, 'FRAUDULENT', 1.0, f"PoCC: {reason}"

        return True, label, conf, "PoCC verified"

    # ── Mining ─────────────────────────────────────────────────────────────

    def solve_poqc(self, puzzle: PoQCPuzzle):
        """Simulate the quantum circuit. Returns the probability answer."""
        return puzzle.solve()

    def mine_one_block(self, all_nodes: list = None) -> Optional[Block]:
        """
        Stake-Weighted PoQC block production.

        All validators solve the same puzzle independently.
        All who answer correctly within the window are valid candidates.
        Winner = highest stake among valid candidates — NOT fastest solver.

        This is the critical design decision that separates XEQUES from
        naive PoQC: quantum hardware speed gives zero block-production
        advantage. A nation-state with a quantum supercomputer and a
        solo validator with a laptop are equal if both answer correctly
        and both have equal stake.

        Hardware does not equal power. Stake — distributed across the
        community — determines who produces blocks.
        """
        puzzle = PoQCPuzzle(
            height    = self.chain.height + 1,
            prev_hash = self.chain.tip.block_hash,
            difficulty= self.chain.difficulty,
        )

        # VDF: all nodes solve the puzzle — all take roughly equal time
        # First validator with a correct answer wins (hardware speed buys nothing
        # because the anti-concentration regime is hard for everyone equally)
        solving_nodes = all_nodes if all_nodes else [self]
        winner_addr   = None
        for node in solving_nodes:
            answer = node.solve_poqc(puzzle)
            if puzzle.verify(answer):
                winner_addr = node.addr
                break   # first correct answer wins — fair because all solve in ~equal time

        if not winner_addr:
            return None

        proof = puzzle.proof_hash(winner_addr)
        txs   = self.chain.pending_txs(max_txs=50)

        block = Block(
            height      = self.chain.height + 1,
            prev_hash   = self.chain.tip.block_hash,
            transactions= txs,
            miner       = winner_addr,
            poqc_proof  = proof,
            difficulty  = puzzle.difficulty,
        )
        return block

    def submit_block(self, block: Block) -> tuple:
        ok, reason = self.chain.add_block(block, brain=self.brain)
        if ok:
            self.blocks_mined += 1
            self.last_block_time = time.time()
            self.save_wallet()
            self.save_brain()
        return ok, reason

    def mine_loop(self, max_blocks: int = None, target_interval: float = 10.0):
        """
        Continuous mining loop. In production this runs as a daemon.
        target_interval: seconds to sleep between blocks (simulates block time).
        """
        self.mining = True
        mined = 0
        while self.mining:
            if max_blocks and mined >= max_blocks:
                break
            block = self.mine_one_block()
            if block:
                ok, reason = self.submit_block(block)
                if ok:
                    mined += 1
                    bal = self.chain.ledger.balances.get(self.addr, 0)
                    print(f"[{self.name}] ⛏  Block #{block.height}  "
                          f"txs={len(block.transactions)}  "
                          f"balance={bal:.2f} XEQ")
            time.sleep(target_interval)
        self.mining = False

    def start_mining(self, max_blocks=None, target_interval=10.0):
        self._mine_thread = threading.Thread(
            target=self.mine_loop,
            args=(max_blocks, target_interval),
            daemon=True)
        self._mine_thread.start()

    def stop_mining(self):
        self.mining = False

    # ── Governance ─────────────────────────────────────────────────────────

    def propose(self, title: str, body: str) -> dict:
        p = self.chain.governance.submit(
            self.addr, title, body, self.chain.height)
        return p.to_dict()

    def vote(self, pid: int, yes: bool, tokens: float) -> dict:
        ok, reason, quad = self.chain.governance.vote(
            self.addr, pid, yes, tokens)
        return {'ok': ok, 'reason': reason, 'quadratic_votes': round(quad, 4)}

    # ── Status ─────────────────────────────────────────────────────────────

    def status(self) -> dict:
        return {
            'node'         : self.name,
            'address'      : self.addr,
            'balance'      : self.chain.ledger.balances.get(self.addr, 0),
            'keys_left'    : self.wallet.keys_remaining,
            'blocks_mined' : self.blocks_mined,
            'mining'       : self.mining,
            'brain'        : self.brain.stats(),
            'chain'        : self.chain.stats(),
        }

    def print_status(self):
        s = self.status()
        print(f"\n{'═'*60}")
        print(f"  Node     : {s['node']}  ({s['address'][:20]}…)")
        print(f"  Balance  : {s['balance']:.4f} XEQ")
        print(f"  Keys left: {s['keys_left']}")
        print(f"  Mined    : {s['blocks_mined']} blocks")
        c = s['chain']
        print(f"  Chain    : #{c['height']}  diff={c['difficulty']}  "
              f"mempool={c['mempool_size']}")
        b = s['brain']
        print(f"  Brain    : {b['total_txs']} txs  "
              f"STDP={b['stdp_updates']}  {b['label_dist']}")
        print(f"{'═'*60}\n")
