# GLASSCHIP-V2 — Escape-Route Audit (correction + new direction)

**This corrects a prior committed conclusion.** `V2_DECISION.md` /
`PHASE_V2_ALPHA_REPORT.md` stated: *"No accessible public dataset supplies
node-level co-located processor temperature + power at sub-20 s resolution."*
That is **refuted** by the ORNL **Summit** power-and-thermal dataset, verified
below from primary sources. V1 remains frozen; all work stays in `v2_research/`.

## The dataset the prior audit missed

**Long-Term Per-Component Power & Thermal Measurements of the OLCF Summit
System** — ORNL AAIMS team.
- DOI `10.13139/OLCF/1861068`; OSTI `1861393`; GitHub
  `at-aaims/summit_power_and_thermal_data`. License **CC-BY-4.0**.
- **Per-component CPU-core temperatures (23 cores × 2 Power9) and GPU
  core/memory temperatures, float32 °C — NOT 1 °C-quantized.**
- Per-CPU DC power, per-GPU DC power (6× V100), per-node AC power.
- Originally 1 Hz; **public release = 10 s and 1 min means** (raw 1 Hz not
  released). Parquet/Snappy. 4,626 nodes; 5 month-segments (2020–2022).
- **Sample = 15.9 GB (obtainable here); full = 612 GB.**
- Coolant inlet ≈ **constant 21 °C** (medium-temp direct liquid cooling +
  rear-door HX). **No per-node coolant variation, no fan.**

**Why this is the ideal V1 companion:** Summit is the *same hardware class* as
Marconi100/M100 — IBM AC922, **Power9 + V100** (Summit 6 GPU/node, M100 4).
Same thermal physics; **the only material difference is instrumentation.**
It therefore isolates *observability* as the variable, which is exactly V1's
open question.

## What changes vs the M100 barriers V1/V2 blamed

| V1/V2 barrier | On Summit |
|---|---|
| Temperature quantized to 1 °C (0.39 °C floor; kills finite differences) | **float32 temps — barrier removed** |
| No per-component co-located temp+power | **per-core temp + per-CPU/GPU power — present** |
| 20 s sampling | 10 s means (**2× finer only — modest**; raw 1 Hz not public) |
| No known thermal boundary | **known constant 21 °C coolant** (boundary fixed, not missing) |
| τ_eff poorly identified (quantization-contaminated) | testable — quantization no longer contaminates dT/dt |

## Novelty position (verified)

Prior Summit work (SC'21 "Revealing power, energy and thermal dynamics…";
"Not All GPUs Are Created Equal", arXiv 2208.11035) is **descriptive
characterization / variability statistics**, not physics-informed system
identification. The ORNL **SMC Data Challenge** explicitly poses node-level
physics thermal modelling (2 CPU + 6 GPU, cooling-flow split) as an **open
question** — evidence the direction is unsolved, not crowded. Physics-informed
*state-estimation-from-quantized-sensors* is established in adjacent domains
(motor/battery/building, MAE ≈ 0.2–0.7 °C) — a method precedent, not a done
HPC result.

## Decision

Pivot V2 to **GLASSCHIP-V3: physics-guided thermal system identification +
observability on Summit**, using V1's *identical* first-order baseline as the
frozen control. First experiment and kill criteria: see chat / next module.
V1 untouched; anchor `8473342129fb19f0` intact.
