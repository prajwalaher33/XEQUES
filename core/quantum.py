"""
xeques/core/quantum.py
──────────────────────
Proof of Quantum Control (PoQC) — Consensus Engine

Each block requires validators to simulate a seeded quantum circuit and
submit the full probability distribution P(x) = |⟨x|ψ⟩|² over all
computational basis states x ∈ {0,1}^n.

Difficulty scales with circuit depth. As real quantum hardware matures,
classical simulation becomes the bottleneck — creating a natural economic
incentive to deploy actual quantum processors as validators.

Gate set:
  H   Hadamard                  ─ creates superposition
  X   Pauli-X (NOT)             ─ bit flip
  Y   Pauli-Y                   ─ rotation
  Z   Pauli-Z                   ─ phase flip
  S   Phase gate (√Z)           ─ π/2 rotation
  T   π/8 gate                  ─ non-Clifford; needed for universality
  Rz  Parameterised Z-rotation  ─ continuous parameter
  CNOT Controlled-NOT           ─ 2-qubit entanglement
  CZ   Controlled-Z             ─ 2-qubit entanglement
"""

import numpy as np
import json
import math
from typing import List, Optional
from .crypto import sha3_hex

# ── Gate matrices ──────────────────────────────────────────────────────────

_R2 = 1.0 / math.sqrt(2)

GATE_1Q = {
    'H': np.array([[_R2,  _R2], [_R2, -_R2]], dtype=complex),
    'X': np.array([[0, 1], [1, 0]], dtype=complex),
    'Y': np.array([[0, -1j], [1j, 0]], dtype=complex),
    'Z': np.array([[1, 0], [0, -1]], dtype=complex),
    'S': np.array([[1, 0], [0, 1j]], dtype=complex),
    'T': np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex),
}

def rz(theta: float) -> np.ndarray:
    return np.array([[np.exp(-1j * theta / 2), 0],
                     [0, np.exp(1j * theta / 2)]], dtype=complex)


# ── State vector operations ────────────────────────────────────────────────

def _apply_1q(sv: np.ndarray, gate: np.ndarray, q: int, n: int) -> np.ndarray:
    """Apply single-qubit gate to qubit q of n-qubit state vector."""
    dim = 1 << n
    new = np.zeros(dim, dtype=complex)
    for idx in range(dim):
        bit = (idx >> (n - 1 - q)) & 1
        for b2 in range(2):
            amp = gate[b2, bit]
            if abs(amp) < 1e-15:
                continue
            new_idx = idx ^ ((bit ^ b2) << (n - 1 - q))
            new[new_idx] += amp * sv[idx]
    return new

def _apply_cnot(sv: np.ndarray, ctrl: int, tgt: int, n: int) -> np.ndarray:
    """Flip target qubit if control is |1⟩."""
    dim = 1 << n
    new = np.zeros(dim, dtype=complex)
    for idx in range(dim):
        c_bit = (idx >> (n - 1 - ctrl)) & 1
        if c_bit:
            flipped = idx ^ (1 << (n - 1 - tgt))
            new[flipped] += sv[idx]
        else:
            new[idx] += sv[idx]
    return new

def _apply_cz(sv: np.ndarray, ctrl: int, tgt: int, n: int) -> np.ndarray:
    """Phase flip if both qubits are |1⟩."""
    new = sv.copy()
    dim = 1 << n
    for idx in range(dim):
        if ((idx >> (n - 1 - ctrl)) & 1) and ((idx >> (n - 1 - tgt)) & 1):
            new[idx] *= -1
    return new


# ── Circuit ────────────────────────────────────────────────────────────────

class Gate:
    __slots__ = ('name', 'qubits', 'theta')

    def __init__(self, name: str, qubits: List[int], theta: float = 0.0):
        self.name   = name
        self.qubits = qubits
        self.theta  = theta

    def to_dict(self) -> dict:
        return {'g': self.name, 'q': self.qubits, 't': self.theta}

    @staticmethod
    def from_dict(d: dict) -> 'Gate':
        return Gate(d['g'], d['q'], d.get('t', 0.0))


