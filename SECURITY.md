# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.1.x (testnet) | ✅ Active development |

XEQUES is currently in testnet. The cryptographic primitives are production-grade, but the networking and node software should be treated as pre-release until v1.0.

---

## Reporting a vulnerability

**Please do not report security vulnerabilities through public GitHub Issues.**

If you find a vulnerability — especially anything affecting the cryptographic layer (`core/crypto.py`), the PoQC puzzle verification (`core/quantum.py`), or consensus integrity (`core/chain.py`) — please disclose it responsibly.

**How to report:**

1. Email a description of the vulnerability to the maintainer (address in the GitHub profile)
2. Include steps to reproduce, the potential impact, and any suggested fix if you have one
3. You'll receive an acknowledgement within 48 hours

We take cryptographic vulnerabilities extremely seriously. If the issue is valid we will:
- Acknowledge your report privately
- Work on a fix before public disclosure
- Credit you in the fix commit and changelog (unless you prefer to stay anonymous)

---

## Cryptographic assumptions

The security of XEQUES wallets rests on:

- **Collision resistance of SHA3-256** (NIST standard, Keccak family)
- **One-wayness of SHA3-256** (Lamport signature security)
- **No Lamport key reuse** (enforced in code — signing twice with the same key is blocked)

The security of PoQC consensus rests on:

- **Deterministic seeding** of puzzle circuits from `SHA3(prev_hash ‖ height ‖ difficulty)` — validators cannot predict the circuit in advance
- **Exact probability verification** — submitted distributions are checked against exact simulation results

If you believe any of these assumptions are weaker than stated, please report it.
