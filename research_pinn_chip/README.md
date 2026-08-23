# Clean-room PINN prototype — GPU temperature prediction in the data-scarce hot regime

Independent research branch. No GLASSCHIP model, PINN, preprocessing pipeline, or result is
imported or reused. The public Summit dataset is read **read-only** through a configurable path.

**Verdict: KILL.** The physics-informed model lost decisively to a plain gradient-boosted tree.
All 30 automated sanity checks passed, so this is a real negative result, not an implementation
artifact. Details below.

# Research Question

Can physics-informed learning improve GPU temperature prediction in the high-temperature regime
where real production telemetry is data-scarce?

# Hypothesis

In the abundant cool regime a black-box model wins and physics adds nothing. In the sparse hot
regime a model whose loss embeds a thermal energy balance should degrade *gracefully*, because
the physics term constrains behaviour where training data is absent.

**This hypothesis was not supported.**

# Dataset

Summit per-component power and thermal measurements (OSTI/OLCF DOI 10.13139/OLCF/1861393,
CC-BY-4.0), read from the local derived tables. Verified directly rather than assumed:
timestamps monotonic with zero duplicates; `dt_s` = 10 s for >99.9% of rows; `segment_id` marks
collection gaps; per-GPU power 17–400 W (float); GPU core temperature (float).

Channel mapping verified by correlation (clean diagonal):
`gpu{0,1,2}_core_temp` ↔ `p0_gpu{0,1,2}_power`, `gpu{3,4,5}_core_temp` ↔ `p1_gpu{0,1,2}_power`.

# Selected GPU

**host `a11n12`, GPU 5** — chosen deterministically as the trace with the most hot-regime
(>55 °C) samples among all 348 traces (58 hosts × 6 GPUs), subject to ≥100,000 cold samples,
ties broken by (host, gpu). Selection never depended on model performance.

Trace: 1,191,322 valid rows · 929,038 cold · 184,293 transition · 77,991 hot · T max 74.8 °C ·
T median 35.0 °C · P max 369 W.

# Data Regime

After causal filtering (lags formed only across exact 10 s steps inside a segment):

| | count |
|---|---|
| Total usable observations | 1,190,696 |
| **Train** (all temps < 45 °C) | **914,928** |
| **Hot test** (all temps > 55 °C) | **73,233** |
| Excluded (45–55 °C transition) | 202,535 |
| Hot fraction of usable rows | 6.15% |

Train and test are disjoint by construction with a 10 °C gap, verified numerically.
All models predict the **increment** ΔT = T[n+1] − T[n], deliberately, so the tree baselines
cannot fail trivially by being unable to output a temperature outside their training range.
This makes the baselines as strong as possible.

# Models

## Classical RC
Three-parameter first-order lumped model, ordinary least squares on the training regime only.
Fitted: τ = 341.6 s, T_amb = 30.66 °C, a > 0 and b > 0 (**physically admissible**).

## XGBoost
**XGBoost and LightGBM are not installed in this environment.** `HistGradientBoostingRegressor`
from scikit-learn was used instead — the direct equivalent (histogram-based gradient boosted
trees, same algorithm family, `sample_weight` support). Substitution documented, not silent.
400 iterations, lr 0.05, depth 6, seed 0.

## Tail-weighted XGBoost
Identical model with training weights `w = clip(exp((T − median)/std), 1, 50)` computed from
**training temperatures only**. This is the control that tests whether any PINN advantage is
merely the tree under-weighting rare warm samples.

## PINN
New minimal model: MLP (8 → 64 → 64 → 1, tanh) predicting ΔT, with jointly learned physical
parameters a, b (softplus, strictly positive) and T_amb. Four variants trained: primary
(λ = 1, synthetic collocation), strict (λ = 1, training points only), ablation (λ = 0, i.e. a
plain MLP), and λ = 10.

# Physics Formulation

    C · dT/dt = P − (T − T_amb) / R

**In plain English:** the GPU turns electrical power into heat, which raises its temperature. At
the same time it loses heat to its coolant, faster the hotter it is relative to that coolant.
Temperature changes according to the balance of the two.

Discretised at Δt = 10 s, with a = 1/C and b = 1/(RC):

    ΔT[n] = Δt · ( a·P[n] − b·(T[n] − T_amb) )

**a** is how fast a watt heats the chip up (small heat capacity → heats faster). **b** is how
fast heat leaks away to the coolant; its reciprocal 1/b is the thermal time constant — roughly
how many seconds the chip takes to respond to a change in power. **T_amb** is the effective
temperature of whatever the chip is dumping heat into.

Loss: `L = L_data + λ · L_physics`, where `L_data` is mean squared error on ΔT over training
samples and `L_physics` is the mean squared ODE residual `ΔT̂/Δt − (a·P − b·(T − T_amb))`. The
physics residual needs no labels, which is what lets it be evaluated where no training data
exists.

# Experimental Protocol

- **One-step**: predict T[n+1] from observed causal features at n, over all 73,233 hot samples.
- **Multi-step (free-running, H = 30 steps = 300 s)**: seed with the observed temperature at the
  start of a contiguous hot block, then roll forward on the model's own predictions, consuming
  only observed future power. 12 qualifying blocks × 30 steps = 360 points.

