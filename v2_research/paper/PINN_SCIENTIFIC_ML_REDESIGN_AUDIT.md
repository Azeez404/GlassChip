# PINN / SCIENTIFIC-ML REDESIGN AUDIT

Audit date: 2026-08-23. Redesign and novelty-discovery audit only. No manuscript, figure,
table, Phase 2/3 artifact, `src/`, or `tests/` modification; no implementation; nothing
committed. Numbers computed below come from reading locked artifacts to test feasibility and
are **not validated results** — anything used in the paper must go through
`paper_analysis/validate_results.py`.

## Headline

**Do not add a PINN.** The field is saturated, the project's own V1 PINN already failed at
this task, and for a linear first-order model the proposed "measurement-aware inverse problem"
is a solved classical estimation problem that the manuscript already cites.

**But the audit found something better, and it is free.** The physical parameters R, C and an
inferred ambient temperature are recoverable from ARX coefficients **already computed and
stored in Phase 2A**, and the recovered ambient is physically plausible against Summit's known
cooling. This grounds the paper in real thermal physics, supplies a parameterization-independent
damage metric, and requires no neural network, no new data, and no new infrastructure.

---

## 1. What the existing research actually exposes

**Data (verified by direct inspection).**

- Summit derived tables: 33 columns per host, 1.19 M rows/host, 116 sockets. Contains
  `p0_power`, `p0_core_temp_{mean,min,max}`, six GPU core temps, six GPU powers, `dt_s`,
  `segment_id`, `n_merged`. **No ambient, no coolant inlet temperature.**
- M100 (`data/raw/21-03/`, 1.2 GB local): IPMI at 20 s — `p0_core0_temp` **int32 (1 °C)**,
  `p0_power` int32, and **`ambient` float32 at 20 s**. Ganglia at ~60 s / ~90 s.
- `src/alignment/`: causal backward as-of matching, per-metric staleness bounds, explicit
  missingness flags, native-interval estimation. Built and tested, targets M100.

**Model.** `T[n+1] = αT[n] + βP[n] + γ`, OLS, frozen across all conditions; τ = −Δt/ln α.

**The physical model this corresponds to.** Discretising the standard lumped first-order
energy balance

    C·dT/dt = P − (T − T_amb)/R

at interval Δt with zero-order-hold power gives exactly the fitted ARX, with

    α = exp(−Δt / RC),   β = R·(1 − α),   γ = (1 − α)·T_amb

**Three ARX coefficients, three physical unknowns.** The mapping is exact and invertible:

    τ = RC = −Δt/ln α        R = β/(1 − α)        C = τ/R        T_amb = γ/(1 − α)

**The project has been computing R, C and T_amb since Phase 2A and discarding two of the
three coefficients.** The manuscript reports only τ. `phase2a_results.json` stores α, β and γ
per unit, and `summit_baseline_counterfactual.py:235` even documents that ambient is
"absorbed in gamma; NOT measured telemetry" — the interpretation was understood and then not
pursued.

**What the recovered physics says** (20 units, Phase 2A coefficients, feasibility computation):

| Quantity | p05 | median | p95 |
|---|---|---|---|
| τ (s) | 274 | 394 | 2277 |
| R (°C/W) | −0.084 | 0.047 | 0.061 |
| C (J/°C) | −19 569 | 6 813 | 91 668 |
| **T_amb inferred (°C)** | **24.4** | **26.0** | **36.9** |

- **100% of units yield an inferred ambient in a physically plausible 5–45 °C; none negative;
  median 26.0 °C.** Summit uses medium-temperature water cooling with inlet in the low 20s °C.
  An effective sink temperature of ~26 °C is the right answer to within a few degrees. This is
  an independent, previously unperformed validation that the RC reading of the fitted model is
  not fiction.
- **10% of units yield R ≤ 0** — a thermodynamically impossible negative thermal resistance,
  with C ranging into large negative values. These fits are statistically unremarkable and
  physically inadmissible.

That last line is the most useful thing in this audit after the ambient check. It is a
**free physics-violation detector**: a binary, parameterization-independent test that flags
fits which OLS is perfectly happy with and physics is not.

**What the F2 anomaly means physically.** For a genuine first-order system τ is invariant to
decimation. The observed 394 s → 910 s shift is therefore direct evidence of **unmodelled fast
dynamics** — at minimum a second thermal mode (die → heat spreader → coolant), which is
exactly what a 2R2C network would represent. F0's τ is a reference regime, not ground truth.

