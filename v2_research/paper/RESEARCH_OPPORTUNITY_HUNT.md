# RESEARCH OPPORTUNITY HUNT
## Physics-informed scientific ML for processors and compute nodes

Audit date: 2026-08-23. Discovery audit only. No repository modification, no implementation,
nothing committed. Feasibility numbers below come from reading local public data and are
**not validated results**.

---

## 1. Research landscape

Live search, 2018–2026, conceptual rather than keyword-driven. Four findings shape everything
that follows.

**1.1 Chip thermal surrogate / operator learning is saturated.** DeepOHeat (DAC 2023,
arXiv:2302.12949), Enhanced Operator Learning for 3D-IC (ASP-DAC 2025), DeepOHeat-v1
(arXiv:2504.03955, KAN trunk networks, 70.6× optimization speedup). A strong group with an
active follow-up line owns physics-aware operator learning for 3D-IC thermal fields. A student
without floorplan data or an EDA flow cannot compete here. **Categories G and H are closed.**

**1.2 Multicore thermal coupling modelling is old and established.** Matrix Model, predictive
DTM, dedicated thermal emulators — largely 2010–2014 architecture work. Estimating a coupling
matrix is not a new idea.

**1.3 Process-variation-aware thermal modelling exists — but only in simulation.** VarSim
(arXiv:2307.12119) models process variation thermally using Green's functions. The literature
states plainly that variability "results in variation in core characteristics and different
heating properties even between adjacent cores." This is *predicted and simulated*, not
measured at scale.

**1.4 And here is the load-bearing finding.** The HotSpot validation literature states that
researchers built an independent FEM model in Floworks "since there exists no infrastructure
for making such measurements... direct per-block temperature measurements on actual
microprocessors were not readily available," and warns that "a model that matches a thermal
test vehicle under constant heating can still fail under realistic workload phasing, memory
traffic, or heterogeneous compute behavior."

**The entire compact-thermal-model stack — and the SciML surrogates now built on top of it — is
validated against simulation and a single test chip under constant heating.** The data the
field says it lacks now exists publicly. That is the landscape-level opportunity.

---

## 2. Major unsolved problem areas

| Area | Matters? | Public data? | SciML role? | Verdict |
|---|---|---|---|---|
| Chip thermal field surrogates | Yes | Needs floorplans (not public) | Saturated | **Closed** (1.1) |
| Inter-core coupling matrix ID | Moderate | Partial | Constraint-driven | Underdetermined (see 4.F1) |
| **GPU die ↔ HBM thermal coupling** | **Yes, acutely** | **Yes — verified** | **Yes** | **Open** |
| Leakage–temperature feedback | Yes | Partial | Genuine (nonlinear) | Separability risk |
| Cross-architecture transfer | Moderate | Yes | Moderate | Confounded |
| HPC anomaly detection | Yes | Yes + Nagios labels | Weak | **Taken** by dataset owners (RUAD, FGCS 2023) |
| Aging / electromigration | Yes | No public labelled data | n/a | **Blocked** |
| Thermal-aware control / DVFS | Yes | Needs a live system | n/a | **Blocked** |

---

## 3. Dataset opportunities (verified by direct inspection, not assumed)

### 3.1 Summit per-component power and thermal — the asset

Public (OSTI/OLCF, CC-BY), 10 s and 1 min means, 4,626 nodes, 71 variables. Local derived
tables inspected directly (`v2_research/summit/derived/cleaned/`, 33 columns, 1.19 M rows/host):

| Signal | Range | Resolution | Coverage |
|---|---|---|---|
| `p0_gpu{0,1,2}_power`, `p1_gpu{0,1,2}_power` | 17–400 W | **float, 21,243 unique values** | 99.997% |
| `gpu{0..5}_core_temp` | 25.0–60.2 °C | **float, 4,079 unique values** | 99.997% |
| `gpu{0..5}_mem_temp` (HBM2) | 23.0–55.0 °C | **float, 5,254 unique values** | 99.996% |
| `p0_power`, `p0_core_temp_{mean,min,max}` | 14–259 W | float | 99.997% |

Correlations on one node: GPU power↔core temp 0.942, power↔mem temp 0.918, core↔mem temp 0.958.

**The critical property: per-GPU power is measured.** The GPU subsystem has a measured *input*
and two measured *thermal states*, at higher resolution than the CPU subsystem the existing
project used. **6 GPUs × 4,626 nodes = 27,756 production V100s.**

### 3.2 M100 ExaData — rich, but with one fatal gap for GPUs