**Leakage controls**: features strictly causal (T, T₋₁, T₋₂, P, P₋₁, P₋₂, ΔP, ΔT); target never
an input; lags never span a gap or an irregular interval; scaler fitted on training rows only;
tail weights from training temperatures only; PINN collocation points **synthetic**, so no
measured hot-regime row enters training; rollout feeds back predicted, never observed,
temperatures. Verified: train max 44.98 °C < test min 55.01 °C, zero shared timestamps.

# Results

Hot regime (>55 °C), all values in °C. **Lower is better.**

### Multi-step, H = 30 (the decision task) — n = 360

| Model | RMSE | MAE | Max Error |
|---|---|---|---|
| **GBT** | **4.4425** | **3.8674** | 10.1692 |
| Classical RC | 4.8778 | 4.3822 | 10.5803 |
| PINN-strict *(ablation)* | 6.2377 | 5.2164 | 14.2436 |
| MLP, λ=0 *(ablation)* | 6.5962 | 5.5809 | 14.7782 |
| GBT (tail-weighted) | 6.9127 | 6.1473 | 13.2970 |
| **PINN** | **27.8139** | 22.3375 | 72.5185 |
| PINN, λ=10 *(ablation)* | 27.8305 | 22.8633 | 67.9873 |

### One-step — n = 73,233

| Model | RMSE | MAE | Max Error |
|---|---|---|---|
| **GBT** | **0.5271** | **0.3648** | 9.6222 |
| PINN-strict *(ablation)* | 0.5831 | 0.4447 | 9.5178 |
| MLP, λ=0 *(ablation)* | 0.6091 | 0.4746 | 9.4663 |
| GBT (tail-weighted) | 0.6101 | 0.4669 | 9.4234 |
| Classical RC | 0.6187 | 0.4752 | 9.2846 |
| PINN | 2.3643 | 2.1373 | 12.3410 |
| PINN, λ=10 *(ablation)* | 3.0793 | 2.7880 | 13.3165 |

Sanity checks: **30 / 30 passed** (no NaNs, no infinities, timestamps ordered, no duplicates,
regimes disjoint with a 10.03 °C gap, no timestamp overlap, all prediction shapes correct, no
numerical explosion in the reported one-step outputs).

# GO / INVESTIGATE / KILL Verdict

## KILL

Against the criteria fixed in `PROTOTYPE_BLUEPRINT.md` before the run:

1. **The PINN loses to both ML baselines**, by 526% versus the best (27.81 vs 4.44 RMSE).
2. **The physics term makes things worse, not better.** The same network with the physics term
   removed (λ=0) scores 6.60; with physics on synthetic collocation points it scores 27.81.
   Increasing λ to 10 does not help (27.83). The constraint is actively harmful.
3. **The classical RC alone (4.88) beats every neural variant.** If simple physics is what
   matters here, the three-parameter model already delivers it, and the network adds nothing.

The failure mode is visible in `results/hot_regime_predictions.png`: the PINN diverges
monotonically upward to 117 °C where the truth is 60 °C — a **physics-induced thermal runaway**.
Enforcing the energy balance at synthetic points spanning 20–80 °C and 17–400 W pushed the
learned parameters toward a regime where the network predicts a persistently positive ΔT, which
compounds under free-running rollout. This is a documented PINN failure mode (competing loss
terms, out-of-distribution collocation), consistent with the published literature on PINN
extrapolation limits found during the opportunity hunt.

One nuance worth recording: **PINN-strict (6.24) does modestly beat the identical network with
no physics at all (6.60)**, so the physics term is not useless when evaluated only where data
exists. But it is a 5% gain on a variant that is itself 40% worse than a plain gradient-boosted
tree. That is not a research direction.

Per the pre-registered stop condition, no rescue tuning was performed, no trace was re-selected,
and no additional complexity was added.

# Limitations

- **One GPU on one host.** A prototype, not a fleet study. A different trace could behave
  differently — though the selected trace was the *most* hot-data-rich of 348, which if anything
  favoured the PINN.
- The selected trace's hot fraction is 6.15%, far above the fleet median of 52 samples per
  trace. The genuinely data-scarce case was therefore **not** the one tested; testing it would
  make the ML baselines weaker but would not rescue a model that diverges.
- 10 s sampling cannot resolve the fastest die thermal mode.
- Power and temperature correlate ~0.94, so the design matrix is poorly conditioned.
- No coolant inlet temperature exists in the archive; T_amb was fitted (30.66 °C) and is
  plausible but somewhat above Summit's known low-20s °C coolant, consistent with a lumped
  first-order model absorbing package and board thermal resistance into one term.
- A first-order lumped model ignores GPU↔HBM coupling and fan/cooling control.
- Only one PINN architecture family was tried. A different formulation might behave better —
  but the burden of evidence now sits with that claim, and the classical RC baseline sets a bar
  that a neural model must clear to be worth the complexity.

# Reproducibility

Deterministic: fixed seeds (0) throughout, deterministic trace selection, no shuffling outside
seeded generators.

```bash
python research_pinn_chip/experiments/run_prototype.py
```

Reads Summit from `v2_research/summit/derived/cleaned` by default; override with the
`GLASSCHIP_SUMMIT_DERIVED` environment variable. Runtime ≈ 3 minutes on CPU; no GPU required.
Outputs `results/metrics.csv`, `results/summary.json`, `results/hot_regime_predictions.png`.

Environment: numpy 2.5.1, pandas 3.0.3, scikit-learn 1.9.0, torch 2.13.0+cpu, matplotlib 3.11.0,
pyarrow 25.0.0. XGBoost/LightGBM unavailable; scikit-learn's histogram GBT substituted.