---

## 2. The literature verdict on adding physics-informed ML

Live search, heavy 2022–2026 emphasis, conceptual rather than keyword matching.

| Prior art | Class | Consequence |
|---|---|---|
| **PINNs for building thermal RC modelling and parameter estimation** — *Physics informed neural networks for control oriented thermal modeling of buildings* (Applied Energy 2022; arXiv:2111.12066); *Physics-informed neural networks for building thermal modeling and demand response control* (Building & Environment 2023); *Physically Consistent Neural Networks for building thermal modeling* (Applied Energy 2022) | **DIRECT OVERLAP with concepts A/B/C** | 2R2C + neural network, RC parameter estimation, sub-0.25 °C prediction error, works with partial physics knowledge. Explicitly reported: parameters and inputs estimable "even with certain missing states." A first-order RC + MLP on HPC telemetry is a domain swap of a solved problem. |
| **Quantized-observation state estimation and identification** — Gaussian sum filtering/smoothing for quantized measurements; quantized MMSE filter; Kalman-like particle filter with quantized innovations (PMC8622185 two-filter approach); Wang/Yin/Zhao *System Identification with Quantized Observations* (already cited P6–P8) | **DIRECT OVERLAP with concepts C/J** | The proposed y = Q(T) + ε inverse problem **is** quantized-observation state-space identification. For a linear model it has principled classical solutions with identifiability theory. The literature also documents precisely why naive gradient methods fail here: the observation model is non-differentiable and EKF-style linearisation breaks. A neural network is strictly worse than the classical estimator on a linear model. |
| **PIML for datacenter thermal digital twins** — PIML+MPC for hybrid-cooled datacenters (Applied Energy 2026); PINN-based digital twins for thermal energy systems review (Springer 2026); AI/digital-twin datacenter cooling review 2018–2026 (EPJ ST); physics-informed datacenter twins reporting 0.18 °C median error | **DIRECT OVERLAP with concept H** | Crowded, active, and populated by groups with cooling-plant access, CFD, and control loops. Entering with public telemetry, no control loop, and a first-order model is entering from a position of weakness. |
| **Universal Differential Equations / hybrid mechanistic-neural** — Rackauckas et al. 2020 and the 2024–2026 line (hybrid ODE-NN for incomplete physiological systems, PMC12048883; structured hybrid mechanistic models, arXiv:2602.11350; **RTS Smoother-Guided Learning of Physics-Based Neural Differential Models, arXiv:2607.15180**) | **PARTIAL OVERLAP — closest prior art for the only defensible neural option** | Known RC term + learned residual term, fitted under noisy/irregular observation, is exactly UDE. The 2026 smoother-guided work is very close to a "measurement-aware hybrid identification." The method family is established; applying it to HPC telemetry is a domain application, not a method contribution. |
| UKF/NLS for RC parameter-input estimation with missing states (PMC11798724) | SUPPORTING | Classical alternative that already handles missing states. |
| CMP thermal sensor placement (readings off true max core temp by up to 12.6 °C) | SUPPORTING | Physical justification for the F3 spatial-aggregation axis. |

### The critical-novelty test (§6 of the brief)

| | Already done? |
|---|---|
| A PINN thermal prediction | **Yes**, extensively |
| B PINN thermal system identification | **Yes** (buildings) |
| C PINN thermal parameter estimation | **Yes** (2R2C, Applied Energy / Build. Env.) |
| D PINN with noisy measurements | **Yes** |
| E PINN with sparse measurements | **Yes** |
| F PINN with irregular sampling | **Yes** (neural ODE / latent ODE families) |
| G PINN with sensor degradation | **Partially**; not systematically for thermal ID |
| H PINN for datacenter/HPC thermal | **Yes**, and crowded |
| I Physics-informed reconstruction from quantized telemetry | **Yes in substance** — classical quantized-observation estimation, non-neural |
| J Physics-informed identification modelling the observation operator | **Yes in substance** — this is the definition of quantized-observation state-space ID |
| **K Physics-informed learning to distinguish *physical* from *measurement-induced* heterogeneity across a fleet** | **No direct overlap found.** Confidence: medium-high. |

**K is the only survivor, and note what it is not.** K is a question about a *population* of
units, not about recovering one latent trajectory. Nothing in the PINN or quantized-estimation
literature addresses whether an observation-aware estimator restores the *cross-unit ordering*
that naive identification destroys. That is the gap — and answering it requires an
observation-aware estimator, not a neural network.

