# Measured, Not Simulated: Die-to-Memory Thermal Coupling Across Production GPUs

**Current status: KILL.** The two-node GPU/HBM coupled thermal model does **not** improve
held-out prediction over a one-node baseline on Summit telemetry. It is consistently *worse*,
across every GPU tested, and the fitted coupling is physically inadmissible in 7 of 8 traces.
The full result and the reasoning are below. No neural network, PINN, or ML model is used
anywhere in this study.

## 1. Research question

What is the thermal coupling between a GPU die and its stacked HBM memory on real deployed
hardware, how much does it vary across production GPUs, and does a simple coupled physical
model explain the observed die/HBM temperature dynamics better than a single-node model?

## 2. Why HBM matters

Modern accelerators stack memory next to (or on top of) the compute die in the same package.
That memory has a lower temperature limit than the logic does, so in practice it is often the
memory — not the processor — that decides when a chip must slow down. Every published number
for how strongly the die heats the memory comes from *simulation*, because per-device
measurements on deployed hardware have not been available. Summit's public dataset happens to
contain exactly those measurements.

## 3. What thermal coupling means

Two objects are thermally coupled if heat flows between them, so that heating one warms the
other. Here: the die makes heat, some escapes to the coolant, and some flows sideways into the
memory stacks. If that pathway matters, the memory's temperature should depend on the *die's*
temperature — not only on how much power the GPU is drawing.

That is the entire hypothesis, and it is what we test.

## 4. Dataset

Summit per-component power and thermal measurements
(OSTI/OLCF DOI 10.13139/OLCF/1861393, CC-BY-4.0), read **read-only** through a configurable
path. Nothing is copied or modified.

Verified directly (`docs/DATA_AUDIT.json`), not assumed from documentation:

| Property | Verified |
|---|---|
| Hosts available locally | 58 · **348 usable GPU traces** |
| Timestamps | monotonic, **0 duplicates** |
| Sampling | 10 s nominal; only exact 10 s steps within a segment are used |
| GPU power | float, 33–394 W on the selected trace |
| GPU die temperature | float, 27.0–67.1 °C |
| HBM memory temperature | float, 24.0–61.0 °C |
| **Channel mapping** | **verified empirically, 18/18 (100%)** — each die temperature's own power channel is its argmax correlate, so power/die/HBM provably refer to the same physical GPU |

## 5. Measurements used

Per GPU: `p{0,1}_gpu{0,1,2}_power` (P), `gpu{0..5}_core_temp` (T_g),
`gpu{0..5}_mem_temp` (T_m). Nothing else. No floorplan, no coolant inlet temperature (Summit
does not record one — the coolant temperature is fitted and then sanity-checked).

## 6. One-node model (Model A — baseline)

Die and HBM each obey their own first-order heat balance, driven by power, with **no** exchange
between them:

    dTg = dt * ( a_g*P − b_g*(Tg − Ta_g) )
    dTm = dt * ( a_m*P − b_m*(Tm − Ta_m) )

## 7. Two-node model (Model B — the hypothesis)

Same, plus a pathway carrying heat between die and memory:

    dTg = dt * ( a_g*P − b_g*(Tg − Ta) − c_g*(Tg − Tm) )
    dTm = dt * (            c_m*(Tg − Tm) − b_m*(Tm − Ta) )

A third **control (Model C)** lets the die temperature enter the HBM equation with a *free*
coefficient instead of as the physical difference `(Tg − Tm)`. It separates "die temperature is
informative" from "the physical coupling form is the right description".

## 8. Parameter meanings

| Symbol | Meaning | Must be |
|---|---|---|
| `a_g = 1/C_g` | how much a watt heats the die | > 0 |
| `b_g = 1/(R_g C_g)` | die-to-coolant cooling rate; `1/b_g` is the die time constant | > 0 |
| `c_g = 1/(R_gm C_g)` | die↔HBM pathway, as felt by the die | > 0 |
| `c_m = 1/(R_gm C_m)` | die↔HBM pathway, as felt by the memory — **the coupling term** | > 0 |
| `b_m = 1/(R_m C_m)` | HBM-to-coolant cooling rate | > 0 |
| `Ta` | effective coolant temperature | ≈ low 20s °C |

A negative `c` means heat flowing from cold to hot: thermodynamically impossible, and therefore
a hard rejection criterion rather than a number to be reported.

## 9. Experimental design

Chronological 60/15/25 train/validation/test on the longest continuous segment. Never shuffled.
All models fitted by ordinary least squares on **training data only** — the models are linear in
their parameters, so no iterative optimisation is involved and there is nothing to tune.

Evaluated on held-out test data, two tasks reported separately:
- **one-step**: predict the next sample from observed values.
- **multi-step (free-running, H = 30 = 300 s)**: seeded with the observed temperatures once, then
  fed only its own predictions plus observed future power. Every model gets the same seed and the
  same power and must predict **both** temperatures jointly. This is the primary test.

## 10. Results

Selected trace: **host `a07n04`, GPU 5** — chosen deterministically as the trace with the largest
power standard deviation (most thermal excitation, which is what makes coupling identifiable).
Selection never depended on model performance.

