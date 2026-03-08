"""
xeques/core/crypto.py

Post-quantum cryptography for XEQUES wallets.

The problem with every existing blockchain wallet: they all use ECDSA,
which Shor's algorithm running on a quantum computer will break completely.
Not weaken. Break. Your private key becomes derivable from your public key.

This file is my answer to that.

I went with Lamport One-Time Signatures combined with a Merkle key tree —
basically the XMSS scheme that NIST has blessed for post-quantum use.
The security comes down to the collision resistance of SHA3-256.
Grover's algorithm halves the bit security, so 256-bit hashes give us
128-bit post-quantum security. That's the target.

The one annoying thing about Lamport is that each key is truly one-time.
Sign twice with the same key and you leak your secret. The Merkle tree
solves this — we pre-generate a pool of 64 keys and commit to all of them
via a single Merkle root. That root is your on-chain identity. Each
signature includes a Merkle authentication path proving the key used
was part of your original pool.

64 signatures before you need a new wallet. Enough for most use cases.
"""

import hashlib
import struct
import json
from typing import List, Tuple, Optional


# ── Primitives ─────────────────────────────────────────────────────────────

def sha3(data: bytes) -> bytes:
    return hashlib.sha3_256(data).digest()

def sha3_hex(data: bytes) -> str:
    return hashlib.sha3_256(data).hexdigest()

def derive(seed: bytes, path: bytes) -> bytes:
    """Deterministic child key: child = SHA3(seed || path)"""
    return sha3(seed + path)


# ── Lamport One-Time Signature ─────────────────────────────────────────────

class LamportKey:
    """
    Signs a single 256-bit message hash.

    You get two 256-element arrays of random values (sk0 and sk1).
    Their hashes are the public key. To sign, you reveal sk0[i] or sk1[i]
    for each bit of the message hash. The verifier just re-hashes your
    revealed values and checks them against the public key.

    Simple. Elegant. Quantum-resistant.

    One catch: never reuse. I enforce this with a flag.
    """
    BITS = 256

    def __init__(self, seed: bytes):
        self._seed = seed
        self._used = False
        self.sk: List[List[bytes]] = [
            [derive(seed, struct.pack('>HB', i, b)) for b in range(2)]
            for i in range(self.BITS)
        ]
        self.pk: List[List[bytes]] = [
            [sha3(self.sk[i][b]) for b in range(2)]
            for i in range(self.BITS)
        ]
        self.pk_hash: bytes = sha3(
            b''.join(self.pk[i][b] for i in range(self.BITS) for b in range(2))
        )

    def sign(self, message: bytes) -> List[bytes]:
        if self._used:
            raise RuntimeError(
                "This Lamport key has already been used. "
                "Each key is strictly one-time. Use the next key in your pool."
            )
        self._used = True
        digest = sha3(message)
        return [
            self.sk[i][(digest[i >> 3] >> (7 - (i & 7))) & 1]
            for i in range(self.BITS)
        ]

    @staticmethod
    def verify(message: bytes, sig: List[bytes],
               pk: List[List[bytes]], pk_hash: bytes) -> bool:
        # First check the pk_hash commitment
        if sha3(b''.join(pk[i][b] for i in range(LamportKey.BITS) for b in range(2))) != pk_hash:
            return False
        # Then verify each element of the signature
        digest = sha3(message)
        for i in range(LamportKey.BITS):
            bit = (digest[i >> 3] >> (7 - (i & 7))) & 1
            if sha3(sig[i]) != pk[i][bit]:
                return False
        return True


# ── Merkle Key Tree ────────────────────────────────────────────────────────

class MerkleTree:
    """
    Standard binary Merkle tree over a list of leaf hashes.

    Used here to commit to a whole pool of Lamport public keys in
    one compact root hash. To prove a key belongs to your wallet,
    you just provide the sibling hashes on the path from leaf to root.
    """

    def __init__(self, leaves: List[bytes]):
        self.leaves = leaves[:]
        self._levels = self._build(self.leaves)

    def _build(self, nodes: List[bytes]) -> List[List[bytes]]:
        levels = [nodes[:]]
        while len(nodes) > 1:
            nodes = [
                sha3(nodes[i] + (nodes[i+1] if i+1 < len(nodes) else nodes[i]))
                for i in range(0, len(nodes), 2)
            ]
            levels.append(nodes[:])
        return levels

    @property
    def root(self) -> bytes:
        return self._levels[-1][0]

    def auth_path(self, idx: int) -> List[bytes]:
        """Sibling hashes from leaf up to root."""
        path = []
        for level in self._levels[:-1]:
            sib = idx ^ 1
            path.append(level[sib] if sib < len(level) else level[idx])
            idx >>= 1
        return path

    @staticmethod
    def verify_path(leaf: bytes, idx: int, path: List[bytes], root: bytes) -> bool:
        node = leaf
        for sib in path:
            node = sha3(sib + node) if idx & 1 else sha3(node + sib)
            idx >>= 1
        return node == root