---

## 3. Ten candidate concepts, ranked

Common notation: physics C·dT/dt = P − (T − T_amb)/R; observation yᵢ = Hᵢ(T(tᵢ)) + εᵢ with
Hᵢ ∈ {quantize, decimate, max-aggregate, drop}.

| # | Concept | Method | Data sufficient? | Prototype | Novelty | Level | Verdict |
|---|---|---|---|---|---|---|---|
| **1** | **Recover R, C, T_amb from stored α, β, γ; validate inferred ambient; use R ≤ 0 as a physics-violation detector; measure how violation rate rises with degradation** | Algebra on existing coefficients | **Yes — already computed** | **Hours** | Moderate | **3** | **DO — highest ROI in this audit** |
| **2** | **Observation-aware re-identification as a control: refit with an explicit quantization/decimation/aggregation likelihood, test whether fleet rank ordering is recovered** | Dead-zone / Gaussian-sum ML on first-order model, ~150 LOC | **Yes** | **1–3 days** | **Moderate–high** | **3** | **DO — the gap-K experiment** |
| **3** | Validate inferred T_amb against M100's **measured** ambient — a falsification test of the RC reading | Same algebra + M100 loader | Yes (M100 local) | 3–5 days | Moderate–high | 3 | **DO IF TIME** |
| 4 | 2R2C two-mode fit at F0 to test whether a second mode explains the F2 anomaly | Linear, 5-parameter LS | Yes | 2–4 days | Moderate | 3 | Optional, strong for R2 |
| 5 | UDE: known RC term + small learned residual dynamics, fitted under explicit Hᵢ | Neural ODE / UDE | Yes | **2–4 weeks** | Moderate | 3 | **NO — wrong window, and it adds a confound to the central question** |
| 6 | Physics-informed latent-state reconstruction from quantized telemetry | PINN with dead-zone loss | Yes | 1–2 weeks | **Low** | 1 | **NO — V1 already did this** |
| 7 | Neural ODE on irregular M100 multi-rate telemetry | Latent ODE | Yes | 2–3 weeks | Low–moderate | 2 | **NO — method application, not contribution** |
| 8 | Neural operator / DeepONet for thermal response | FNO/DeepONet | No (needs field data) | Months | Low here | 0 | **NO — no spatial field exists** |
| 9 | Bayesian physics-informed identification with uncertainty over R, C | Probabilistic programming | Yes | 1–2 weeks | Moderate | 2 | Defer — the block bootstrap already covers uncertainty |
| 10 | PINN thermal prediction baseline comparison | Existing `src/pinn/` | Yes | Done | **Zero** | **0** | **NO — already run, already failed** |

**Concept 10 is not hypothetical.** `src/pinn/thermal_pinn.py` already implements a
quantization-aware dead-zone data loss (`quant_halfwidth = 0.5 · QUANT_STEP_C`) plus an ODE
residual physics loss — i.e. a simplified version of the very formulation under consideration.
Its out-of-sample R² was **−0.0055 (F0)**, 0.0257 (F1), 0.0110 (F2), 0.0228 (F3), 0.0500 (F4)
— beaten by a gradient-boosted tree in every condition. The project has already run this
experiment and it did not work.

There is a fair counter-argument: V1 applied it to *residual prediction*, a near-null task, not
to *parameter identification under degradation*, which is more tractable. That distinction is
legitimate — and it is exactly what concept 2 tests, without a neural network.

---

## 4. Where the physics genuinely enters, and why no ML is needed

The scientific question the project has converged on is:

> How much of a fleet's apparent thermal heterogeneity is physical, and how much is
> manufactured by the measurement?

Physics enters at three points, all without a neural network:

1. **Interpretation.** α, β, γ → R, C, T_amb. Exact, invertible, already computed.
2. **Validation.** Inferred T_amb ≈ 26 °C against Summit's known low-20s °C water cooling; and
   on M100, against a *measured* ambient channel. A mechanistic model that reproduces an
   independently known physical constant is evidence the fit means something.
3. **Falsification.** R ≤ 0 is thermodynamically impossible. 10% of F0 units already violate it.
   **Does degradation increase that rate?** This is a binary, unit-free, parameterization-independent
   damage measure — and it is immune to the τ-transform critique that the previous audit
   established undermines dispersion claims in τ-space.

