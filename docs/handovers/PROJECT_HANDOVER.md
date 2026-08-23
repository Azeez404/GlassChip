# GLASSCHIP — Full Project Handover

**Audience:** a programmer or AI assistant picking this repository up cold.
**Scope:** everything from V1 to the current state, in the order it happened, with the
reasoning behind each decision — not just what exists, but why it exists and what was
deliberately abandoned.

**Read this file first.** `docs/handovers/HANDOVER.md` is the older, V1-only handover and is
still accurate for V1; this document supersedes it as the whole-project entry point.

**Last updated:** 2026-08-23. Nothing in this session was committed; the working tree holds
uncommitted work (see §9).

---

## 0. One-paragraph summary

GLASSCHIP is an empirical research project on **how the quality of a supercomputer's own
temperature/power telemetry affects the thermal models you can identify from it**. V1 asked
whether a physics-informed neural network could beat classical first-order physics on CINECA
Marconi100 data and found it could not. V2 turned that into a rigorous measurement-quality
study on Oak Ridge's Summit, which is **complete and journal-submittable** — that manuscript is
the project's main asset. Three subsequent exploratory branches (a PINN opportunity hunt, a PINN
prototype, and a GPU/HBM thermal-coupling study) all returned **honest negative results** and are
documented as such. The single most important thing a newcomer can do is **submit the finished
V2 paper**; the second is to read §7 before proposing any new neural-network idea.

---

## 1. Repository map

```
GlassChip/
├── README.md                      V1 usage
├── requirements.txt
├── data/                          M100 ExaData 21-03 (1.2 GB, public, NOT committed)
├── src/                           V1 pipeline (LOCKED) + additive alignment layer
│   ├── loader/                    M100 dataset loader (LOCKED)
│   ├── preprocessing/             V1 preprocessor (LOCKED)
│   ├── baseline/  screening/  validator/  visualization/
│   ├── pinn/                      V1 PINN (thermal_pinn.py) — historical, do not reuse
│   └── alignment/                 NEW, additive: causal as-of alignment for M100
├── tests/                         tests for src/alignment
├── docs/
│   ├── RESEARCH_SUMMARY.md        V1 scientific story
│   └── handovers/
│       ├── HANDOVER.md            V1-only handover (older)
│       └── PROJECT_HANDOVER.md    <- THIS FILE
├── v2_research/                   ** THE MAIN ASSET **
│   ├── summit/                    Summit data + Phase 2 experiments (12 GB, NOT committed)
│   ├── paper_analysis/            canonical analysis pipeline, manifest, validator
│   └── paper/                     manuscript + strategy audits
├── research_pinn_chip/            Branch 1: PINN hunt + prototype — KILLED
└── research_hbm_thermal/          Branch 2: GPU/HBM coupling — KILLED
```

**Data is never committed.** `data/` (1.2 GB) and `v2_research/summit/` (12 GB) are public
datasets held locally and referenced by path/config.

---

## 2. GLASSCHIP-V1 — the origin (FROZEN)

**Question:** can a PINN learn thermal behaviour that classical first-order physics cannot
already explain, from the same observable inputs?

**Answer: No.** A rigorous negative result. See `docs/handovers/HANDOVER.md` and
`docs/RESEARCH_SUMMARY.md`.

- **Dataset:** M100 ExaData (CINECA Marconi100), record `21-03`, CC-BY-4.0.
- **Locked inputs:** `p0_core0_temp`, `p0_power`, `fan0_0` — the IPMI triple sharing an exact
  20 s grid.
- **Status:** frozen at commit `7cbfd1d` (Release GLASSCHIP-V1.0). `src/loader`,
  `src/preprocessing`, and the V1 PINN are LOCKED. Do not modify them.

**Relevant detail for anyone tempted to revive the PINN:** `src/pinn/thermal_pinn.py` already
implements a quantization-aware dead-zone data loss plus an ODE residual physics loss. It was
tried and it underperformed. This is settled in-house, not a matter of opinion.

---

## 3. GLASSCHIP-V2 — the main asset (COMPLETE, UNSUBMITTED)

### 3.1 What it is

An **empirical HPC measurement-quality study** on the Summit supercomputer:

> How does telemetry quality — temperature quantization, sampling rate, spatial aggregation —
> affect identification of a first-order thermal model, and does better telemetry also make the
> unexplained residual more predictable?

It is **not** a PINN paper, not a new method, not a monitor, not a digital twin. The project
README enumerates forbidden claims; respect them.

### 3.2 Data

