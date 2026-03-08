# Contributing to XEQUES

Thanks for your interest. XEQUES is an early-stage open-source project and contributions of all kinds are welcome — code, documentation, testing, research, or just opening a well-described issue.

---

## Before you start

Please open an issue before starting significant work. This avoids duplicated effort and makes sure what you're building fits the direction of the project. For small fixes (typos, docs, minor bugs), just send the PR directly.

---

## What we need most right now

- **P2P networking** — libp2p or raw TCP gossip so real nodes can talk to each other
- **JSON-RPC API** — so external wallets and tools can connect to a node
- **Block explorer** — even a single self-contained HTML file is a meaningful contribution
- **Unit tests** — especially for `core/crypto.py` (Lamport signatures, Merkle proofs)
- **Dilithium signatures** — as an alternative to Lamport OTS in `core/crypto.py`
- **Benchmarks** — PoQC simulation speed at varying qubit counts and depths

---

## How to contribute

1. Fork the repository
2. Create a branch: `git checkout -b your-feature-name`
3. Make your changes
4. Run the demo to make sure nothing is broken: `python main.py`
5. Open a pull request with a clear description of what you changed and why

---

## Code style

- Python 3.10+
- No external dependencies beyond `numpy` for the core protocol
- Keep comments honest and specific — explain *why*, not just *what*
- If you're adding a new cryptographic primitive, include a comment with the security proof sketch

---

## Reporting bugs

Open a GitHub Issue. Include:
- What you were doing
- What you expected
- What actually happened
- Python version and OS

---

## Security vulnerabilities

**Do not open a public issue for security vulnerabilities.** See [SECURITY.md](SECURITY.md) for the responsible disclosure process.

---

## Questions

Open a Discussion or join the Discord. No question is too basic.