ML would be needed if the unknown were a *function* rather than a *parameter*. The F2 anomaly
says the structure is indeed incomplete — but a second RC mode (concept 4) is a five-parameter
linear model, not a neural network. Reaching for a UDE to represent one missing thermal mode is
using a function approximator where a known physical term suffices, and it would inject a
learned component into precisely the quantity — apparent heterogeneity — the paper is trying to
attribute. **It makes the central question harder to answer, not easier.**

---

## 5. Three-persona debate

**Dreamer.** Reframe the whole project as a measurement-aware physics-informed inverse problem:
latent RC state, explicit degradation operator Hᵢ, hybrid neural residual for unmodelled modes,
Bayesian uncertainty over R and C, validated cross-machine. Target a scientific-ML venue.

**Practical Researcher.** The window closes 8 October. A UDE with a non-differentiable
observation operator is 2–4 weeks of research-grade debugging with a real chance of producing
nothing — the classic PINN failure modes all apply here at once: stiff two-timescale dynamics,
loss balancing between data and physics, non-differentiable Q, weak identifiability of R and C
under strong T–P collinearity (0.94–0.98 per unit), and the ever-present risk of a model that
satisfies the physics residual while fitting the wrong dynamics. Meanwhile concepts 1 and 2
deliver most of the scientific value in hours and days respectively. Cut 5–10 entirely.

**Critic.** "Why is this not just another PINN paper?" — because there is no PINN. "Why is the
physics trivial?" — it is first-order, and the paper says so; the contribution is not the
physics but what the physics *detects*. "Why isn't this just system identification?" — it is,
and that is the honest framing; the increment is population-level, not estimator-level. "How do
you know the latent state is real?" — the inferred ambient lands within a few degrees of the
known coolant temperature, which is a genuine external check, and 10% of fits fail it, which
shows the check has teeth. "How do you know R and C are identifiable?" — from three coefficients
and three unknowns, *conditional on the RC structure being correct*, and the F2 anomaly says it
is not exactly correct; that limitation must be stated, not hidden. "What happens under
quantization?" — that is the experiment. "Why should a scientific-ML researcher care?" —
**they shouldn't, and the paper should stop trying to make them.**

**Convergence.** All three accept: keep the measurement-quality identity; add the RC
interpretation and the physics-violation diagnostic (free); add the observation-aware
re-identification control (cheap) because it is the only thing that answers gap K; add nothing
neural; target HPC venues, not ML venues.

---

## 6. The one experiment worth running (concept 2)

**Question.** When coarse telemetry destroys the fleet's apparent rank ordering, is the
information recoverable by an estimator that models the measurement — or is it destroyed?

**Setup.** For each unit and condition, identify the first-order model twice:
- *Naive:* the existing frozen OLS ARX (what practitioners actually do).
- *Observation-aware:* maximum likelihood on the same model with an explicit observation
  operator — a dead-zone likelihood over the quantization bin [y − 0.5, y + 0.5] for F1/F4,
  the decimated sampling interval for F2/F4, and the max-over-cores operator for F3/F4.

**Primary outcome.** Spearman ρ(τ_F0, τ_Fk) across units, naive vs observation-aware.
Secondary: physics-violation rate (fraction with R ≤ 0), inferred-ambient plausibility,
per-unit ratio dispersion.

**Both outcomes are publishable, and the negative one is stronger.**
- *Rank recovers* → the artifact is an estimator failure, it is fixable, and the paper delivers
  a concrete remedy practitioners can adopt.
- *Rank does not recover* → the information about fleet heterogeneity is destroyed by the
  measurement itself, not by the estimator. That converts the paper's thesis from "naive
  identification is biased" into **"coarse telemetry destroys recoverable information about
  fleet heterogeneity"** — a limit result, and a considerably stronger claim.

**Feasibility.** Existing data: YES. Existing code reusable: ~80% (loader, conditions, fit
harness, bootstrap, validation pipeline all reusable). New code: one likelihood function and an
optimiser loop, ~150 LOC. GPU: none. Runtime: minutes to hours on 116 units × 5 conditions.
Minimum viable figure: one panel, ρ per condition, naive vs observation-aware, with bootstrap CIs.

---

## 7. Research-question redesign

**Current.** How does measurement quality affect thermal system identification, and does it
also improve residual predictability?