Summit per-component power and thermal measurements, OSTI/OLCF DOI `10.13139/OLCF/1861393`,
CC-BY-4.0. Locally: `v2_research/summit/derived/cleaned/host=*/data.parquet`, 58 hosts,
33 columns, ~1.19 M rows/host, 10 s grid, `segment_id` marking collection gaps.
Raw SHA-256 recorded: `9898170b…996e`.

**Important verified fact:** the public release ships **10 s and 1 min means only**; the
original 1 Hz data is *not* included. This pre-empts the obvious "why not 1 Hz?" reviewer
question and should be stated in the paper.

### 3.3 Experimental design

Five measurement-quality conditions applied to the *same* hardware and workload:

| Condition | Degradation |
|---|---|
| F0 | full quality — socket-mean temperature, float, 10 s |
| F1 | temperature quantized to 1 °C |
| F2 | downsampled 10 s → 20 s |
| F3 | hottest-core proxy instead of socket mean |
| F4 | all three combined |

Frozen first-order ARX `T[n+1] = αT[n] + βP[n] + γ`, effective τ = −Δt/ln α. Moving-block
bootstrap for uncertainty. 116 host-sockets for the fleet analysis; 20 for the ablation.

### 3.4 Headline numbers (validated, 44/44 checks)

- τ: F0 393.8 s · F1 115.8 s (0.29×) · F2 910.5 s (2.31×) · F3 282.6 s · F4 352.0 s
- Fleet (116 units): median 439 s, min 205 s, P05 275 s, P95 1200 s, max 2596 s
- **Key result (C4):** the quantized estimate (116 s) falls **below the entire observed
  full-quality range** (min 205 s) — a measurement artifact exceeding real unit-to-unit variation
- Residual out-of-sample R² ≤ 0.066 (near permutation null) — better telemetry does *not* improve
  residual predictability
- Online rolling-τ: computable at 0.041 ms/window, but no useful standalone monitoring signal

### 3.5 Reproduction

```bash
python v2_research/paper_analysis/run_all.py
```
→ validate (44/44) → tables → figures → manifest. Seeds 0. Raw data read-only.

### 3.6 Status and what remains

Manuscript at `v2_research/paper/manuscript.md` is **fully drafted (693 lines)** and
journal-submittable after four fixes. All four are prose/citation work, roughly one day:

1. **Resolve every `[VERIFY]` citation** — 12 of 15 references are unverified; `arXiv:2607.28962`
   must be confirmed to exist as cited. This is a desk-reject and integrity risk.
2. **Stop calling 116 sockets "the fleet"** — it is 58 hosts of Summit's 4,626 nodes. Use "the
   116 sampled host-sockets" and restate C4 regime-relatively.
3. **Explain the F2 anomaly** (~150 words) — for a true first-order process τ is *invariant* to
   decimation, so 394 → 910 s is evidence of unmodelled fast dynamics, meaning F0 is a *reference
   regime*, not ground truth. Currently the most exploitable hole in the paper.
4. **Cite Ellis/Shin et al. SC'21** (`10.1145/3458817.3476188`) and state that the 1 Hz Summit
   source is not in the public release.

---

## 4. Strategy audits (in `v2_research/paper/`)

Four audit documents, written in this order. Later ones supersede earlier ones where they
conflict.

| File | Verdict |
|---|---|
| `SUBMISSION_STRATEGY_AUDIT.md` | GREEN. Venue landscape, three-persona adversarial review, novelty 52/100, publishability 74/100 |
| `NOVELTY_IMPACT_UPGRADE_AUDIT.md` | Highest-ROI upgrade identified — see §4.1 |
| `PINN_SCIENTIFIC_ML_REDESIGN_AUDIT.md` | ABANDON PINN; use physics-constrained inverse modelling with **no** neural network |
| `RESEARCH_OPPORTUNITY_HUNT.md` | Next-project hunt → GPU die↔HBM coupling (subsequently tested and killed, §6) |

### 4.1 The highest-ROI unexploited finding

`v2_research/summit/observability_ablation/observability_ablation_results.json` stores `taus` as
a **20-element per-unit list for every condition** — fully paired across F0–F4. **The manuscript
uses only the medians.** Per-unit analysis is free and changes what the paper is about:

- Per-unit F1 ratios span **0.18–0.52**, not a single 0.29× — bias is unit-dependent, so no
  global calibration factor can correct it.
- Spearman ρ(τ_F0, τ_Fk): F2 **0.96**, F1 **0.68**, F3 **0.44**, F4 **0.46** — spatial aggregation
  appears to scramble fleet *ordering*, which errors-in-variables theory does not predict.
