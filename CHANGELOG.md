# Changelog

All notable changes to XEQUES are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

---

## [0.2.0] — 2026-03-09

### Added
- **Proof of Command Correctness (PoCC)** — `core/pocc.py`
  - Every transaction is now a `Command` carrying a cryptographic hash chain
  - `chain_hash[n] = SHA3(chain_hash[n-1] + command_hash[n])` per sender
  - Proves authorisation (Lamport sig), ordering (nonce), and integrity (chain) simultaneously
  - Replay attacks, reorder attacks, and field tampering all break the chain and are rejected at mempool admission
  - `PoCCRegistry` tracks chain state per address in the ledger
  - `PoCCVerifier` runs stateless verification — used by validators before PoQC check

- **PoQC-VDF anti-concentration upgrade** — `core/quantum.py`
  - Replaced naive random circuits with `random_vdf()` using the Sycamore-pattern structure
  - Per-layer: T-gate on all qubits + random Rz rotations + alternating brick CZ entanglement
  - This places the circuit in the `#P-hard` anti-concentration regime — hard for quantum computers too, not just classical
  - Added `anti_concentration_score()` — measures the second moment of the output distribution against the Porter-Thomas target
  - Added `is_in_hard_regime()` — rejects puzzles where the output is too concentrated (shortcuts may exist)
  - `verify()` now checks both L1 correctness AND the hardness regime before accepting an answer

- **Four-stage validation pipeline** in `validator.py`
  - Brain AGI pre-screening runs first (cheap — catches obvious fraud before crypto)
  - PoCC proof verification (command chain + Lamport signature)
  - Format check
  - Balance check (ledger)
  - Added `validate_command()` for PoCC-wrapped commands alongside existing `validate_transaction()`

### Changed
- PoQC consensus now uses VDF "first correct answer wins" — stake-weighted selection removed
  - Because everyone solves in approximately equal time (all in the hard regime), first correct answer is effectively random and fair
  - Removes the centralisation risk that stake-weighted selection introduced
- README completely rewritten to reflect the combined PoCC + PoQC-VDF architecture
- `mine_one_block()` now accepts `all_nodes` list — all nodes solve simultaneously, first correct answer wins
- Demo in `main.py` now shows PoCC command verification, replay attack rejection, and Lamport tamper detection as separate labelled tests

### Fixed
- README FAQ incorrectly stated quantum computers would mine faster — corrected to explain #P-hard VDF design
- README incorrectly referenced "FESH governance" — corrected to XEQ
- GitHub username placeholder updated throughout

---

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
