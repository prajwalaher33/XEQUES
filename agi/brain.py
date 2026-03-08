"""
xeques/agi/brain.py
───────────────────
Brain AGI Layer — Spiking Neural Network + STDP

Architecture:  INPUT(7) → HIDDEN(20) → OUTPUT(3)
Neuron model:  Leaky Integrate-and-Fire (LIF)
Learning rule: Spike-Timing-Dependent Plasticity (STDP)
Output labels: [VALID=0, SUSPICIOUS=1, FRAUDULENT=2]

Mathematics:
─────────────
LIF membrane dynamics (discrete Euler):
    V[t+dt] = V[t] + (dt/τ_m) × (-(V[t] - V_rest) + R_m × I[t])
    Spike:    V[t] ≥ V_th  →  V ← V_reset, ref_timer ← T_ref

STDP weight update (supervised variant):
    Δt = t_post - t_pre
    If Δt > 0 (pre before post, LTP):  Δw = +A+ × exp(-Δt / τ+)
    If Δt < 0 (post before pre, LTD):  Δw = -A- × exp(+Δt / τ-)
    Correct output neuron: reinforce (+)
    Wrong output neurons:  suppress  (-)

Features extracted per transaction:
    0: amount_ratio       (amount / sender_balance)
    1: amount_abs         (amount / 100_000, clipped)
    2: receiver_known     (1 if receiver seen before, 0 otherwise)
    3: sender_tx_rate     (tx/block rate, normalised)
    4: amount_vs_avg      (amount / network_avg_amount)
    5: time_since_last_tx (seconds / 3600, clipped to [0,1])
    6: nonce_jump         (nonce / expected_nonce, clipped)
"""

import numpy as np
import json
from dataclasses import dataclass, field
from typing import Tuple, List, Optional


# ── Hyperparameters ────────────────────────────────────────────────────────

@dataclass
class LIFConfig:
    tau_m  : float = 20.0    # membrane time constant (ms)
    R_m    : float = 80.0    # membrane resistance (MΩ)
    V_rest : float = -65.0   # resting potential (mV)
    V_th   : float = -50.0   # spike threshold (mV)
    V_reset: float = -75.0   # post-spike reset (mV)
    T_ref  : float = 2.0     # refractory period (ms)
    dt     : float = 0.5     # simulation timestep (ms)

@dataclass
class STDPConfig:
    A_plus   : float = 0.015   # LTP amplitude
    A_minus  : float = 0.018   # LTD amplitude
    tau_plus : float = 20.0    # LTP time constant (ms)
    tau_minus: float = 20.0    # LTD time constant (ms)
    w_min    : float = 0.0     # minimum weight (excitatory only)
    w_max    : float = 2.0     # maximum weight


LABELS = ['VALID', 'SUSPICIOUS', 'FRAUDULENT']
N_IN   = 7
N_HID  = 20
N_OUT  = 3
T_SIM  = 100   # simulation duration (steps)


# ── LIF Layer ──────────────────────────────────────────────────────────────