- **Caveat, verified:** at n=20 the rank result has a bootstrap 95% CI of [−0.06, 0.80] and
  **cannot currently be claimed**. Extending the F0–F4 ablation from 20 to all 116 units (same
  frozen code; Phase 2D already proved 116-unit runs work) would make it defensible and
  simultaneously answer the obvious "why only 20 units?" objection.

### 4.2 A trap that was caught, and must not be re-introduced

τ = −Δt/ln α is strongly nonlinear. In τ-space, quantization looks like a 6× *compression* of
fleet dispersion. In the underlying α it is a 2× *expansion*. **The apparent F1 homogenization
is an artifact of the parameterization.** Any claim about population spread must be shown in
both τ and α, or restricted to rank statistics (Spearman is transform-invariant). F3/F4
compression is real; F1 compression is not.

### 4.3 Physics available for free, never exploited

The ARX coefficients α, β, γ are stored in `v2_research/summit/counterfactual/phase2a_results.json`
and map exactly onto the lumped RC model: `α = exp(−Δt/RC)`, `β = R(1−α)`, `γ = (1−α)·T_amb`.
Recovering R, C and an inferred ambient from coefficients already computed gives:

- **Inferred ambient median 26.0 °C, 100% of units in a plausible 5–45 °C** — against Summit's
  known low-20s °C water cooling. An independent physical validation nobody has run.
- **10% of units yield R ≤ 0** — a thermodynamically impossible negative resistance that OLS
  accepts. A free, parameterization-independent physics-violation detector.

---

## 5. Branch 1 — `research_pinn_chip/` (KILLED)

Clean-room search for a defensible PINN problem in chips/processors, then a prototype.

**Prototype result** (`research_pinn_chip/README.md`), Summit `a11n12` GPU5, train <45 °C,
test >55 °C, free-running 30-step:

| Model | RMSE (°C) |
|---|---|
| GBT | **4.44** |
| Classical RC | 4.88 |
| GBT tail-weighted | 6.91 |
| **PINN** | **27.81** |

All 30 sanity checks passed. The PINN diverged to 117 °C where truth was 60 °C — a
**physics-induced runaway** caused by a soft physics penalty at out-of-distribution collocation
points. The three-parameter classical RC beat every neural variant.

Two further hunts followed (`RESEARCH_OPPORTUNITY_HUNT_V2.md`,
`RESEARCH_OPPORTUNITY_FINAL_AUDIT.md`), the last covering semiconductor degradation.
**Conclusion: NO VIABLE PINN PROJECT FOUND.** Reasons in §7.

---

## 6. Branch 2 — `research_hbm_thermal/` (KILLED)

Tested whether a two-node coupled model (GPU die ↔ HBM memory) explains Summit telemetry better
than two independent one-node models. Production-grade: config-driven, 7/7 tests passing.

**Held-out multi-step RMSE (°C), `a07n04` GPU5:**

| Model | HBM | die |
|---|---|---|
| one-node | **2.2174** | 1.9335 |
| unconstrained control | 2.3302 | 1.9333 |
| two-node | 2.5009 | **1.9246** |

Confirmed across 8 diverse hosts: two-node beats one-node on HBM **0/8**; physically admissible
**1/8**; coupling lag resolvable **0/8**; unconstrained control beats the physical model **8/8**.
Median HBM change **−14.5%**.

**Four of five pre-registered kill conditions triggered.** Root cause: die/HBM correlate at
0.977; the fit absorbs that collinearity into a large coupling term plus a near-zero HBM
self-cooling term (`tau_m ≈ 3000 s`), so the HBM state integrates upward and overshoots. `c_g`
comes out **negative** — an impossible thermal conductance — in 7/8 traces. Underneath: partial
cross-correlation of temperature *changes*, with the common power change removed, peaks at
**lag 0** in 8/8 traces. At 10 s means, die and HBM move within one sample, so the data cannot
separate "die heats memory" from "both heated by the same power".

**The code was validated, not assumed:** `tests/test_core.py` generates synthetic two-node data
with known positive parameters, confirms the estimator recovers them within 5%, **and** confirms
the two-node model does beat one-node on that data. The failure is about the data, not the
implementation.

---

## 7. Why every neural/physics-informed direction failed — read before proposing another

Four structurally distinct attempts died, consistently:

1. **GPU hot-regime thermal prediction** — killed experimentally (§5).
2. **Thermal fields / hotspots / IR drop** — physics is known and *linear*, so classical solvers
   and CV surrogates dominate; geometry-dependent formulations need floorplans that are
   proprietary for exactly the chips with public telemetry.