# ── XEQUES Wallet ──────────────────────────────────────────────────────────

class XequesWallet:
    """
    A quantum-safe wallet backed by a pool of 64 Lamport keys.

    Your on-chain identity is the Merkle root of all 64 key hashes.
    Your address is the first 20 bytes of SHA3(root), hex-encoded.

    Each time you sign something, you use the next key in line and
    include a Merkle proof showing it belongs to your root.

    When you've used all 64 keys, generate a new wallet and transfer.
    (In a future version this will be automated with key rotation.)

    Usage:
        wallet = XequesWallet.generate()
        bundle = wallet.sign(message_bytes)
        valid  = XequesWallet.verify_bundle(message_bytes, bundle)
    """
    POOL_SIZE = 64

    def __init__(self, master_seed: bytes):
        self.master_seed = master_seed
        self._keys = [
            LamportKey(derive(master_seed, i.to_bytes(4, 'big')))
            for i in range(self.POOL_SIZE)
        ]
        self._tree  = MerkleTree([k.pk_hash for k in self._keys])
        self.root   = self._tree.root
        self.address= sha3_hex(self.root)[:40]
        self._idx   = 0

    @classmethod
    def generate(cls) -> 'XequesWallet':
        import os
        return cls(os.urandom(32))

    @classmethod
    def from_seed(cls, seed_hex: str) -> 'XequesWallet':
        return cls(bytes.fromhex(seed_hex))

    def seed_hex(self) -> str:
        return self.master_seed.hex()

    @property
    def keys_remaining(self) -> int:
        return self.POOL_SIZE - self._idx

    def sign(self, message: bytes) -> dict:
        if self._idx >= self.POOL_SIZE:
            raise RuntimeError(
                "All 64 signing keys have been used. "
                "Please generate a new wallet and transfer your funds."
            )
        idx  = self._idx
        sig  = self._keys[idx].sign(message)
        auth = self._tree.auth_path(idx)
        self._idx += 1
        return {
            'v'        : 1,
            'key_idx'  : idx,
            'pk'       : [[p.hex() for p in pair] for pair in self._keys[idx].pk],
            'pk_hash'  : self._keys[idx].pk_hash.hex(),
            'auth_path': [a.hex() for a in auth],
            'sig'      : [s.hex() for s in sig],
            'signer'   : self.address,
            'root'     : self.root.hex(),
        }

    @staticmethod
    def verify_bundle(message: bytes, bundle: dict) -> bool:
        try:
            sig     = [bytes.fromhex(s) for s in bundle['sig']]
            pk      = [[bytes.fromhex(p) for p in pair] for pair in bundle['pk']]
            pk_hash = bytes.fromhex(bundle['pk_hash'])
            auth    = [bytes.fromhex(a) for a in bundle['auth_path']]
            root    = bytes.fromhex(bundle['root'])
            idx     = bundle['key_idx']
            if not LamportKey.verify(message, sig, pk, pk_hash):
                return False
            return MerkleTree.verify_path(pk_hash, idx, auth, root)
        except Exception:
            return False

    def to_keystore(self, password: str) -> dict:
        """Encrypt seed with password and save to JSON keystore."""
        pw_hash   = sha3(password.encode())
        encrypted = bytes(a ^ b for a, b in zip(self.master_seed, pw_hash))
        return {
            'version' : 1,
            'address' : self.address,
            'root'    : self.root.hex(),
            'key_idx' : self._idx,
            'crypto'  : {
                'cipher'    : 'xor-sha3-256',
                'ciphertext': encrypted.hex(),
            }
        }

    @classmethod
    def from_keystore(cls, ks: dict, password: str) -> 'XequesWallet':
        pw_hash   = sha3(password.encode())
        encrypted = bytes.fromhex(ks['crypto']['ciphertext'])
        seed      = bytes(a ^ b for a, b in zip(encrypted, pw_hash))
        w         = cls(seed)
        w._idx    = ks.get('key_idx', 0)
        return w