**Version A — minimal evolution.** Add the RC interpretation, the inferred-ambient validation,
and the physics-violation rate to the existing paper. Novelty +modest, impact +modest,
feasibility **very high (hours)**, risk near zero. Physics grounding at no cost.

**Version B — strong upgrade ✅ RECOMMENDED.** Version A + the 116-unit ablation (from the
previous audit) + concept 2:

> When coarse telemetry distorts a fleet's apparent thermal heterogeneity, how much of that
> distortion is an artifact of the estimator — removable by modelling the measurement — and how
> much is information the measurement has destroyed?

Novelty **high for this venue class**, impact high, feasibility high (~2–3 weeks total), risk
low. Physics is load-bearing, ML is absent, and the "just textbook errors-in-variables" attack
finally has an answer: errors-in-variables predicts attenuation of an estimator; it says nothing
about whether population rank structure is recoverable.

**Version C — ambitious.** Version B + 2R2C model-order test + M100 measured-ambient validation
+ cross-machine sensitivity. Novelty higher, feasibility **marginal for 8 October**, risk
moderate — it consumes the whole window and reintroduces cross-machine confounds. Do only if
Version B is written up by mid-September.

**Chosen: Version B.**

---

## 8. Titles

Only if Version B is adopted, and the scientific identity does change — the paper becomes about
recoverability, not just distortion.

1. *Recoverable or Destroyed? Measurement-Aware Identification of Thermal Dynamics Across 116 Supercomputer Sockets*
2. *Apparent Thermal Heterogeneity: Separating Measurement Artifacts from Hardware Variation Across 116 Supercomputer Sockets* (carried from the previous audit)
3. *What Coarse Telemetry Destroys: Limits of Thermal Model Identification on a Supercomputer Fleet*
4. *Modelling the Meter: Observation-Aware Thermal System Identification Under Degraded HPC Telemetry*
5. *When Physics Rejects the Fit: Physical Admissibility as a Diagnostic for Thermal Identification from Coarse Telemetry*

**Recommend #1** if concept 2 returns a clean answer either way; **#2** if it is ambiguous.
Decide after the run, not before.

---

## 9. Venue impact

| Venue | Does the physics-informed upgrade improve eligibility? |
|---|---|
| **IPDPS 2027 MME** (abstract 1 Oct, paper 8 Oct 2026) | **Yes.** Physical admissibility and observation-aware estimation deepen a measurement-track paper without diluting it. |
| **CCGrid 2027** (1 Dec 2026) | Yes, same. |
| **FGCS / JPDC** | Marginally — already eligible. |
| SC / HPDC / TPDS | No. Novelty still short. |
| **Scientific-ML venues** | **No, and this matters.** With no neural network there is no ML contribution, and with one there would be no novelty. Both branches say the same thing: do not target ML venues. |
| Computational-science venues | No — no new numerics. |

---

## 10. Scores

Strongest surviving formulation = Version B.

| Dimension | /100 | Note |
|---|---|---|
| Scientific novelty | 60 | Gap K is real; the components are individually classical. |
| Practical impact | 70 | A physical-admissibility check and a recoverability answer are directly usable by facilities. |
| Technical depth | 65 | Real estimation theory, real thermodynamic constraint, no hand-waving. |
| **Feasibility** | **88** | Concept 1 is hours; concept 2 is days; no new data, no GPU. |
| Reviewer survivability | 72 | Answers R2 (physics grounding), R5 (not textbook), and R1 (full fleet) at once. |
| Publication potential | 78 | IPDPS MME viable, CCGrid fallback, FGCS floor. |

| Version | Novelty | Impact | Feasibility | Risk |
|---|---|---|---|---|
| Current paper | 38 | 40 | 85 | Low |
| + minor upgrade (prev. audit: 116-unit + per-unit rank) | 62 | 68 | 80 | Low |
| **+ physics-informed version (Version B)** | **68** | **74** | **78** | **Low** |
| PINN / UDE version | 45 | 45 | **35** | **High** |
| Strongest finished product (Version C) | 74 | 80 | 55 | Moderate |

Note the PINN row: it *lowers* novelty relative to doing nothing neural, because it moves the
paper into a saturated field where it is uncompetitive, while cutting feasibility by more than
half.

---

## 11. Final answer

