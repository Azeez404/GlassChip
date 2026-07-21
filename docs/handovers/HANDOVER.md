# GLASSCHIP — SESSION HANDOVER

**Date:** 2026-07-21
**Status:** Dataset Exploration COMPLETE. GATE A RESOLVED (PASS). GATE B OPEN. 5 reports and 9 diagnostic plots generated.
**Owner hardware:** Intel Core 5 210H (4P+4E, 12T, Raptor Lake-H Refresh) · RTX 4050 Laptop 6 GB · 16 GB DDR5 · Windows 11

---

## 0. READ THIS FIRST

Dataset exploration of M100 ExaData (record `21-03`, March 2021) is **100% COMPLETE**.

### GATE A — Sampling Interval Resolution: ✅ RESOLVED (PASS)
- **Per-node sampling interval:** **20.0 s** median (`p0_power`, 11,167 samples/node over ~30 days).
- **Thermal time constant ($\tau_{th}$):** Estimated 50–200 s for liquid-cooled POWER9.
- **Verdict:** Sampling interval is 2.5–10× below $\tau_{th}$. **$C_{th}$ estimation is FEASIBLE** from natural workload transients.

### GATE B — Node ID Stability Across Records: ⚠️ OPEN
- Data ships as 12–13 separate Zenodo records.
- Record `21-03` node IDs are Strings (`'0'`, `'1'`, ..., `'979'`) representing 980 nodes.
- **Status:** Unverified across multiple periods (only record `21-03` is locally downloaded).

### Additional Sensor & Parameter Verification
1. **Temperature Sensors:** 48 sensors per node (24 POWER9 cores per socket for P0 & P1, VDD regulator, DIMMs, 4× NVIDIA V100 GPU core + HBM memory).
2. **Power Channels:** Separate per-socket CPU power (`p0_power`, `p1_power`), total node power, memory power, and GPU card power.
3. **Voltage & PSU telemetry:** Mains input AC voltage (230V), PSU output DC voltage (12.2V), output DC current (28A).
4. **Cooling Loop Telemetry:** Schneider Electric SCADA values are integer-encoded tenths of a degree (°C × 10). Supply: 18.2 °C median (17.2–20.3 °C); Return: 24.2 °C median (23.3–25.6 °C); ΔT: 6.0 °C.

---

## 1. WHAT THIS PROJECT IS NOW

> **GLASSCHIP-V1 — Physics-Constrained Thermal Modelling of Fleet-Scale Processor Telemetry**
> Single public dataset (M100 ExaData). Classical + physics-guided thermal models. `Rth` estimation. Cooling behaviour. Longitudinal drift. No PINNs.