3. **Leakage–temperature feedback** — killed on verified data: the signal is ~0.1–0.3 W on a 35 W
   baseline and fatally confounded, since power causes temperature and produces that correlation
   with zero leakage present.
4. **Semiconductor degradation** — the "hidden" state is directly measured; extended Kalman and
   particle filters already solve it in the source NASA paper; the published prognostics analysis
   uses **one device over 210 minutes**; no free multi-device public dataset exists.

**The generalization:** physics-informed neural learning pays off when physics is
high-dimensional or nonlinear, the operator is unknown, and labels are scarce relative to model
complexity. Chip problems reachable with *public* data are the opposite — low-dimensional,
linear or monotone, known operators, and either abundant telemetry or a handful of devices.
There, classical estimation (least squares, Kalman, particle filtering, sparse solvers) is not
merely competitive; it is the right tool.

Saturated areas confirmed by literature search: chip thermal surrogates (DeepOHeat line),
PINN sparse-sensor thermal field reconstruction, PINN inverse heat conduction, PINN datacenter
thermal control, physics-informed RUL for power semiconductors.

**Do not add a neural network to this project unless a new experiment independently
demonstrates it is necessary.**

---

## 8. Recommended next actions, in priority order

1. **Submit the V2 paper.** Apply the four fixes in §3.6, then submit to **FGCS** or **JPDC**
   (rolling). This is the only near-certain outcome in the portfolio and it is being delayed by
   searching for a neural angle it does not need.
2. **Optional strengthening before submission** (~1.5–2.5 weeks): extend the F0–F4 ablation to
   all 116 units and report per-unit paired outcomes (§4.1), plus the free R/C recovery and
   physics-admissibility rate (§4.3). This raises novelty from ~38 to ~62 and opens conference
   venues (CCGrid 2027, abstract 24 Nov / paper 1 Dec 2026; IPDPS 2027 Measurements track,
   abstract 1 Oct / paper 8 Oct 2026 — verify these dates before relying on them).
3. **Do not** revive PINNs, build a benchmark, or claim the alignment module as a contribution.

---

## 9. Repository state and hygiene

- **Nothing from the recent sessions is committed.** `git status` shows modified `.gitignore`
  and `docs/handovers/HANDOVER.md`, plus untracked `research_hbm_thermal/`,
  `research_pinn_chip/`, `src/alignment/`, `tests/`, `v2_research/`.
- Last commit: `7cbfd1d` Release GLASSCHIP-V1.0.
- **Locked, do not modify:** `src/loader`, `src/preprocessing`, the V1 PINN, Phase 2/3 artifacts,
  `v2_research/paper_analysis/`, canonical figures and tables, raw data.
- `src/alignment/` is **additive** — it does not touch the frozen V1 pipeline. Keep it that way.
- Environment: numpy 2.5.1, pandas 3.0.3, scipy 1.18.0, scikit-learn 1.9.0, torch 2.13.0+cpu,
  matplotlib 3.11.0, pyarrow 25.0.0, PyYAML. **XGBoost/LightGBM are not installed**;
  scikit-learn's `HistGradientBoostingRegressor` was substituted and this is documented in the
  affected branch. `pytest` is not installed; `research_hbm_thermal/tests/test_core.py` has a
  built-in runner and executes directly.

---

## 10. Reproduction commands

```bash
python v2_research/paper_analysis/run_all.py
```

```bash
python research_hbm_thermal/experiments/run_single_gpu.py
```

```bash
python research_hbm_thermal/tests/test_core.py
```

```bash
python research_pinn_chip/experiments/run_prototype.py
```

Dataset paths are configurable: `research_hbm_thermal/configs/default.yaml`, or the
`GLASSCHIP_SUMMIT_DERIVED` environment variable.

---

## 11. Working principles this project has followed

Worth preserving, because they are why the negative results are trustworthy:

- **Verify data before designing around it.** Several promising ideas died in minutes because a
  channel was all zeros (M100 per-GPU power), a signal was confounded (leakage), or a dataset had
  one device (NASA MOSFET). Check first.
- **Pre-register kill conditions**, then honour them. No rescue tuning.
- **Validate the tooling on synthetic ground truth** so a negative result is a statement about
  the data rather than the code.
- **Distinguish evidence from inference** in every document, and mark unverified citations.
- **A negative result, honestly established, is a real outcome.** Three of this project's four
  scientific conclusions are negative, and they are the reason the surviving positive one (V2's
  C4) is credible.
