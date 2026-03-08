<div align="center">

```
██╗  ██╗███████╗ ██████╗ ██╗   ██╗███████╗███████╗
╚██╗██╔╝██╔════╝██╔═══██╗██║   ██║██╔════╝██╔════╝
 ╚███╔╝ █████╗  ██║   ██║██║   ██║█████╗  ███████╗
 ██╔██╗ ██╔══╝  ██║▄▄ ██║██║   ██║██╔══╝  ╚════██║
██╔╝ ██╗███████╗╚██████╔╝╚██████╔╝███████╗███████║
╚═╝  ╚═╝╚══════╝ ╚══▀▀═╝  ╚═════╝ ╚══════╝╚══════╝
```

### The blockchain that thinks. Built for a world where quantum computers exist.

[**Quickstart**](#quickstart) · [**How it works**](#how-it-works) · [**Discord**](#community) · [**Contributing**](#want-to-help)

[![MIT License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue)](https://python.org)
[![Status](https://img.shields.io/badge/status-testnet-orange)](#quickstart)
[![Crypto](https://img.shields.io/badge/crypto-quantum--safe-blueviolet)](#post-quantum-wallets)
[![Stars](https://img.shields.io/github/stars/YOUR_USERNAME/xeques?style=flat)](https://github.com/YOUR_USERNAME/xeques/stargazers)

</div>

---

## What is XEQUES?

# Open-source quantum-safe blockchain with a brain in every node

**If Bitcoin is a *ledger*, XEQUES is a *living system***

XEQUES is a blockchain I built from scratch — no fork, no copy — because I couldn't find anything that took the quantum threat seriously *and* made the network itself intelligent. Every validator node runs a spiking neural network modelled on real neuron biology. It learns from every transaction. It gets smarter. And nobody owns it.

It runs today. One command.

| | Step | What happens |
|---|---|---|
| **01** | Start a node | Your wallet is quantum-safe from the first keystroke. SHA3-256 + Merkle tree. Survives Grover's algorithm. |
| **02** | Mine a block | Solve a quantum circuit puzzle — simulate the physics, submit the probability distribution. That's proof of work. |
| **03** | The brain decides | Every transaction passes through a spiking neural net before the mempool. It flags fraud. It learns. Nobody runs it. |

> **COMING SOON: XEQ Mainnet** — Real nodes. Real stake. Real governance. Testnet is live now — run a node and get genesis validator status when we launch.

---

## XEQUES is right for you if

* ✅ You think **quantum computers will break Bitcoin and Ethereum** — and you want to be on the chain that's ready
* ✅ You want **block rewards that mean something** — simulating quantum circuits is real computational work
* ✅ You're tired of AI in crypto meaning **a chatbot bolted onto a DEX**
* ✅ You want **governance that can't be bought** — quadratic voting means the crowd beats the whale
* ✅ You want to run a node that **learns over time** without any company behind it
* ✅ You're a developer who wants to build on **infrastructure that will still be standing in 20 years**
* ✅ You want to get in **before mainnet** and be part of the genesis validator set

---

## How it works

### Post-Quantum Wallets

Every other blockchain uses ECDSA. Shor's algorithm on a quantum computer breaks ECDSA completely — not weakens, breaks. Your private key becomes derivable from your public key.

XEQUES uses **Lamport One-Time Signatures** backed by a **Merkle key tree**. The security comes from SHA3-256 collision resistance. Grover's algorithm halves bit security, so 256-bit gives 2¹²⁸ quantum security. That's the ceiling nobody's hitting.

```
sk[i][b] = SHA3(seed ‖ i ‖ b)          →  secret key elements
pk[i][b] = SHA3(sk[i][b])              →  public key (hashes only)
sign(m)  = reveal sk[i][ bit_i(msg) ]  →  reveal the right half per bit
verify   = SHA3(revealed) == pk         →  anyone can check, nobody can fake
```

### Proof of Quantum Control (PoQC)

Bitcoin burns electricity. XEQUES makes the work useful.

Every block, the network derives a seeded quantum circuit from the previous block hash. Validators simulate it and submit the exact probability distribution over all measurement outcomes — the Born rule result. Wrong answer, no block.

```
Puzzle : random quantum circuit C  (5 qubits, depth = difficulty)
Answer : P(x) = |⟨x| U_C |0⟩|²   for every x ∈ {0,1}^5
Valid  : ‖P_submitted − P_true‖₁ < 10⁻⁶   and   ΣP = 1 exactly
```

As real quantum hardware matures, classical simulation hits a wall. Validators with actual quantum processors will mine blocks that classical machines can't compete with. The consensus mechanism rewards building the technology that replaces it.

### The Brain

Every XEQUES node runs a **Leaky Integrate-and-Fire Spiking Neural Network** — the same biological model as real neurons. Not a wrapper around GPT. Not a rule-based classifier. Actual neuronal dynamics with STDP learning.

```
# Membrane voltage integrates input current until it spikes
τ_m · dV/dt = -(V - V_rest) + R_m · I(t)

# Synaptic weights update based on the timing gap between spikes
Δw = A+ · exp(-Δt/τ+)    ← pre fires before post: connection strengthens
   − A- · exp(+Δt/τ-)    ← post fires before pre: connection weakens
```

Every transaction gets screened — VALID, SUSPICIOUS, or FRAUDULENT — before it enters the mempool. After each confirmed block, the brain updates its weights based on what actually happened. No server. No model updates pushed from anywhere. Just every node getting smarter together.

### XEQ Token

| Property | Value | Why |
|---|---|---|
| Total supply | 1,000,000,000 XEQ | Fixed. No inflation tap. |
| Block reward | 50 XEQ, halving every 210,000 blocks | Same proven schedule as Bitcoin |
| Staking APY | Elastic: `BASE_APY × (1 − staked_ratio)` | Self-balancing — rewards shrink as more people stake |
| Governance | Quadratic voting: `votes = √(tokens)` | The crowd beats the whale |

---

## What XEQUES is not

| | |
|---|---|
| **Not a fork.** | Built from scratch. Every line written to understand it. No inherited debt, no inherited vulnerabilities. |
| **Not an AI gimmick.** | The SNN is a real biologically-grounded model running inside every node. Not a chatbot. Not a summariser. An actual learning system. |
| **Not a quantum computer.** | XEQUES simulates quantum circuits classically. The puzzle difficulty is tuned so that as real QCs improve, they gain a mining advantage — incentivising the hardware. |
| **Not VC-backed.** | No investors. No token sale. No dump risk. Fair launch when mainnet is ready. |
| **Not finished.** | Early testnet. One person. The fundamentals work. A lot still needs to be built. |
| **Not for the passive.** | If you run a node, contribute code, or engage with governance, you're shaping what this becomes. That's the point. |

---

## Problems XEQUES solves

| Without XEQUES | With XEQUES |
|---|---|
| ❌ Your Bitcoin wallet is already harvestable — someone's archiving your public keys right now, waiting for Q-Day. | ✅ Lamport + Merkle signatures. Quantum computers cannot derive your private key from your public key. Ever. |
| ❌ Proof of Work burns electricity solving puzzles that produce nothing useful. | ✅ PoQC validators simulate real quantum physics. The work contributes to understanding quantum systems. |
| ❌ On-chain fraud detection means a centralised API call to someone's server. | ✅ The fraud classifier runs inside every node. No company owns it. It improves with every block. |
| ❌ One whale with enough tokens can pass any governance proposal they want. | ✅ Quadratic voting. 1,000,000 tokens = 1,000 votes. 1,000 people with 1,000 tokens each = 31,623 votes. The crowd wins. |
| ❌ Smart contract bugs can drain wallets. Chains can't reason about intent. | ✅ The Brain AGI layer adds a reasoning layer below the contract layer — context-aware, not just rule-based. |
| ❌ Most blockchains will need emergency post-quantum migrations under pressure. | ✅ Quantum-safe from block zero. No migration. No emergency. |

---

## Why XEQUES is different

| | |
|---|---|
| **Born quantum-safe.** | Not retrofitted. Not an upgrade path. The cryptography was the first thing designed, before a single block was written. |
| **Consensus that evolves.** | PoQC difficulty grows with the quantum computing landscape. The puzzle adapts as the hardware does. |
| **Intelligence without a company.** | The SNN brain is deterministic and distributed. No cloud. No API key. No company that can shut it down or change its behaviour. |
| **STDP learning is local.** | Each node's brain updates from its own observed transactions. The network's collective intelligence emerges from individual learning — the way real brains work. |
| **Fair tokenomics.** | Quadratic governance prevents capture. Elastic APY prevents yield-chasing. No pre-mine. No insider allocation. |
| **Open from day one.** | Everything is public. The code, the math, the roadmap. If you find a bug, fix it. If you have a better idea, propose it. |

---

## Quickstart

No Docker. No 50-step setup. Works on any machine with Python.

```bash
git clone https://github.com/YOUR_USERNAME/xeques
cd xeques
pip install numpy
python main.py
```

A 4-node testnet spins up, mines 5 blocks via PoQC, runs every transaction through the SNN brain, executes a governance vote, and prints the live network state. About 5 seconds. You'll see every pillar working.

**What you're running:**
- 4 quantum-safe wallets (Lamport OTS, 64-key Merkle pool each)
- 5-qubit quantum circuit simulator (PoQC consensus)
- LIF spiking neural network (7 input features, 20 hidden neurons, 3 outputs)
- FESH governance with quadratic voting

---

## Project structure

```
xeques/
├── core/
│   ├── crypto.py      # post-quantum wallets: Lamport OTS + Merkle key tree
│   ├── quantum.py     # PoQC engine: quantum circuit simulator + puzzle
│   └── chain.py       # blockchain: blocks, ledger, staking, governance
├── agi/
│   └── brain.py       # LIF spiking neural network + STDP learning
├── node/
│   └── validator.py   # full validator: mine, validate, stake, vote
└── main.py            # start here — testnet demo
```

---

## FAQ

**How is this different from just using a post-quantum library like liboqs?**
XEQUES is a complete blockchain — not a library. The post-quantum cryptography is the wallet layer. PoQC is the consensus. The SNN is the intelligence layer. These three things together don't exist anywhere else.

**Is the quantum circuit simulation real quantum physics?**
Yes. The state vector simulation is exact — we apply real unitary gates (H, CNOT, T, Rz, CZ) and compute Born rule probabilities. It's the same simulation used in quantum computing research. The difference is we're doing it on classical hardware.

**What happens when my 64 signing keys run out?**
Generate a new wallet and transfer your funds. Key rotation will be automated in v0.2.

**Will real quantum computers be able to mine faster?**
Yes, and that's intentional. PoQC is designed so that as quantum hardware matures, validators with real quantum processors gain an increasing advantage. The consensus incentivises building the technology.

**Is the XEQ token live?**
Not yet. We're on testnet. Mainnet is the v1.0 milestone. Early testnet validators will receive a genesis allocation documented in the mainnet config.

**Can I run a node on a cheap VPS?**
Yes. Oracle Cloud Free Tier (genuinely free forever) gives you enough compute to run a validator node 24/7.

---

## Roadmap

- [x] **v0.1** — Core protocol: all 4 systems working end-to-end
- [ ] **v0.2** — P2P networking: real nodes talking to each other
- [ ] **v0.3** — Public testnet: faucet, block explorer, documentation site
- [ ] **v0.4** — Security review and formal specification
- [ ] **v1.0** — Mainnet: fair launch, genesis validator set, XEQ live

---

## Want to help?

One person built this. There's a lot left.

If quantum cryptography, neuromorphic computing, or consensus design interests you — or you just want to work on something genuinely new — open an issue or send a PR. No gatekeeping.

**Most useful right now:**

- [ ] P2P gossip layer so real nodes can talk
- [ ] Block explorer (even a single HTML file is a real contribution)
- [ ] Unit tests for the Lamport signature scheme  
- [ ] Dilithium as an alternative signature scheme
- [ ] JSON-RPC API so external wallets can connect
- [ ] WebSocket feed for real-time block and transaction events

---

## Community

- **Discord** — [discord.gg/xeques](#) — come talk, ask questions, find collaborators
- **GitHub Issues** — bugs, feature requests, and proposals
- **GitHub Discussions** — ideas, RFCs, and longer conversations

---

## Development

```bash
python main.py              # run the testnet demo
python -m pytest tests/     # run tests (coming in v0.2)
```

---

## License

MIT © 2026 XEQUES

---

<div align="center">

*Open source. No company. No VC. Built by one person for a world where quantum computers exist.*

*If you believe the quantum threat is real — run a node.*

</div>
