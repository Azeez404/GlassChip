# Phase 2B — Within-Summit Observability Ablation

Controlled test: on the **same** Summit hosts/sockets/period, degrade only
telemetry **fidelity** and measure the effect on (i) thermal-parameter
identifiability and (ii) out-of-sample residual learnability. Removes the
M100-vs-Summit hardware/workload confound.

Frozen V1 model (read-only): `T[n+1]=αT[n]+βP[n]+γ` (OLS), `τ=−dt/ln α`.
Raw data unchanged (SHA-256 `9898170b…996e`); V1 unmodified; Phase 2A untouched.

## Conditions (10 coverage-ranked hosts × 2 sockets = 20 units)
| id | temperature | quant | sampling | note |
|----|-------------|-------|----------|------|
| F0 | socket-mean | float | 10 s | full fidelity (= Phase 2A) |
| F1 | socket-mean | 1 °C | 10 s | quantization only |
| F2 | socket-mean | float | 20 s (decimate ×2) | temporal only |
| F3 | **Tjmax** (`p*_core_temp_max`) | float | 10 s | spatial only |
| F4 | Tjmax | 1 °C | 20 s | combined low-fidelity |

**F3/F4 caveat:** the cleaned "decomp" archive has **no fixed per-physical-core
streams** — only `core_temp_{mean,min,max}`. F3 therefore uses **Tjmax = the
per-timestamp hottest-core reading** (a real single-sensor telemetry mode) as
the closest *precisely-defined* single-sensor proxy. It is an approximation of
"single-core," documented, not a fabricated fixed-core index.

## Protocol
- Identifiability: analytic OLS delta-method τ, CoV, 95% CI per unit.
- Residual: pooled across sockets, strict chronological split (last collection
  block = test), models = persistence / linear / HistGradientBoosting
  (sklearn; xgboost unavailable) / tiny LSTM / physics-anchored MLP.
- Permutation-null (200×) on the linear model; fair seeded caps
  (150k train / 50k test) identical across conditions.

## Headline result (see JSON/CSV/figures)
- **Fidelity biases the identified τ, it does not merely widen its CI:**
  τ_median = 394 s (F0) → **116 s** (quantized) → **910 s** (downsampled) →
  283 s (Tjmax) → 352 s (combined). Analytic CoV even *shrinks* under
  quantization (0.026→0.009) — i.e. the analytic uncertainty is **not** a
  faithful identifiability indicator under degradation.
- **Residual stays not-materially-learnable at every fidelity:** OOS R² ≤ ~0.07
  (best = HGB), hovering near the permutation-null; higher fidelity does **not**
  increase it (full-fidelity F0 is among the lowest).

Files: `observability_ablation.py`, `observability_ablation_results.json`,
`observability_ablation_table.csv`, `fig1/2/3_*.png`.