Split: train 104,482 · val 26,121 · test 43,535.

### Held-out multi-step RMSE (°C) — the primary comparison

| Model | HBM (T_m) | die (T_g) |
|---|---|---|
| **one-node** | **2.2174** | 1.9335 |
| unconstrained (control) | 2.3302 | 1.9333 |
| **two-node** | **2.5009** | **1.9246** |

The two-node model is **12.8% worse** at predicting HBM temperature. The die is a near-tie
(+0.46%).

### One-step RMSE (°C)

| Model | HBM | die |
|---|---|---|
| one-node | 1.1741 | 1.1970 |
| unconstrained | 1.1759 | 1.1985 |
| two-node | 1.1776 | 1.1985 |

Indistinguishable — one-step prediction cannot separate these models at all.

### Confirmation across 8 diverse hosts

| Check | Result |
|---|---|
| Two-node beats one-node on HBM | **0 / 8** |
| Two-node physically admissible | **1 / 8** (7 have `c_g < 0`) |
| Coupling lag resolvable at 10 s | **0 / 8** |
| Unconstrained control beats two-node | **8 / 8** |
| Median HBM gain | **−14.47%** (range −11.8% to −20.2%) |

## 11. Falsification tests

Five kill conditions were defined in advance. **Four triggered.**

| Condition | Result |
|---|---|
| K1 — two-node no better on held-out data | **TRIGGERED** — −12.8% on the primary trace, 0/8 fleet-wide |
| K2 — coupling not identifiable | passed — `c_m = 0.00255 > 0`, condition number 286 |
| K3 — physical constraints violated | **TRIGGERED** — `c_g = −6.7e-4` (negative conductance), 7/8 traces |
| K4 — explained by common power driver | **TRIGGERED** — the unconstrained control beats the physical model 8/8 |
| K5 — sampling artefact | **TRIGGERED** — partial cross-correlation of the die/HBM temperature *changes*, after removing the common power change, peaks at **lag 0** (0.85) with negative neighbours, in 8/8 traces |

**The code is not at fault, and this was tested rather than assumed.** `tests/test_core.py`
generates synthetic data from a two-node system with known positive parameters and confirms
(a) the estimator recovers those parameters to within 5%, and (b) the two-node model *does* beat
the one-node model on that data. The experiment can detect coupling when coupling exists.

## 12. Current conclusion

**Two-node GPU/HBM thermal coupling is not supported by the available Summit telemetry.**

The mechanism of failure is visible in `results/single_gpu_prediction.png` and in the fitted
parameters. Die and HBM temperatures correlate at 0.977. Given that collinearity, the two-node
fit splits the HBM dynamics into a large coupling term and a nearly-vanishing self-cooling term
(`b_m` → `tau_m ≈ 3000 s`, i.e. 50 minutes). With almost no restoring force, the HBM state simply
integrates upward during each free-running rollout and overshoots. The fit is not discovering a
thermal pathway; it is absorbing collinearity into an unphysical parameter split, which is
exactly what the negative `c_g` reports.

Behind that sits the deeper obstacle. At 10 s sampling — and these are 10 s *means*, not
instantaneous samples — die and HBM temperature changes move within the same sample. There is no
measurable lag, so the data cannot distinguish "the die heats the memory" from "both are heated
by the same power at the same time". Any real coupling on this package is faster than the
sampling interval, and no amount of modelling recovers timing information the measurement never
captured.

One further observation worth recording: on host `g14n16` GPU5 the median die temperature is
**1.0 °C below** its HBM temperature, contradicting the assumed die→HBM heat-flow direction on
that device.

## 13. Limitations

- **The negative result is specific to this measurement regime**, not to the physics. A package
  with 1 Hz or faster telemetry could well show resolvable coupling; Summit's public release
  provides only 10 s and 1 min means.
- Eight traces confirm the finding; the full 348 were not fitted, because a fleet-scale sweep
  is not warranted once the hypothesis has failed uniformly on a diverse sample.
- Forward Euler discretisation at 10 s is coarse relative to fast thermal modes.
- Summit records no coolant inlet temperature, so `Ta` is fitted rather than validated.
- A first-order lumped model per node is an approximation; a genuine coupling with a
  sub-10-second time constant would be invisible to this analysis by construction — which is the
  point of falsification test K5.

## 14. Reproduction

```bash
python research_hbm_thermal/experiments/run_single_gpu.py
```

```bash
python research_hbm_thermal/experiments/run_multi_gpu.py
```

```bash
python research_hbm_thermal/tests/test_core.py
```

Dataset path is set in `configs/default.yaml` and can be overridden with the
`GLASSCHIP_SUMMIT_DERIVED` environment variable. Deterministic: OLS fits, fixed seeds,
deterministic trace selection. Runtime ≈ 1 minute after the one-off trace scan (~30 s).
Requires numpy, pandas, pyarrow, matplotlib, PyYAML. No GPU.

Outputs: `results/single_gpu_metrics.csv`, `results/multi_gpu_metrics.csv`,
`results/single_gpu_summary.json`, `results/single_gpu_prediction.png`,
`results/trace_scan.csv`, `docs/DATA_AUDIT.json`.
