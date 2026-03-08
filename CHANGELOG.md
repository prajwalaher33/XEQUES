# Changelog

All notable changes to XEQUES are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Planned for v0.2
- P2P networking layer (real nodes communicating over TCP)
- JSON-RPC API endpoint for wallet and tool integrations
- Block explorer (self-contained HTML)
- Unit test suite for `core/crypto.py` and `core/quantum.py`
- Persistent chain storage (LevelDB)

---

## [0.1.0] — 2026-03-09

Initial testnet release.

### Added
- **Post-quantum wallets** (`core/crypto.py`)
  - Lamport One-Time Signature scheme over SHA3-256
  - Merkle key pool (64 keys per wallet, XMSS-style)
  - Keystore encryption and restore
  - 2¹²⁸ post-quantum security under Grover's algorithm

- **Proof of Quantum Control** (`core/quantum.py`)
  - Exact state-vector simulator for n-qubit circuits
  - Gate set: H, X, Y, Z, S, T, Rz, CNOT, CZ
  - Seeded random circuit generation from block context
  - Born rule probability verification: ‖P̂ − P_true‖₁ < 10⁻⁶
  - Difficulty scaling by circuit depth

- **Blockchain core** (`core/chain.py`)
  - Block production and validation
  - In-memory ledger with nonce and balance tracking
  - Transaction mempool with fee-priority ordering
  - Dynamic difficulty adjustment (targets 10s per block)
  - Staking module with elastic APY and slashing
  - Governance module with quadratic voting

- **Brain AGI layer** (`agi/brain.py`)
  - Leaky Integrate-and-Fire spiking neural network
  - Topology: INPUT(7) → HIDDEN(20) → OUTPUT(3)
  - STDP synaptic learning rule
  - Transaction classification: VALID / SUSPICIOUS / FRAUDULENT
  - 7-feature normalised transaction encoding

- **Validator node** (`node/validator.py`)
  - PoQC mining loop
  - Three-stage transaction validation (format → signature → brain)
  - Wallet keystore persistence
  - Brain state persistence
  - Governance proposal and voting

- **Testnet demo** (`main.py`)
  - 4-node local testnet
  - End-to-end demonstration of all four protocol layers