Public (Scientific Data 10:288, CC-BY), 980 nodes, 934 days, 1.2 GB local for 21-03. Verified
metric inventory: **24 per-core temperatures per socket × 2 sockets** (`p0_core0..23_temp`),
16 DIMM temps, 8 fan speeds, `ambient` (float32, 20 s), `p0_vdd_temp`, `p0_{io,mem}_power`,
`p0_power`, GPU core/mem temps for cards 0/1/3/4, PSU rails, plus Ganglia at 60/90 s.

**Verified blocker:** `gv100card0` (per-GPU power) is **identically zero** — min = median =
max = 0 across 10.7 M rows, one unique value. **M100 has no usable per-GPU power.**
Per-core CPU power is also absent (socket-level only).

Consequence: M100 is a strong *secondary* dataset (temperatures, ambient, fans, 934-day span)
but cannot support GPU inverse identification on its own. **Checking this before recommending
a project changed the winner.**

### 3.3 Labelled anomalies
Zenodo 7541722 — M100 with Nagios anomaly labels, CC-BY, but **15-minute aggregation**, which
destroys thermal dynamics on a system with τ in the hundreds of seconds. Wrong timescale, and
the problem is already owned by the dataset authors' own group.

---

## 4. Five finalists

### F1 — Core-to-core and chip-to-chip thermal variability on real silicon (M100, 48 sensors × 980 chips)
Physics-constrained inference of per-core thermal parameters from shared socket power.
**Novelty 62 · Impact 60 · Feasibility 45 · Publication 58 · Overall 56.**
*Why it could fail — and does:* per-core power is not measured, so the input to a 24-core
system is rank-1. The core-to-core causal coupling matrix is **not identifiable**, only each
core's response to a common input. Physics constraints narrow but do not close this gap.
Closest prior art: VarSim (simulation), and *Fine-Grained Clustering-Based Power Identification
for Multicores* (arXiv:2410.21261) — **STRONG PARTIAL OVERLAP** on the per-core power inference
step. Also exposed to "this is your previous fleet-heterogeneity paper at finer granularity."
**ELIMINATED** — underdetermined, and overlapping.

### F2 — GPU die ↔ HBM thermal coupling identified at fleet scale from production telemetry ⭐
**Novelty 68 · Impact 76 · Feasibility 88 · Publication 76 · Overall 78. SURVIVED.**
See §6.

### F3 — Sim-to-real validation of compact thermal models / SciML surrogates
Conceptually the sharpest gap (§1.4), but building a HotSpot model of POWER9 or GV100 requires
a die floorplan, which is **not public**. **ELIMINATED — blocked on non-public data.**
Its *spirit* survives inside F2.

### F4 — Leakage–temperature positive feedback as a learned residual (UDE)
Physics genuinely nonlinear, so a hybrid earns its place. But leakage cannot be separated from
dynamic power without per-core activity, and idle-period natural experiments give weak
excitation. **Novelty 60 · Impact 55 · Feasibility 40 · Overall 51. ELIMINATED as a standalone
project** — retained as a *component* of F2 (the nonlinear residual stage).

### F5 — Physics-informed cooling-degradation detection on M100 (934-day span, Nagios labels)
**ELIMINATED.** Owned by the dataset authors (Molan et al., RUAD, FGCS 2023); labels are at
15-minute aggregation; labels are availability alerts, not thermal-physics events.

---

## 5. Three-researcher debate

**Dreamer.** HBM thermal is the binding constraint on AI accelerators — imec's IEDM 2025 study
shows 3D HBM-on-GPU peaking at 141.7 °C. Every number in that literature comes from simulation.
Measure the die→HBM coupling on 27,756 real GPUs, publish the first empirical distribution of a
parameter the whole field assumes, then extend to a thermal digital twin for AI datacenters.

**Practical Researcher.** Drop the digital twin. Keep the measurement and the identification.
The data is on disk, the loader and fit harness already exist, and a two-node RC is six
parameters — this is a prototype in hours, not weeks. But three constraints are real: 10 s
sampling may alias the die's fastest thermal mode; power and temperature correlate at 0.94, so
conditioning must be checked; and Summit has no coolant inlet temperature, so the sink term is
a fitted constant. State all three, do not hide them. Also: this is a **new** project — it does
not replace submitting the finished GLASSCHIP paper, it follows it.

**Reviewer from Hell.** "Why is this not another PINN paper?" — there is no PINN, and with both
states and the input measured there is no latent state for one to recover. "Why does the physics
matter?" — because a black-box fit gives no R and C, cannot be checked for thermodynamic
admissibility, and cannot be compared across devices. "What if a black-box model predicts
better?" — it probably will, marginally, and that is fine: the deliverable is *identified
physical parameters and their fleet distribution*, not a leaderboard. "Two-node RC is trivial
physics." — correct; the contribution is the measurement at a scale nobody has had, not the
model. "How do you know 10 s doesn't destroy the coupling dynamics?" — **that is the sharpest
attack**, and it must be answered head-on with an explicit resolvability analysis, which is
precisely the expertise this project already has.