**Primary contribution:** physics-constrained thermal modelling of fleet-scale processor telemetry.
**Secondary:** `Rth` estimation · cooling behaviour characterisation · longitudinal analysis · physics-guided ML.
**NOT a contribution:** the dataset (it is someone else's), novel architectures, new sensors, digital twins, processor health.

---

## 2. HOW WE GOT HERE (six adversarial phases)

| Phase | Question | Outcome |
|---|---|---|
| **0** | Battery SOH via PINNs on a Kaggle laptop-battery table | **KILLED.** Not a PINN (`Q₀−kt` is algebraic, not differential; inputs categorical). Circular synthetic target. Target leakage via `Performance Rating`. Field saturated (Nature Comms 2024 + PINN4SOH + ≥12 more). Score 0.8/10. |
| **1** | Pivot to processor thermal/reliability. What data exists? | Real PDE now (heat equation) — genuine improvement. But chip-thermal PINN is a live DAC/ICCAD subfield (DeepOHeat 300,000× @ <0.1 K). **No public CPU RUL/failure data exists at all.** |
| **2** | Is it feasible on this laptop? | Yes for thermal, no for aging. **Existential finding: heat conduction is linear → an RC network is its exact discretisation, not an approximation. A PINN is a worse-conditioned way to fit a linear system.** |
| **3** | Smallest defensible version | Measurement-science benchmark. PINNs removed. Design for "RC wins" as a publishable outcome. |
| **4** | Implementation-ready spec | Full design: 8 instrument validations, 4 experiments, 5 degradation states, 5 classical models, 309 runs, ~$60 hardware, 10 weeks. |
| **5** | Public data only (no hardware) | **Constraint killed the Phase-4 design** — no public dataset has open-loop excitation, degradation labels, or recovery controls. **But M100 ExaData found: 980 nodes, 934 days, CC-BY-4.0.** Gives fleet + timescale that self-collection never could. |
| **6** | Final destroy audit | **Verdict C — remove ~30% and build**, gated on GATE A + GATE B. |

**Key reversal:** Phase 2 said longitudinal degradation was impossible on an internship timeline. Phase 5's M100 makes it possible — 934 days already collected. The trade is **causality for scale**: M100 is observational and closed-loop, so no controlled experiments and no instrument validation.

---

## 3. LOCKED SCOPE

### Dataset — ONE, no fusion, no collection, no purchases
**M100 ExaData** (CINECA Marconi100)
- Borghesi et al., *Nature Scientific Data* (2023), DOI `10.1038/s41597-023-02174-3`
- Zenodo `10.5281/zenodo.7588815` → `7590583` (12–13 records; source count disagrees — verify)
- **CC-BY-4.0**, free, no registration
- 980+ nodes · 934 days (2020-03-09 → 2022-09-28) · 573 metrics · Parquet+zstd · 49.9 TB raw / ~372 GB compressed
- Node hardware believed IBM POWER9 AC922 + 4× V100 — **UNVERIFIED**

### Inputs — MANDATORY (5)
Temperature · CPU power · clock frequency · CPU utilisation · fan speed
**OPTIONAL:** cooling/coolant · workload/job data · infrastructure (CRAC, PSU) · weather · GPU utilisation *(only if GPU power is also present)*

### Baselines — MANDATORY (4)
- **M0** Linear regression — sanity floor; may win outright on steady-state-dominated observational data
- **M1** First-order RC
- **M3** N4SID subspace ID (MIMO) — **hardest baseline; near-optimal for a linear plant**
- **M4** Nonlinear grey-box RC (+ leakage term, + `h(fan)` gain scheduling) — **the physics-informed model that needs no neural network**

**OPTIONAL:** M2 Foster/Cauer *(demoted — see §5)* · Kalman on M3 · XGBoost as a **fit ceiling**, explicitly not a physical model

### Physics constraints
Energy conservation · lumped thermal ODE `C·dT/dt = P − (T−T_c)/R` · **Newton cooling with measured `h(fan)` and coolant temperature (strongest constraint available)** · thermal bounds · piecewise-monotone `Rth` · CMOS power model *(gated on voltage availability)*
**REMOVED:** spatial PDEs · Fourier heat equation · per-core diffusion — M100 has no spatial coordinates.

### Metrics
RMSE · MAE · R² · parameter estimates **with bootstrap CIs** · **cross-node held-out RMSE** · **energy-balance residual in watts** · fit time · inference time · parameter count

### Roadmap
V1 Fleet-Scale Thermal Characterisation *(now)* → V2 Cooling Intelligence → V3 PINNs *(gated)* → V4 Digital Twins → V5 Safe Operating Regions.
**Only V1 is being built.**

---

## 4. PHASE-6 REMOVALS — APPLY BEFORE CODING

| # | Remove | Why |
|---|---|---|
| 1 | **PINNs, entirely, from V1** | M100 has no spatial coordinates → no PDE → no PINN in the technical sense. Anything built would be M4 with extra steps and less interpretability. Frees Week 7 to cover the Week-1 overrun. **Delete `PINNs/` from the repo structure.** |
| 2 | **"Thermal Intelligence"** (all 3 occurrences) | Undefined, unmeasurable, unfalsifiable. Last fragment of the dead "Processor Intelligence Framework" framing. Rename V1 to **Fleet-Scale Thermal Characterization**. |
| 3 | **GPU utilisation from MANDATORY inputs** | Nothing in the physics or objectives requires it. Without GPU power it is a confounder, not an input. Demote to optional. |
| 4 | **"Physics consistency" as a bare metric** | Undefined. Replace with **energy-balance residual, in watts**. |
| 5 | **"Generalization capability" as a bare metric** | Not a metric. Replace with **cross-node held-out RMSE** (fit nodes A, test nodes B). |
| 6 | **M2 Foster/Cauer → optional** | JESD51-14 structure functions require a **clean, known, step-shaped power input**. M100 is uncontrolled production telemetry. Fitting a ladder to it yields numerically-fit, physically-meaningless rungs. **Never claim JESD51-14 compliance on non-JESD51-14 data.** Keep only for natural quasi-steps (job start/end) and call it "step-like transient fitting." |

---

## 5. PHYSICS ERRORS TO FIX BEFORE WRITING

**1. CMOS power model is not identifiable as written.**
`P = α·C·V²·f + P_leak(T)` contains **V**, which is not in the confirmed channel list. On POWER9 the OCC sets voltage — exposure unverified. Without `V` you cannot separate `V²f` from `f` (DVFS moves them together).
→ Verify voltage exists, or drop to `P ≈ a·f·u + b` and state the limitation. **Never write an equation containing a symbol you do not have.**

**2. Leakage feedback is probably undetectable here.**
The 38%-leakage-variation evidence is for **consumer junction temperatures (65–110 °C)**. Liquid-cooled HPC nodes run in a narrow, actively-regulated band. If node temperature spans only ~15 °C, the nonlinearity is buried in noise and M4's leakage term is unidentifiable — collapsing M4 toward M1.
→ **Test the actual temperature range in Week 3 EDA before building M4 around leakage.**

**3. Monotonicity as stated is FALSE for this dataset.**
`Rth` is **not** monotone over 934 days — **maintenance resets it** (repaste, clean, replace). M100 has **no maintenance logs** (Nagios data largely removed by anonymisation).
→ Enforcing monotone `Rth` will **hide the very events that would validate degradation detection.**
→ Restate as: *"`Rth` is piecewise non-decreasing between unobserved maintenance events"* and **detect the changepoints** instead of forbidding them.

**4. Mandatory limitation statement.**
Without maintenance records, an `Rth` step is **uninterpretable** — fouling vs. hardware swap vs. sensor recalibration are indistinguishable. You may report *that* it changed and *when*. Never *why*.

---

## 6. CORRECTED TIMELINE

Removing PINNs exactly funds the data-engineering overrun. This is the argument for cutting them.

| Week | Work |
|---|---|
| **0 (Days 1–2)** | **GATE SPRINT.** GATE A, GATE B, sensor/channel identification, prior-work sweep. Nothing else. |
| **1–2** | Dataset pipeline — download, schema discovery, unit reconciliation |
| **3** | Preprocessing — resampling, alignment, gap handling, node filtering |
| **3–4** | EDA — **including the temperature-range / leakage-identifiability check** |
| **5** | Baselines M0, M1, M3 |
| **6** | Physics model M4 (the hard one) |
| **7** | Experiments *(was: PINNs — removed)* |
| **8** | Evaluation |
| **9** | Analysis |
| **10** | Paper |

### Hidden risks, ranked by likelihood of costing a week

1. **Schema drift across 934 days.** Metrics were added mid-campaign by changing plugin behaviour — column names, units, and availability are **not constant**. This is the main landmine.
2. **Download + disk.** ~372 GB compressed across 12–13 records. Plan 100+ GB working set, 20 GB scratch.
3. **16 GB RAM.** Use `pyarrow` dataset API or `polars` streaming. **Loading a record into pandas will OOM.**
4. **Wrong sensor** (board/inlet instead of die) → junction `Rth` never identifiable.
5. **Wrong power channel** → identified `Rth` is a mixture.
6. **N4SID × 980 nodes.** Fit per node, not pooled. Automate and parallelise or it will not finish.
7. **Prior work.** Not ruled out.

---

## 7. REJECTION vs. ACCEPTANCE

**Top rejection risks:** GATE A fails and `Cth` is claimed anyway · GATE B fails and longitudinal is fabricated · prior work exists · **causal verbs applied to observational data** · no instrument validation (unfixable — must be stated) · no maintenance records · wrong sensor · weak/token baselines · undefined terms reaching the manuscript · POWER9 findings presented as general.

**Top acceptance strengths:** 980 nodes vs. the 1–8 typical of this literature · 934 days vs. hours · **measured boundary conditions (fan + coolant + CRAC) — nearly unique** · correct baselines (N4SID + grey-box, usually omitted) · genuinely available physics · **publishable either way** · fully reproducible (CC-BY-4.0, permanent DOIs, zero hardware) · honest limitations · real industrial relevance · falsifiable claims with CIs.

---

## 8. TWO STANDING PRINCIPLES

**If RC beats everything → PUBLISH.**
Heat conduction with constant properties is **linear**; an RC network is its exact spatial discretisation. N4SID is near-optimal for linear plants with 50 years of theory behind it. **RC winning is the physically expected outcome.** The chip-thermal ML literature is saturated with papers claiming neural wins that never benchmark against properly-identified classical baselines. A rigorous demonstration that classical methods match or beat learned models on production telemetry is **more valuable to the field than a 13th neural variant.** Frame the title as a question so both outcomes are the paper's fulfilment.

**If PINNs are absent → the paper is unaffected.**
PINNs were never the contribution. Every deliverable — fleet `Rth` distribution, cooling characterisation, model benchmark, longitudinal drift — exists regardless. That is what "conditionally locked" meant, and the design honours it.

---

## 9. REPOSITORY (9 directories — `PINNs/` removed)

```
GLASSCHIP/
├── datasets/          # Zenodo download + integrity checks
├── preprocessing/     # resample, align, gap-fill, node filter
├── experiments/       # run configs
├── baselines/         # M0 linear, M1 RC, M3 N4SID, M4 grey-box
├── physics_models/    # constraint formulations
├── evaluation/        # metrics, protocols, bootstrap CIs
├── results/
├── visualizations/
└── paper/
```

**Carry over from the Phase-4 design (still applies):**
- `models/base.py` interface: `fit()` / `predict()` / `parameters()` (with CIs) / `cost()`. Every model implements it. A future PINN implements the same interface with **zero changes to the evaluation harness.**
- **Freeze and publish evaluation splits as JSON.** Any future model must be evaluated on identical splits or comparison is worthless. Highest-leverage future-proofing act available.
- Store **raw counters** alongside derived values. Keep **continuous time as an explicit column**, never an implicit index.
- CI check: **`import torch` anywhere in V1 = scope violation.**

---

## 10. OBSOLETE FILES

`01_Project_Overview.md` … `08_Final_Conclusion.md` describe the **dead battery-SOH project** (Phase 0). They are historical only. **Do not use them as a specification.** Archive or delete.

---

## 11. NEXT ACTION

**Run the GATE SPRINT. Two days. Nothing else.**

1. `pip install pyarrow polars` — download one Zenodo record
2. Compute median inter-sample interval for node temperature and CPU power → **GATE A**
3. Download a second record from a different period; check node ID stability → **GATE B**
4. Enumerate available temperature sensors and power channels; check for voltage
5. Two hours: Scholar + Semantic Scholar sweep for prior thermal-model identification on M100/Marconi100

**Then apply §4 removals, fix §5 physics, and execute §6.**

Verdict from Phase 6: **C — remove ~30% and build.** The design is sound, the dataset is exceptional, the physics is genuinely available, the baselines are correct, and the contribution is publishable under every outcome. Nothing warrants redesign.

---

## 12. THE ONE-WAY DOOR

Planning is closed. Not permitted: new datasets · new objectives · new architectures · new directions · "can we make it more novel."

Permitted: *How do we preprocess this?* · *Which baseline first?* · *Why is this experiment failing?* · *How should this constraint be formulated?* · *Does the physics term improve results?*

**Answer the two gates. Then build.**
