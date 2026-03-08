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

    # ── Transaction creation ────────────────────────────────────────────────

    def create_transaction(self, receiver: str, amount: float,
                           fee: float = 0.001, memo: str = '') -> Transaction:
        nonce = self.chain.ledger.nonces[self.addr]
        tx = Transaction(self.addr, receiver, amount, fee, nonce, memo=memo)
        tx.sign(self.wallet)
        return tx

    def broadcast_transaction(self, tx: Transaction) -> tuple:
        return self.chain.submit_tx(tx, brain=self.brain)

    # ── Validation ─────────────────────────────────────────────────────────

    def validate_transaction(self, tx: Transaction) -> tuple:
        """
        Three-stage validation:
          1. Format check (amounts, addresses, nonce)
          2. Signature verification (quantum-safe Lamport + Merkle proof)
          3. Brain AGI screening (SNN classification)
        Returns (ok: bool, label: str, confidence: float, reason: str)
        """
        # Stage 1: format
        ok, reason = tx.is_valid_format()
        if not ok:
            return False, 'FRAUDULENT', 1.0, reason

        # Stage 2: signature
        if tx.signature:
            if not tx.verify_signature():
                return False, 'FRAUDULENT', 1.0, "Invalid quantum-safe signature"

        # Stage 3: brain
        ns    = self.chain.ledger.network_state_for(tx.sender)
        feats = XequesBrain.extract_features(tx.to_dict(), ns)
        label_idx, conf, _, _ = self.brain.process(feats)
        label = LABELS[label_idx]

        if label_idx == 2 and conf > 0.85:
            return False, label, conf, "Brain flagged as fraudulent"
        if label_idx == 1 and conf > 0.90:
            return False, label, conf, "Brain flagged as suspicious"

        return True, label, conf, "OK"

    # ── Mining ─────────────────────────────────────────────────────────────

    def solve_poqc(self, puzzle: PoQCPuzzle):
        """Simulate the quantum circuit and return probability answer."""
        return puzzle.solve()

    def mine_one_block(self) -> Optional[Block]:
        """
        Attempt to mine the next block:
          1. Generate PoQC puzzle from (prev_hash, height, difficulty)
          2. Solve it (classical simulation for testnet)
          3. Package pending transactions
          4. Build and return block
        """
        puzzle = PoQCPuzzle(
            height    = self.chain.height + 1,
            prev_hash = self.chain.tip.block_hash,
            difficulty= self.chain.difficulty,
        )

        answer = self.solve_poqc(puzzle)

        if not puzzle.verify(answer):
            return None   # shouldn't happen in classical sim

        proof = puzzle.proof_hash(self.addr)
        txs   = self.chain.pending_txs(max_txs=50)

        block = Block(
            height      = self.chain.height + 1,
            prev_hash   = self.chain.tip.block_hash,
            transactions= txs,
            miner       = self.addr,
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