**Convergence.** All three accept F2 provided it is framed as a *measurement and identification*
study whose contribution is an empirical distribution of physical parameters, with the
mechanistic model first and any learned component second and optional.

---

## 6. Winning project

### Title
**Measured, Not Simulated: Die-to-Memory Thermal Coupling Across 27,756 Production GPUs**

### Research question
> What is the thermal coupling between a GPU die and its stacked HBM memory on real deployed
> hardware under real workloads, how much does it vary from device to device, and does a
> two-node physical model identified from telemetry hold across a fleet?

### Hypothesis
The die→HBM coupling conductance is identifiable from public 10 s telemetry; its fleet
distribution is materially wider than the single nominal value the simulation literature
assumes; and a two-node physically-constrained model out-predicts a one-node model
out-of-sample while remaining thermodynamically admissible.

### Physics — explained plainly first
> The GPU chip makes heat. Some of it flows out into the cooling water. Some flows sideways
> into the memory stacks sitting right next to it on the same package. The memory also loses
> heat to the water. Two connected buckets of heat, one filled by the chip's power.

Then the equations — a two-node lumped RC network:

    C_c · dT_c/dt = P − (T_c − T_m)/R_cm − (T_c − T_sink)/R_c
    C_m · dT_m/dt =     (T_c − T_m)/R_cm − (T_m − T_sink)/R_m

Six unknowns (C_c, C_m, R_cm, R_c, R_m, T_sink), two measured states (T_c, T_m), one measured
input (P). **Physics difficulty: MODERATE.** Every term is conservation of energy plus
Newton's law of cooling. Nothing requires more than one afternoon to understand.

Physical admissibility gives free, hard constraints a black-box fit cannot satisfy: all R > 0,
all C > 0, reciprocity of R_cm, and a fitted T_sink that must land near Summit's known
medium-temperature coolant (low-20s °C). Fits violating these are rejected — a genuine
falsification test, not a regularizer.

### Method — and why it is *not* a PINN
**Physics-constrained state-space identification** (structured, positivity-parameterized,
differentiable), fitted per GPU. PINNs are rejected on three independent grounds: the field is
saturated (§1.1); both states and the input are measured, so there is no latent-state recovery
problem for a PINN to solve; and the project's own prior PINN attempt underperformed a
gradient-boosted tree in all conditions.

**Stage 2, conditional:** if the linear model fails *systematically* at high power — the
expected signature of leakage feedback and cooling-control nonlinearity — add a small learned
residual term in the UDE sense (Rackauckas et al.; closest recent work arXiv:2607.15180).
**Only if a structured failure is demonstrated first.** This keeps the ML honest: it enters to
represent an unknown *function*, never an unknown *parameter*.

### Dataset
Summit per-component power and thermal, OSTI/OLCF DOI 10.13139/OLCF/1861393, CC-BY-4.0.
Companion: github.com/at-aaims/summit_power_and_thermal_data. Already local (12 GB derived).
M100 ExaData (Scientific Data 10:288) as a temperature-only secondary — **no per-GPU power**.

### Baselines
(1) One-node RC on core temperature alone — the model the existing literature effectively uses.
(2) Unconstrained linear state-space (no physics constraints).
(3) Gradient-boosted trees / LSTM — black-box reference.
(4) Independent per-state fits ignoring coupling.

### Experiment
Identify the two-node model per GPU across a large sample of the 27,756 devices. Report:
out-of-sample multi-step prediction error vs all four baselines; the fleet distribution of
R_cm, C_c, C_m; the physical-admissibility rejection rate; agreement of fitted T_sink with the
known coolant temperature; and a resolvability analysis bounding what 10 s sampling can and
cannot identify.

### Evaluation metrics
Out-of-sample multi-step RMSE on both states; admissibility rate; parameter dispersion across
the fleet (IQR, and rank stability across time windows); fitted-T_sink error against known
coolant; and identifiability diagnostics (Fisher information / profile likelihood, conditioning
under the 0.94 power–temperature correlation).

### Failure condition — stated in advance
The hypothesis is falsified if **any** of: the two-node model does not beat the one-node model
out-of-sample; R_cm is not identifiable (profile likelihood flat, or CI spanning an order of
magnitude); the admissibility rejection rate exceeds ~50%, indicating the RC structure does not
describe this package; or fitted T_sink lands far from the known coolant temperature. Each is a
clean, publishable negative.

