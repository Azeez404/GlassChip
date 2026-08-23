# PROTOTYPE BLUEPRINT

Clean-room PINN prototype. Written before implementation, after data inspection.
Independent of GLASSCHIP: no GLASSCHIP code imported, no prior PINN reused, raw data read
read-only through a configurable path.

## 1. Research question

Can physics-informed learning improve GPU temperature prediction in the high-temperature
regime, where real production telemetry is data-scarce?

## 2. Hypothesis

In the abundant cool regime a black-box gradient-boosted model wins and physics adds nothing.
In the sparse hot regime (>55 °C) the black-box model degrades because it has no training
support there, while a model whose loss embeds a thermal energy balance degrades gracefully,
because the physics term constrains behaviour where data is absent.

**This is a test, not a claim.** A negative result is a valid and publishable outcome.

## 3. Dataset and verified signals

Summit per-component power and thermal measurements (OSTI/OLCF DOI 10.13139/OLCF/1861393,
CC-BY-4.0). Read **read-only** from the existing local derived tables via a configurable path;
nothing is copied into this branch.

Verified by direct inspection (not assumed from documentation):

| Property | Verified value |
|---|---|
| Hosts available locally | 58 (`host=*/data.parquet`, 33 columns, ~1.19 M rows each) |
| Timestamp | `datetime64[ns, UTC]`, monotonic increasing, **0 duplicates** |
| Sampling interval | `dt_s` = 10.0 s for 1,191,331 of 1,191,562 rows on the reference host; occasional 20/30/40/50 s |
| Segmentation | `segment_id` (89 segments on host 0) marks collection-gap boundaries |
| GPU power | `p0_gpu{0,1,2}_power`, `p1_gpu{0,1,2}_power`, float64, 17–400 W |
| GPU core temp | `gpu{0..5}_core_temp`, float64 |
| GPU memory temp | `gpu{0..5}_mem_temp`, float64 (available; **not used** in this prototype) |
| Nulls | small (34 of 1.19 M for power/core temp on host 0) |

**Verified channel mapping** (by correlation, clean diagonal argmax):
`gpu0,1,2_core_temp` ↔ `p0_gpu0,1,2_power`; `gpu3,4,5_core_temp` ↔ `p1_gpu0,1,2_power`.

**Verified regime scarcity** — the reason this experiment exists. Across all 348 traces
(58 hosts × 6 GPUs): median hot-regime (>55 °C) count per trace is **52 samples**; only 92 of
348 traces have ≥2,000. The hot regime is genuinely rare in production.

## 4. Data flow

```
Summit derived parquet (read-only, external path)
   → select one (host, gpu) trace; join core temp with its own GPU power
   → drop nulls; keep only rows on a regular 10 s step within a segment
   → build causal lag features
   → regime split (train <45 °C, test >55 °C, 45–55 °C excluded)
   → fit scaler on TRAIN ONLY
   → 4 models → one-step + multi-step prediction on hot regime
   → metrics.csv + hot_regime_predictions.png → verdict
```

## 5. Selected GPU trace strategy

Deterministic: scan all 348 traces, select the one with the **greatest number of hot-regime
(>55 °C) observations**, subject to ≥100,000 cold-regime observations; ties broken by
(host, gpu) ascending. Selection depends only on regime coverage, never on model performance.

**Result of the scan: `a11n12`, GPU 5** — 1,191,322 valid rows, 929,038 cold (<45 °C),
184,293 transition, **77,991 hot (>55 °C)**, T max 74.8 °C, P max 369 W.

## 6. Train/test regime definition

- **TRAIN**: target `T[n+1] < 45 °C` **and** every lagged temperature in the feature vector `< 45 °C`.
- **TEST**: target `T[n+1] > 55 °C` **and** every lagged temperature in the feature vector `> 55 °C`.
- **EXCLUDED**: everything touching 45–55 °C. No sample can appear in both sets; the 10 °C gap
  guarantees genuine extrapolation rather than interpolation.

## 7. Prediction target — a deliberate anti-straw-man choice

All models predict the **temperature increment** `ΔT[n] = T[n+1] − T[n]`, and the temperature is
reconstructed as `T̂[n+1] = T[n] + ΔT̂[n]`.

Predicting absolute `T[n+1]` would let a tree model fail trivially: trained only below 45 °C, it
can never output 60 °C, so it would lose by construction. Predicting the increment removes that
artifact and makes the comparison about **dynamics**, which is what the physics claim actually
concerns. This deliberately makes the ML baselines as strong as possible.

## 8. Classical model (Model A)

First-order lumped thermal model for a single GPU:

    C · dT/dt = P − (T − T_amb) / R

**In plain English:** the GPU turns electrical power into heat, which raises its temperature.
At the same time it loses heat to its coolant, faster the hotter it is relative to that coolant.
Temperature changes according to the balance of the two.

Discrete form actually fitted (Δt = 10 s):

    ΔT[n] = Δt · ( a · P[n] − b · (T[n] − T_amb) ),   a = 1/C > 0,  b = 1/(RC) > 0

Three parameters (a, b, T_amb) fitted by ordinary least squares **on the training regime only**,
then checked for physical admissibility: a > 0, b > 0, and T_amb near Summit's known
medium-temperature coolant (low-20s °C). Admissibility is reported, not enforced by clipping.

