# Methodology

Condensed reference for the experimental design. The manuscript
(`paper/manuscript/manuscript.md`) is authoritative; this file orients a reader to the code.

## Question

How does measurement quality — temperature quantization, sampling rate, spatial aggregation —
affect identification of a first-order thermal model from a supercomputer's own measurements,
and does higher measurement quality also make the unexplained residual more predictable?

## Design

Hardware and workload are held fixed; only the *measurements* are degraded, so any difference in
the identified parameter is attributable to measurement quality rather than to differing
machines or workloads.

| Condition | Temperature | Sampling | Spatial |
|---|---|---|---|
| **F0** | socket-mean, float | 10 s | socket-mean | *reference regime* |
| **F1** | socket-mean, 1 °C | 10 s | socket-mean | quantization |
| **F2** | socket-mean, float | 20 s | socket-mean | downsampling (decimate ×2) |
| **F3** | Tjmax, float | 10 s | hottest-core proxy | spatial aggregation |
| **F4** | Tjmax, 1 °C | 20 s | hottest-core proxy | combined |

F3/F4 use a per-timestamp hottest-core value as a single-sensor proxy; the archive provides no
fixed per-physical-core streams.

## Model

A frozen first-order ARX relating the next temperature sample to the current temperature and
power:

```
T[n+1] = alpha * T[n] + beta * P[n] + gamma
tau    = -dt / ln(alpha)
```

τ is an **identification parameter**, never a physical R·C constant. Fitted by OLS over
consecutive within-segment pairs; a fit is retained only when 0 < α < 1. Pairs are never formed
across a collection gap.

**F0 is a reference measurement regime, not physical ground truth.** An ideal first-order process
leaves τ invariant under decimation, so the F2 shift (394 → 910 s) indicates dynamics faster than
the model represents. All comparisons are relative to F0 under a fixed identification convention.

## Phases

| Phase | Script | What it produces |
|---|---|---|
| 2A | `experiments/phase2a_counterfactual.py` | frozen baseline; per-unit α, β, γ |
| 2B | `experiments/phase2b_ablation.py` | F0-F4 ablation, 20 units — **canonical** |
| 2C | `experiments/phase2c_bootstrap.py` | moving-block bootstrap (B=500, block ≈ 640 s) |
| 2D | `experiments/phase2d_fleet.py` | all 116 sampled host-sockets at F0 |
| 2E | `experiments/phase2e_streaming.py` | causal online rolling-τ boundary |
| 2F | `experiments/phase2f_ablation_116.py` | F0-F4 across all 116 units, paired per unit |

## Units and sampling

The unit of analysis is one CPU socket of one host: 58 hosts × 2 sockets = **116 sampled
host-sockets**. This is a *sample*, not the machine — Summit has 4,626 nodes. The ablation and
bootstrap use a deterministic 20-unit subset; the population analyses and Phase 2F use all 116.

Never write "the fleet" for these 116 units.

## Statistical conventions

- Chronological train/test splits only; observations are never shuffled.
- Uncertainty: analytic delta-method **and** moving-block bootstrap, reported separately. The
  bootstrap quantifies uncertainty; it does not correct measurement-induced bias.
- Residual prediction is strictly out-of-sample with a permutation null.
- **Population spread must be checked in both τ and α.** τ = −Δt/ln α is strongly nonlinear, so
  τ-space dispersion can move for purely algebraic reasons: F1's apparent narrowing in τ (IQR
  ratio 0.370) *reverses* in α (3.315). Only F3 narrows in both. Rank statistics (Spearman) are
  invariant to monotone reparameterisation and so are immune to this.

## Claims that must not be made

Physical R·C; "unlearnable"; failure/degradation/RUL prediction; a validated monitor; PINN as a
contribution; causal socket/host explanation; a universal or digital-twin framework;
measurement-induced homogenisation; any causal claim outside the within-Summit ablation.