### Exact novelty sentence
> *We report the first measurement-based identification of GPU die-to-HBM thermal coupling on a
> fleet of production GPUs, and the first empirical distribution of that coupling across tens of
> thousands of nominally identical devices under real workloads.*

### Prior art
| Work | Class |
|---|---|
| imec 3D HBM-on-GPU thermal STCO, IEDM 2025 | **RELATED — simulation only.** Establishes the problem matters; supplies no measurements. |
| DeepOHeat / DeepOHeat-v1 / ASP-DAC 2025 | DIFFERENT PROBLEM — surrogate for design-time field simulation, not measurement-based identification. |
| Ellis/Shin et al., SC'21 (10.1145/3458817.3476188) | **STRONG PARTIAL OVERLAP — must cite.** Characterises Summit power/thermal descriptively at fleet scale; does **not** identify thermal models or coupling. This is the paper that most needs a clear distinction. |
| VarSim (arXiv:2307.12119) | RELATED — process-variation thermal modelling, simulation. Predicts the variation this project would measure. |
| HotSpot line (Skadron et al.) | SUPPORTING — the compact-model tradition being tested, and the source of the "no measurement infrastructure" admission. |
| Multicore Matrix Model / predictive DTM (2010–2014) | SUPPORTING — establishes coupling matters; single platforms, CPU, mostly emulated. |
| Wattchmen (arXiv:2603.26435) | DIFFERENT PROBLEM — GPU *energy* modelling, not thermal identification. |

**No direct overlap found.** Could a reviewer say it has been done? They can say GPU thermal
modelling exists (true) and that two-node RC is textbook (true). Neither claim touches the
contribution, which is the *fleet-scale measured distribution of a parameter previously only
simulated*.

### Feasibility — **PROTOTYPE TODAY**
Data acquisition: **0 h** (local). Preprocessing: ~2 h (reuse the frozen pipeline; select GPU
columns). Physics implementation: ~3 h (six-parameter two-node discretisation). Model
implementation: ~3 h. Training: minutes per GPU, embarrassingly parallel. Evaluation and
figures: ~1 day. **Minimum viable experiment:** one node, one GPU, fit two-node vs one-node,
compare out-of-sample multi-step error. **Minimum viable figure:** measured vs predicted T_core
and T_mem over a held-out window, with the one-node model visibly failing on T_mem.

Reusable from the existing project: loader, segmentation, gap handling, chronological OOS
protocol, moving-block bootstrap, validation pipeline, figure harness. Realistically **~70%
of the toolchain**.

### Scores
Novelty **68** · Scientific impact **76** · Feasibility **88** · Publication potential **76** ·
**Overall 78.**

---

## 7. Finished-product vision

Not "we trained a neural network." The deliverable is **an empirically measured physical
parameter distribution that the field currently only simulates**, plus the means to reproduce
and extend it:

1. **A scientific finding** — the fleet distribution of die↔HBM thermal coupling on real
   silicon, with admissibility statistics and identifiability bounds.
2. **A derived dataset** — per-GPU identified thermal parameters for tens of thousands of
   production GPUs, publishable as a small CC-BY table. This is the artifact others will
   actually reuse: it is a *calibration prior* for anyone building a GPU thermal model.
3. **A reproducible identification pipeline** — public data in, physical parameters plus
   admissibility verdict out.

The second item is the one that earns citations. A simulation-based thermal study currently has
no measured prior for R_cm; this would supply one.

---

## 8. Publication strategy

| Venue | Fit | Notes |
|---|---|---|
| **IPDPS 2027 — Measurements, Modeling, and Experiments** | **Strong** — the track explicitly covers measurement, modelling, experiments, energy/power | Abstract 1 Oct, paper 8 Oct 2026, double-anonymous, 10 pp. **Very tight for a greenfield project.** |
| **CCGrid 2027** | Strong | Abstract 24 Nov, paper 1 Dec 2026. **Realistic primary target.** |
| **ICPE 2027** (ACM/SPEC) | Good — measurement and performance modelling; HPC thermal work has appeared there | **2027 deadline not announced at audit time.** Verify. |
| HPC-ODA / HPCMASPA 2027 | Good, low bar | ~11 months out. |
| **FGCS / JPDC** | Good | Rolling. Safe landing. |
| IEEE TPDS | Possible after a strong conference version | Rolling. |
| SC / HPDC / ICS / DAC | **No** — DAC wants design-time methods; SC/HPDC want systems contributions | — |
| SciML venues | **No** — the contribution is measurement, not method | — |