def lif_step(V: np.ndarray, ref: np.ndarray, I: np.ndarray,
             cfg: LIFConfig) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    One LIF timestep.
    Returns: (V_new, spikes, ref_new, spike_mask)
    """
    active  = ref <= 0
    dV      = (cfg.dt / cfg.tau_m) * (-(V - cfg.V_rest) + cfg.R_m * I)
    V_new   = np.where(active, V + dV, cfg.V_reset)
    spikes  = (V_new >= cfg.V_th) & active
    V_new   = np.where(spikes, cfg.V_reset, V_new)
    ref_new = np.where(spikes, cfg.T_ref, np.maximum(0.0, ref - cfg.dt))
    return V_new, spikes, ref_new, spikes.astype(float)


# ── Brain ──────────────────────────────────────────────────────────────────

class XequesBrain:
    """
    Distributed SNN that evaluates transactions.
    Each validator node runs its own brain; consensus on classification
    is reached when >2/3 of nodes agree on the label.

    The brain improves over time through STDP — no centralised training,
    no labelled dataset required. It learns from the network's collective
    confirmation/rejection of transactions.
    """

    def __init__(self, seed: int = 42, lif: LIFConfig = None, stdp: STDPConfig = None):
        self.lif  = lif  or LIFConfig()
        self.stdp = stdp or STDPConfig()
        rng = np.random.RandomState(seed)
        # Excitatory synaptic weights
        self.W1 = rng.uniform(0.10, 0.50, (N_HID, N_IN))
        self.W2 = rng.uniform(0.25, 0.90, (N_OUT, N_HID))
        # Spike history for STDP
        self._last_hid = np.full(N_HID, -np.inf)
        self._last_out = np.full(N_OUT, -np.inf)
        # Stats
        self.total_txs  = 0
        self.stdp_steps = 0
        self.label_counts = [0, 0, 0]

    # ── Feature extraction ─────────────────────────────────────────────────

    @staticmethod
    def extract_features(tx_data: dict, network_state: dict) -> np.ndarray:
        """
        Convert raw transaction data into 7 normalised features ∈ [0, 1].

        tx_data keys:   sender, receiver, amount, nonce, timestamp
        network_state:  balances, known_addrs, avg_amount, tx_rates, nonces
        """
        amount      = float(tx_data.get('amount', 0))
        sender      = tx_data.get('sender', '')
        receiver    = tx_data.get('receiver', '')
        nonce       = int(tx_data.get('nonce', 0))
        ts          = float(tx_data.get('timestamp', 0))

        balances    = network_state.get('balances', {})
        known_addrs = network_state.get('known_addrs', set())
        avg_amount  = float(network_state.get('avg_amount', 100.0)) or 100.0
        tx_rates    = network_state.get('tx_rates', {})
        expected_n  = network_state.get('nonces', {}).get(sender, 0)
        last_ts     = network_state.get('last_ts', {}).get(sender, ts)

        sender_bal  = balances.get(sender, 0.0) or 1e-9

        f = np.array([
            min(amount / sender_bal, 1.0),                      # 0: amount / balance
            min(amount / 100_000.0, 1.0),                       # 1: absolute amount
            1.0 if receiver in known_addrs else 0.0,            # 2: receiver known
            min(tx_rates.get(sender, 0) / 10.0, 1.0),          # 3: tx rate
            min(amount / avg_amount / 5.0, 1.0),                # 4: vs network avg
            min(abs(ts - last_ts) / 3600.0, 1.0),              # 5: time since last tx
            min(abs(nonce - expected_n) / 5.0, 1.0),           # 6: nonce anomaly
        ], dtype=float)

        return np.clip(f, 0.0, 1.0)

    # ── Forward pass ───────────────────────────────────────────────────────

    def process(self, features: np.ndarray) -> Tuple[int, float, np.ndarray, np.ndarray]:
        """
        Run SNN simulation.
        Returns: (label_idx, confidence, hid_spike_counts, out_spike_counts)
        """
        cfg  = self.lif
        # Encode features as tonic input current
        # I_th = (V_th - V_rest) / R_m = 15/80 ≈ 0.19 nA
        # Drive range: [0.25, 2.25] nA → all neurons above threshold
        I_in = 0.25 + features * 2.0

        V1, ref1 = np.full(N_HID, cfg.V_rest), np.zeros(N_HID)
        V2, ref2 = np.full(N_OUT, cfg.V_rest), np.zeros(N_OUT)
        spk1_sum = np.zeros(N_HID)
        spk2_sum = np.zeros(N_OUT)
        last_hid = np.full(N_HID, -np.inf)
        last_out = np.full(N_OUT, -np.inf)

        for step in range(T_SIM):
            t = step * cfg.dt
            # Hidden layer: driven by input current through W1
            I1 = self.W1 @ I_in
            V1, spk1, ref1, s1 = lif_step(V1, ref1, I1, cfg)
            spk1_sum += spk1
            last_hid = np.where(spk1, t, last_hid)

            # Output layer: driven by hidden spikes through W2
            I2 = self.W2 @ s1
            V2, spk2, ref2, s2 = lif_step(V2, ref2, I2, cfg)
            spk2_sum += spk2
            last_out = np.where(spk2, t, last_out)

        # Update spike history for STDP
        self._last_hid = last_hid
        self._last_out = last_out

        # Winner-takes-all decode
        label = int(np.argmax(spk2_sum))
        total = spk2_sum.sum() + 1e-9
        conf  = float(spk2_sum[label] / total)

        self.total_txs += 1
        self.label_counts[label] += 1

        return label, conf, spk1_sum, spk2_sum

    # ── STDP learning ──────────────────────────────────────────────────────

    def learn(self, correct_label: int):
        """
        Reinforce correct output neuron; suppress incorrect ones.
        Called after a transaction outcome is confirmed on-chain.
        """
        s = self.stdp
        hid = self._last_hid
        out = self._last_out

        for j in range(N_OUT):
            if not np.isfinite(out[j]):
                continue
            sign = 1.0 if j == correct_label else -1.0
            for i in range(N_HID):
                if not np.isfinite(hid[i]):
                    continue
                dt = out[j] - hid[i]
                if dt > 0:
                    dw = s.A_plus  * np.exp(-dt / s.tau_plus)
                else:
                    dw = -s.A_minus * np.exp(dt  / s.tau_minus)
                self.W2[j, i] = np.clip(self.W2[j, i] + sign * dw, s.w_min, s.w_max)

        self.stdp_steps += 1

    # ── Serialisation ──────────────────────────────────────────────────────

    def state_dict(self) -> dict:
        return {
            'W1'          : self.W1.tolist(),
            'W2'          : self.W2.tolist(),
            'total_txs'   : self.total_txs,
            'stdp_steps'  : self.stdp_steps,
            'label_counts': self.label_counts,
        }

    def load_state(self, d: dict):
        self.W1          = np.array(d['W1'])
        self.W2          = np.array(d['W2'])
        self.total_txs   = d.get('total_txs', 0)
        self.stdp_steps  = d.get('stdp_steps', 0)
        self.label_counts= d.get('label_counts', [0, 0, 0])

    def stats(self) -> dict:
        total = sum(self.label_counts) or 1
        return {
            'total_txs'     : self.total_txs,
            'stdp_updates'  : self.stdp_steps,
            'W2_frobenius'  : float(np.linalg.norm(self.W2)),
            'label_dist'    : {
                LABELS[i]: f"{100*self.label_counts[i]/total:.1f}%"
                for i in range(3)
            }
        }