class QuantumCircuit:
    """
    Exact state-vector simulator for n ≤ 20 qubits.
    (For n > 16, classical simulation becomes the bottleneck — the PoQC puzzle.)
    """

    def __init__(self, n_qubits: int):
        self.n = n_qubits
        self.dim = 1 << n_qubits
        self.gates: List[Gate] = []

    def h(self, q):    self.gates.append(Gate('H', [q]));    return self
    def x(self, q):    self.gates.append(Gate('X', [q]));    return self
    def y(self, q):    self.gates.append(Gate('Y', [q]));    return self
    def z(self, q):    self.gates.append(Gate('Z', [q]));    return self
    def s(self, q):    self.gates.append(Gate('S', [q]));    return self
    def t(self, q):    self.gates.append(Gate('T', [q]));    return self
    def rz(self, q, theta): self.gates.append(Gate('Rz', [q], theta)); return self
    def cnot(self, c, t):   self.gates.append(Gate('CNOT', [c, t]));   return self
    def cz(self, c, t):     self.gates.append(Gate('CZ',   [c, t]));   return self

    @classmethod
    def random(cls, n: int, depth: int, seed: int) -> 'QuantumCircuit':
        """
        Generate a reproducible pseudo-random circuit.
        Seed is derived from (prev_block_hash, block_height, difficulty)
        so no validator can predict the puzzle in advance.
        """
        rng = np.random.RandomState(seed % (2**31))
        qc  = cls(n)
        # Layer 0: full Hadamard to create uniform superposition
        for q in range(n):
            qc.h(q)
        for _ in range(depth):
            # Single-qubit layer
            for q in range(n):
                g = rng.choice(['H', 'X', 'T', 'S', 'Y'])
                qc.gates.append(Gate(g, [q]))
                if rng.rand() < 0.45:
                    qc.rz(q, float(rng.uniform(0, 2 * np.pi)))
            # Two-qubit entangling layer
            qs = list(range(n))
            rng.shuffle(qs)
            for i in range(0, n - 1, 2):
                c, t = qs[i], qs[i + 1]
                g2 = 'CNOT' if rng.rand() < 0.6 else 'CZ'
                qc.gates.append(Gate(g2, [c, t]))
        return qc

    def simulate(self) -> np.ndarray:
        """Evolve |0⟩^n through the circuit. Returns state vector."""
        sv = np.zeros(self.dim, dtype=complex)
        sv[0] = 1.0
        for gate in self.gates:
            g, q = gate.name, gate.qubits
            if g in GATE_1Q:
                sv = _apply_1q(sv, GATE_1Q[g], q[0], self.n)
            elif g == 'Rz':
                sv = _apply_1q(sv, rz(gate.theta), q[0], self.n)
            elif g == 'CNOT':
                sv = _apply_cnot(sv, q[0], q[1], self.n)
            elif g == 'CZ':
                sv = _apply_cz(sv, q[0], q[1], self.n)
        return sv

    def probabilities(self) -> np.ndarray:
        """Born rule: P(x) = |<x|ψ>|²"""
        sv = self.simulate()
        p  = np.abs(sv) ** 2
        p /= p.sum()   # re-normalise for float stability
        return p

    def fingerprint(self) -> str:
        data = json.dumps([g.to_dict() for g in self.gates], sort_keys=True)
        return sha3_hex(data.encode())

    def to_dict(self) -> dict:
        return {'n': self.n, 'gates': [g.to_dict() for g in self.gates]}

    @classmethod
    def from_dict(cls, d: dict) -> 'QuantumCircuit':
        qc = cls(d['n'])
        qc.gates = [Gate.from_dict(g) for g in d['gates']]
        return qc


# ── PoQC Puzzle ────────────────────────────────────────────────────────────

class PoQCPuzzle:
    """
    Block production puzzle:

        Input:   prev_hash (str), height (int), difficulty (int 2-12)
        Seed:    SHA3(prev_hash ‖ height ‖ difficulty)[:8] as uint64
        Circuit: random_circuit(N_QUBITS, depth=difficulty, seed)
        Answer:  probability vector P ∈ ℝ^{2^N_QUBITS}, ‖P‖₁ = 1
        Valid:   ‖P_submitted − P_true‖₁ < TOLERANCE

    Producing a ZK-proof of correct simulation is left for Phase 2
    (SNARK wrapping of circuit evaluation).
    """
    N_QUBITS  = 5        # 32 basis states — classically simulable, but costly at depth 10+
    TOLERANCE = 1e-6

    def __init__(self, height: int, prev_hash: str, difficulty: int):
        self.height     = height
        self.prev_hash  = prev_hash
        self.difficulty = max(2, min(difficulty, 12))
        seed_bytes      = (prev_hash + str(height) + str(difficulty)).encode()
        self.seed       = int(sha3_hex(seed_bytes)[:16], 16) % (2**31)
        self.circuit    = QuantumCircuit.random(self.N_QUBITS, self.difficulty, self.seed)
        self._solution: Optional[np.ndarray] = None

    @property
    def solution(self) -> np.ndarray:
        if self._solution is None:
            self._solution = self.circuit.probabilities()
        return self._solution

    def solve(self) -> np.ndarray:
        """Simulate the circuit and return the answer."""
        return self.circuit.probabilities()

    def verify(self, submitted: np.ndarray) -> bool:
        if submitted.shape != (1 << self.N_QUBITS,):
            return False
        return float(np.sum(np.abs(submitted - self.solution))) < self.TOLERANCE

    def proof_hash(self, solver_address: str) -> str:
        data = solver_address.encode() + self.solution.tobytes()
        return sha3_hex(data)

    def summary(self) -> dict:
        return {
            'height'     : self.height,
            'difficulty' : self.difficulty,
            'seed'       : self.seed,
            'n_qubits'   : self.N_QUBITS,
            'n_gates'    : len(self.circuit.gates),
            'fingerprint': self.circuit.fingerprint(),
            'n_outcomes' : 1 << self.N_QUBITS,
        }

# typing shim
Tuple_or_bool = bool