**Sequencing matters more than venue choice.** The existing GLASSCHIP paper is finished and
journal-submittable *now*. This is a new project. Submit GLASSCHIP to FGCS or JPDC on its own
schedule, and run this as the next project targeting CCGrid 2027. Do not sacrifice a finished
paper to a six-week greenfield sprint at IPDPS.

---

## 9. First prototype

**Build today, in this order:**
1. Extract `p0_gpu0_power`, `gpu0_core_temp`, `gpu0_mem_temp` for one host, within segments.
2. Fit the one-node RC on `gpu0_core_temp` alone (baseline).
3. Fit the two-node model; check R > 0, C > 0, and whether fitted T_sink lands near ~21 °C.
4. Compare multi-step out-of-sample error on **T_mem** — this is where the one-node model
   should fail visibly, and it is the whole thesis in one plot.

**Do not build:** a PINN; a neural operator; a thermal surrogate; a digital twin; a benchmark;
a leaderboard; anything requiring a die floorplan; anything on M100 GPU power (it is zero);
per-core CPU power inference (underdetermined).

---

## 10. Final GO / NO-GO

**GREEN.** The problem matters independently of the method — HBM thermal coupling is the
binding constraint on current AI accelerators, and every published number for it comes from
simulation. The data is public, already local, and verified sufficient: per-GPU power plus two
measured thermal states at float resolution across 27,756 production GPUs. The physics is a
two-node energy balance explainable in four sentences. The inverse problem is well-posed. Every
outcome, including failure, is publishable. A meaningful prototype is hours away, and roughly
70% of the required toolchain already exists.

The honest risks are three and all are stateable rather than fatal: 10 s sampling may not
resolve the die's fastest mode (bound it explicitly); power–temperature collinearity at 0.94
threatens conditioning (report identifiability diagnostics); and Summit provides no coolant
inlet temperature (fit it, then check it against the known value — which converts a limitation
into a validation).

| | /100 |
|---|---|
| Novelty | 68 |
| Impact | 76 |
| Feasibility | 88 |
| Publication potential | 76 |
| **Overall** | **78** |

### One-sentence research identity
An empirical, measurement-based identification study of GPU die-to-memory thermal coupling
across a fleet of production GPUs, using physically-constrained state-space identification to
turn public supercomputer telemetry into measured thermal parameters the field currently only
simulates.

### Three-sentence elevator pitch
Thermal coupling between a GPU die and its stacked HBM memory is now a binding constraint on AI
accelerator design, yet every published value for it comes from simulation, because per-device
thermal measurements on real hardware have not been available. Summit's public dataset contains
per-GPU power together with both die and memory temperatures for 27,756 production V100s
running real workloads — enough to identify a two-node physical thermal model per device. We
report the first measured fleet distribution of die-to-memory thermal coupling, how far it
varies between nominally identical devices, and how often the standard RC description is
physically inadmissible on real silicon.

### Five contributions
1. First measurement-based identification of GPU die↔HBM thermal coupling on production hardware.
2. The empirical fleet distribution of R_cm, C_c and C_m across tens of thousands of nominally
   identical GPUs — a measured prior where the literature has only simulated point values.
3. A physical-admissibility test (R, C > 0; fitted sink temperature vs known coolant) that
   rejects fits a purely statistical criterion accepts.
4. A resolvability analysis bounding which thermal modes 10 s telemetry can and cannot identify.
5. A reproducible pipeline and a released per-GPU parameter table, both from public CC-BY data.

### What not to build
No PINN. No neural operator. No surrogate. No digital twin. No benchmark. Nothing needing a
floorplan. Nothing depending on M100 per-GPU power. And do not shelve the finished GLASSCHIP
paper to chase this — submit that one, then start this.

---

FINAL DECISION:
GREEN

WINNING PROJECT:
Measured, Not Simulated: Die-to-Memory Thermal Coupling Across 27,756 Production GPUs

METHOD:
Physically-constrained two-node RC state-space identification from measured per-GPU power and dual temperature states, with an optional UDE-style learned residual only if the linear model shows structured high-power failure. Explicitly not a PINN.

NOVELTY:
68/100

IMPACT:
76/100

FEASIBILITY:
88/100

PUBLICATION POTENTIAL:
76/100

ONE THING TO BUILD FIRST:
On a single Summit host, fit the one-node RC to gpu0_core_temp and the two-node RC to (gpu0_core_temp, gpu0_mem_temp) driven by measured p0_gpu0_power, then plot held-out multi-step predictions of the HBM memory temperature under both — the one-node model should fail visibly on T_mem, and that single figure is the entire thesis.