**What the research should become.** A measurement-quality study of thermal system
identification that is grounded in the underlying RC energy balance rather than in a bare
autoregressive coefficient — using that physics to validate the fits (inferred ambient ≈ 26 °C
against known low-20s °C water cooling), to reject them (R ≤ 0 for 10% of units), and to ask the
one question the literature has not answered: when coarse telemetry destroys a fleet's apparent
heterogeneity structure, is that loss an estimator artifact or destroyed information?

**Why it is stronger.** It converts three of the manuscript's weaknesses into strengths: the
discarded β and γ become physical parameters; the τ-parameterization critique is bypassed by a
binary physical-admissibility test; and "this is textbook errors-in-variables" is answered,
because errors-in-variables theory addresses a single estimator, not the recoverability of
population rank structure.

**Where physics enters.** C·dT/dt = P − (T − T_amb)/R, mapped exactly onto the already-fitted
ARX via α = exp(−Δt/RC), β = R(1−α), γ = (1−α)T_amb.

**Why ML is necessary.** **It is not.** That is the audit's finding, and it should be stated in
the paper as a deliberate choice, not an omission.

**Is PINN the best architecture?** No. For a linear first-order model with a known observation
operator, classical quantized-observation estimation is better-founded, better-understood, and
strictly easier to defend. The project's own V1 PINN — which already implements a
quantization-aware dead-zone loss — underperformed a gradient-boosted tree in all five
conditions.

**Exact experiment.** Concept 2 (§6): naive OLS vs observation-aware maximum likelihood on the
same frozen first-order model across 116 units × 5 conditions; primary outcome
ρ_s(τ_F0, τ_Fk) under each estimator.

**Prototypable today.** Concept 1 in full — R, C, T_amb per unit per condition, ambient
plausibility, and the physics-violation rate — from `phase2a_results.json` alone.

**Data reused.** All of it. Summit derived tables, Phase 2A–2E artifacts, the frozen fit
harness, the bootstrap, the validation pipeline. **New data required: none.**

**Novelty.** Gap K: whether observation-aware identification recovers cross-unit rank structure
that naive identification loses under measurement degradation. No direct overlap found.

**Closest prior art.** Wang/Yin/Zhao, *System Identification with Quantized Observations*
(already cited P6); Gaussian-sum and two-filter quantized state estimation; and for the neural
branch, UDEs and arXiv:2607.15180.

**Reviewers will attack.** (a) "If the observation-aware estimator is better, why is your
headline about a naive one?" — answer: because the naive estimator is what practitioners use,
and the paper documents both the practice and its limit. (b) "R and C identifiability rests on
the RC structure, which your own F2 result contradicts." — a real limitation; state it, and let
the 10% violation rate stand as evidence the check is not vacuous. (c) "First-order physics is
trivial." — correct, and the contribution is what the physics detects, not the physics itself.

**Finished product.** An empirical study plus a reproducible artifact: per-unit physical
parameters with an admissibility test, a rank-recoverability result, and two unbranded
diagnostics facilities can apply before comparing nodes. No framework, no benchmark, no tool,
no neural network.

**Venue.** IPDPS 2027 MME (abstract 1 Oct, paper 8 Oct 2026); CCGrid 2027 fallback; FGCS floor.

**Should the project proceed?** Yes — with Version B, and with the PINN retired permanently
rather than resurrected. Priority order: **P0** the 116-unit ablation from the previous audit;
**P1** concept 1 (hours, free); **P2** concept 2 (days); **P3** M100 ambient validation if time
allows. Everything neural is rejected.

---

FINAL DECISION:
ABANDON PINN, USE NEWER SCIENTIFIC-ML PARADIGM

— with the important qualification that the replacement is **physics-constrained,
observation-aware inverse modelling containing no neural network at all**. PINNs are the wrong
tool here: the field is saturated, the physics is linear enough that classical estimation
dominates, and the project's own V1 PINN already failed. The mechanistic RC constraint plus an
explicit measurement operator delivers the scientific value the PINN was supposed to provide,
at a fraction of the cost and with far better reviewer survivability.

HIGHEST-ROI ACTION:
Recover R, C and inferred T_amb from the α, β, γ coefficients already stored in `phase2a_results.json`, report the inferred-ambient validation (~26 °C against Summit's known low-20s °C water cooling), and adopt the physics-violation rate (fraction of units with R ≤ 0; currently 10% at F0) as a parameterization-independent measure of measurement damage across F0–F4.

EXPECTED NOVELTY:
68/100

EXPECTED IMPACT:
74/100

EXPECTED PUBLISHABILITY:
78/100