## 9. ML baseline (Model B)

`sklearn.ensemble.HistGradientBoostingRegressor`. **XGBoost and LightGBM are not installed in
this environment**; the scikit-learn histogram-based gradient-boosted tree is the direct
equivalent (same algorithm family, supports `sample_weight`). This substitution is documented
here and in the README rather than silently made.

## 10. Tail-weighted ML control (Model C)

Identical model and features, with training `sample_weight` increasing exponentially in
temperature across the **training** distribution:

    w[n] = exp( (T[n] − T_train_median) / s ),  s = training temperature std, clipped to [1, 50]

Weights are computed from training temperatures only; **no test label or test statistic is used.**
This is the decisive control: if the PINN's advantage is really just the tree under-weighting
rare warm samples, Model C removes it.

## 11. PINN architecture (Model D)

Small MLP: `input → 64 → 64 → 1`, tanh activations, predicting `ΔT`. Jointly learned physical
parameters `a`, `b` (via softplus, so strictly positive) and `T_amb` (free).

Two variants, both trained identically apart from where the physics residual is evaluated:

- **PINN-strict** — physics residual evaluated only at training points. Uses no information of
  any kind from outside the training regime.
- **PINN-collocation** (primary) — physics residual additionally evaluated at **synthetic**
  collocation points on a (T, P) grid spanning T ∈ [20, 80] °C and P ∈ [17, 400] W. These points
  are generated numerically; **no measured hot-regime data is used**, and no label is required
  because the physics residual is unsupervised. This is the canonical mechanism by which a PINN
  can constrain behaviour in a regime where it has no data, and it is leakage-free by construction.

## 12. Loss function

    L = L_data + λ · L_physics

    L_data    = mean over training samples of ( ΔT̂ − ΔT_obs )²
    L_physics = mean over collocation points of ( ΔT̂/Δt − ( a·P − b·(T − T_amb) ) )²

λ = 1.0 for the primary run, with a small sensitivity sweep reported. Adam, fixed seed, fixed
epoch budget. Inputs standardised with a scaler fitted on the **training regime only**.

## 13. Evaluation metrics

Primary table: **RMSE, MAE, Max absolute error** on reconstructed temperature over the hot test
set, for each of the four models.

Reported separately and never mixed:
- **One-step**: predict `T[n+1]` from observed causal features at `n`.
- **Multi-step (free-running, H = 30 steps = 300 s)**: seed with the observed temperature at the
  start of a contiguous hot block, then roll forward using each model's own predictions and the
  observed future power. This is the harder, more informative test.

## 14. Leakage-prevention rules

1. Features are strictly causal: only `T[n], T[n−1], T[n−2], P[n], P[n−1], P[n−2]` and
   differences thereof. Nothing from time > n.
2. The target `T[n+1]` never appears as an input.
3. Lags are built **within a segment only** and only across exact 10 s steps; no feature spans a
   collection gap or an irregular interval.
4. The scaler is fitted on training rows only and applied unchanged to the test set.
5. Tail weights use training temperatures only.
6. PINN collocation points are synthetic; no measured hot-regime row is used in training.
7. Train and test sets are disjoint by construction (a 10 °C regime gap), verified numerically.
8. Multi-step rollout consumes only the seed temperature plus observed power; predicted
   temperatures are fed back, never observed ones.

## 15. GO / INVESTIGATE / KILL criteria

- **GO** — PINN beats **both** Model B and Model C on hot-regime RMSE by a margin that survives
  all sanity checks, on the multi-step task.
- **INVESTIGATE** — PINN is competitive with the strongest baseline but does not clearly beat it,
  or wins on one task and not the other.
- **KILL** — PINN is materially worse than the strongest baseline; or its advantage vanishes once
  the tail-weighted control is applied; or the physics term provides no measurable benefit
  (PINN-strict ≈ PINN-collocation ≈ plain MLP).

If KILL: stop. No rescue tuning, no added complexity, no re-selection of the trace.

## 16. Expected limitations

- One GPU on one host. A prototype, not a fleet study.
- 10 s sampling cannot resolve the fastest die thermal mode; only slower modes are identifiable.
- Power and temperature are strongly correlated (~0.94), so conditioning must be watched.
- No coolant inlet temperature in the Summit archive; `T_amb` is fitted, then sanity-checked
  against the known low-20s °C coolant rather than validated against a measured channel.
- A first-order lumped model is an approximation; GPU/HBM coupling and fan control are not modelled.
- Result establishes direction only. It does not establish novelty or publishability.

## 17. Exact directory structure

```
research_pinn_chip/
├── PROTOTYPE_BLUEPRINT.md      this file
├── README.md                   written after the run, with real numbers
├── RESEARCH_OPPORTUNITY_HUNT.md  (pre-existing, from the opportunity hunt)
├── data/
│   └── _trace_scan.csv         348-trace regime-coverage scan (small, derived)
├── src/
│   ├── data_loader.py          path config, trace selection, features, regime split
│   ├── classical_rc.py         Model A
│   ├── baseline_ml.py          Models B and C
│   ├── pinn.py                 Model D (strict + collocation)
│   └── evaluation.py           metrics, sanity checks, figure
├── experiments/
│   └── run_prototype.py        single entry point
└── results/
    ├── metrics.csv
    └── hot_regime_predictions.png
```
