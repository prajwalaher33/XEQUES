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

[**Quickstart**](#quickstart) · [**How it works**](#how-it-works) · [**Contributing**](#want-to-help)

[![MIT License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue)](https://python.org)
[![Status](https://img.shields.io/badge/status-testnet-orange)](#quickstart)
[![Crypto](https://img.shields.io/badge/crypto-quantum--safe-blueviolet)](#post-quantum-wallets)
[![Stars](https://img.shields.io/github/stars/prajwalaher33/XEQUES?style=flat)](https://github.com/prajwalaher33/XEQUES/stargazers)

</div>

---

## What is XEQUES?

# Open-source quantum-safe blockchain with a brain in every node

**If Bitcoin is a *ledger*, XEQUES is a *living system***

XEQUES is a blockchain built from scratch — no fork, no copy — because I couldn't find anything that took the quantum threat seriously *and* made the network itself intelligent. Every validator node runs a spiking neural network modelled on real neuron biology. It learns from every transaction. It gets smarter. And nobody owns it.

The deeper problem I kept running into: most "quantum-resistant" chains protect your keys but leave the network itself wide open to capture. A nation-state with quantum hardware could dominate block production just by being faster. XEQUES solves this at the physics level — not with rules, not with stake, but by using a consensus puzzle that is equally hard for everyone, including quantum computers.

It runs today. One command.

| | Step | What happens |
|---|---|---|
| **01** | Start a node | Your wallet is quantum-safe from the first keystroke. Every transaction carries a tamper-evident command chain. Replay, reorder, or alter any command — the chain breaks. |
| **02** | Mine a block | Solve a quantum circuit puzzle in the anti-concentration regime. This is provably hard for quantum computers too — not just classical hardware. Nobody can go faster. The math is the floor. |
| **03** | The brain decides | Every transaction passes through a spiking neural net before the mempool. It flags fraud. It learns. Nobody runs it. |

> **COMING SOON: XEQ Mainnet** — Real nodes. Real stake. Real governance. Testnet is live now — run a node and get genesis validator status when we launch.

---

## XEQUES is right for you if

* ✅ You think **quantum computers will break Bitcoin and Ethereum** — and you want to be on the chain that's ready
* ✅ You believe **no country, company, or hardware advantage** should ever control a public network
* ✅ You want **block rewards that mean something** — simulating quantum circuits in the hardness regime is real computational work
* ✅ You're tired of AI in crypto meaning **a chatbot bolted onto a DEX**
* ✅ You want **governance that can't be bought** — quadratic voting means the crowd beats the whale
* ✅ You want to run a node that **learns over time** without any company behind it
* ✅ You're a developer who wants to build on **infrastructure that will still be standing in 20 years**
* ✅ You want to get in **before mainnet** and be part of the genesis validator set

---

## How it works

### Post-Quantum Wallets + Proof of Command Correctness

Every other blockchain uses ECDSA. Shor's algorithm on a quantum computer breaks ECDSA completely — not weakens, breaks. Your private key becomes derivable from your public key.

XEQUES uses **Lamport One-Time Signatures** backed by a **Merkle key tree**. The security comes from SHA3-256 collision resistance. Grover's algorithm halves bit security, so 256-bit gives 2¹²⁸ quantum security — the ceiling nobody's hitting.

But a signature alone only proves *who* sent something. It doesn't prove *when*, it doesn't prove the correct *order*, and it doesn't protect against replay attacks. That's what **Proof of Command Correctness (PoCC)** adds.

Every transaction in XEQUES is a *command* — and every command is linked to every command that came before it through a hash chain:

```
chain_hash[0] = SHA3("GENESIS" + sender_address)
chain_hash[n] = SHA3(chain_hash[n-1] + command_hash[n])
```

This creates a tamper-evident audit trail per sender. Replay a command, reorder two commands, or alter a single field — the chain breaks at that point. Every command carries its own proof that it is the correct next step in that sender's history.

```
sign(cmd)  = Lamport signature over SHA3(amount ‖ receiver ‖ nonce ‖ prev_chain)
verify     = signature valid  AND  prev_chain matches ledger state
```

### Proof of Quantum Control — VDF (#P-Hard Regime)

Bitcoin burns electricity. XEQUES makes the work meaningful.

But the deeper design question is: *who gets to produce blocks?* If the answer is "whoever has the fastest hardware" — you've just built a chain that nation-states with quantum computers will eventually control. That's not decentralisation. It's a different kind of centralisation wearing a decentralised mask.

XEQUES solves this at the physics level, using a result from quantum complexity theory.

Simulating a random quantum circuit in the **anti-concentration regime** is `#P-hard` — provably difficult even for quantum computers. This is the same regime Google's quantum supremacy experiment demonstrated: a quantum computer cannot efficiently simulate another quantum computer's random circuit. The problem is hard for everyone.

We use this property deliberately:

```
Circuit structure per layer:
  1. T-gate on every qubit        ← non-Clifford, breaks all Clifford shortcuts
  2. Random Rz rotations          ← continuous, blocks algebraic attacks
  3. Alternating brick CZ layers  ← maximises entanglement entropy

Acceptance:
  ‖P_submitted − P_true‖₁ < 10⁻⁶   (correct simulation)
  AC score ≤ 3 × (2 / 2^n)          (circuit was in the hard regime — no shortcuts existed)
```

The anti-concentration check is not optional. If the circuit output is too concentrated — meaning shortcuts may exist — the puzzle is rejected. Validators cannot claim easy puzzles.

Because everyone solves in approximately equal time, the first validator with a correct answer wins the block. There is no speed race. A quantum supercomputer and a developer's laptop are equal competitors if both answer correctly.

### The Brain

Every XEQUES node runs a **Leaky Integrate-and-Fire Spiking Neural Network** — the same biological model as real neurons. Not a wrapper around GPT. Not a rule-based classifier. Actual neuronal dynamics with STDP learning.

```
# Membrane voltage integrates input current until it spikes
τ_m · dV/dt = -(V - V_rest) + R_m · I(t)

# Synaptic weights update based on spike timing
Δw = A+ · exp(-Δt/τ+)    ← pre fires before post: strengthens
   − A- · exp(+Δt/τ-)    ← post fires before pre: weakens
```

Every transaction is screened — VALID, SUSPICIOUS, or FRAUDULENT — before it passes PoCC verification. The brain runs first because it's cheap. Cryptographic verification runs after. After each confirmed block, the brain updates from what actually happened. No server. No external model. Just every node getting smarter together.

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
| **Not a hardware race.** | The consensus puzzle is equally hard for classical computers and quantum computers. A nation-state with a 1,000-qubit machine has the same block probability as a solo validator with a laptop. Physics enforces this — not rules, not stake, not a committee. |
| **Not VC-backed.** | No investors. No token sale. No dump risk. Fair launch when mainnet is ready. |
| **Not finished.** | Early testnet. One person. The fundamentals work. A lot still needs to be built. |
| **Not for the passive.** | If you run a node, contribute code, or engage with governance, you're shaping what this becomes. That's the point. |

---

## Problems XEQUES solves

| Without XEQUES | With XEQUES |
|---|---|
| ❌ Your Bitcoin wallet is already harvestable — someone's archiving your public keys right now, waiting for Q-Day. | ✅ Lamport + Merkle signatures. Quantum computers cannot derive your private key from your public key. Ever. |
| ❌ Standard signatures prove *who* sent something, not *when* or in *what order*. Replay and reorder attacks work silently. | ✅ PoCC command chains. Every transaction is cryptographically linked to the one before it. Break the order, break the chain. |
| ❌ Whoever builds the fastest quantum hardware controls block production. The US and China are spending billions on this right now. | ✅ PoQC-VDF uses the #P-hard anti-concentration regime. Equal solve time for everyone. Hardware wealth buys nothing. |
| ❌ On-chain fraud detection means a centralised API call to someone's server. | ✅ The fraud classifier runs inside every node. No company owns it. It improves with every block. |
| ❌ One whale with enough tokens can pass any governance proposal they want. | ✅ Quadratic voting. 1,000,000 tokens = 1,000 votes. 1,000 people with 1,000 tokens each = 31,623 votes. The crowd wins. |
| ❌ Most blockchains will need emergency post-quantum migrations under pressure. | ✅ Quantum-safe from block zero. No migration. No emergency. |

---

## Why XEQUES is different

| | |
|---|---|
| **Born quantum-safe.** | Not retrofitted. Not an upgrade path. The cryptography was the first thing designed, before a single block was written. |
| **Consensus that physics protects.** | Block production fairness is enforced by a hardness result in computational complexity — not by rules, not by stake, not by anything that can be gamed. |
| **Two layers of transaction proof.** | Lamport signatures prove identity. PoCC command chains prove ordering and integrity. Together they're stronger than any signature scheme alone. |
| **Intelligence without a company.** | The SNN brain is deterministic and distributed. No cloud. No API key. No company that can shut it down or change its behaviour. |
| **STDP learning is local.** | Each node's brain updates from its own observed transactions. The network's collective intelligence emerges from individual learning — the way real brains work. |
| **Fair tokenomics.** | Quadratic governance prevents capture. Elastic APY prevents yield-chasing. No pre-mine. No insider allocation. |
| **Open from day one.** | Everything is public. The code, the math, the roadmap. If you find a bug, fix it. If you have a better idea, propose it. |

---

## Quickstart

No Docker. No 50-step setup. Works on any machine with Python.

```bash
git clone https://github.com/prajwalaher33/XEQUES
cd XEQUES
pip install numpy
python main.py
```

A 4-node testnet spins up, creates PoCC-verified commands, mines 5 blocks via PoQC-VDF, runs every transaction through the SNN brain, executes a governance vote, and prints the live network state. About 5 seconds. You'll see every pillar working.

**What you're running:**
- 4 quantum-safe wallets (Lamport OTS, 64-key Merkle pool each)
- PoCC command chains (tamper-evident transaction ordering per sender)
- 5-qubit quantum circuit VDF (anti-concentration, #P-hard regime)
- LIF spiking neural network (7 input features, 20 hidden neurons, 3 outputs)
- XEQ governance with quadratic voting

---

## Project structure

```
xeques/
├── core/
│   ├── crypto.py      # post-quantum wallets: Lamport OTS + Merkle key tree
│   ├── pocc.py        # Proof of Command Correctness: command chains + verifier
│   ├── quantum.py     # PoQC-VDF: anti-concentration circuit + hardness check
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
XEQUES is a complete blockchain — not a library. The post-quantum cryptography is the wallet layer. PoCC is the command authorisation layer. PoQC-VDF is the consensus. The SNN is the intelligence layer. These four things together don't exist anywhere else.

**What is Proof of Command Correctness?**
Every transaction in XEQUES is a command. PoCC proves three things: it was authorised by the right wallet (Lamport signature), it arrived in the correct order (nonce), and it hasn't been replayed or tampered with (command chain hash). The chain hash links every command to every previous command from that sender — alter anything and the chain breaks before the transaction touches the ledger.

**Is the quantum circuit simulation real quantum physics?**
Yes. The state vector simulation is exact — we apply real unitary gates (H, CNOT, T, Rz, CZ) and compute Born rule probabilities. The VDF structure (T-gates + alternating brick CZ) follows the Sycamore architecture that Google used to demonstrate quantum supremacy.

**Won't quantum computers just solve the puzzle faster and dominate block production?**
No — and this is the most important design decision in the protocol. The puzzle is generated in the anti-concentration regime, which is `#P-hard`. This class of problems is believed to be hard even for quantum computers. A quantum computer cannot efficiently simulate another quantum computer's random circuit — that is the entire basis of quantum supremacy demonstrations. Everyone solves in approximately equal time. Hardware wealth buys nothing.

**What happens when my 64 signing keys run out?**
Generate a new wallet and transfer your funds. Key rotation will be automated in v0.3.

**Is the XEQ token live?**
Not yet. Testnet only. Mainnet is the v1.0 milestone. Early testnet validators will receive a genesis allocation documented in the mainnet config.

**Can I run a node on a cheap VPS?**
Yes. Oracle Cloud Free Tier (genuinely free forever) is enough to run a validator node 24/7.

---

## Roadmap

- [x] **v0.1** — Core protocol: post-quantum wallets, PoQC consensus, Brain AGI, XEQ tokenomics
- [x] **v0.2** — PoCC command chains + PoQC-VDF anti-concentration upgrade
- [ ] **v0.3** — P2P networking: real nodes talking to each other over the wire
- [ ] **v0.4** — Public testnet: faucet, block explorer, documentation site
- [ ] **v0.5** — Security review and formal specification
- [ ] **v1.0** — Mainnet: fair launch, genesis validator set, XEQ live

---

## Want to help?

One person built this. There's a lot left.

If quantum cryptography, neuromorphic computing, or consensus design interests you — or you just want to work on something genuinely new — open an issue or send a PR. No gatekeeping.

**Most useful right now:**

- [ ] P2P gossip layer so real nodes can talk to each other
- [ ] Block explorer (even a single HTML file is a real contribution)
- [ ] Unit tests for the Lamport signature scheme
- [ ] Unit tests for PoCC chain verification
- [ ] Dilithium as an alternative post-quantum signature scheme
- [ ] JSON-RPC API so external wallets can connect
- [ ] WebSocket feed for real-time block and transaction events
- [ ] Auto key rotation when the Merkle pool runs low

---

## Community

- **GitHub Issues** — bugs, feature requests, and proposals
- **GitHub Discussions** — ideas, RFCs, and longer conversations

---

## License

MIT © 2026 XEQUES

---

<div align="center">

*Open source. No company. No VC. Built by one person for a world where quantum computers exist.*

*The quantum threat is real. The network should be ready before it matters.*

*If you believe that — run a node.*

</div>
