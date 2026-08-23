# PINN CHIP RESEARCH OPPORTUNITY HUNT

Clean-room research branch. Created 2026-08-23 in `research_pinn_chip/`, logically independent
of GLASSCHIP: no GLASSCHIP source imported, no previous PINN code reused, no existing artifact
modified, nothing committed. GLASSCHIP is used only as (a) background knowledge and (b) a
pointer to public datasets already on disk.

Numbers below come from reading public data directly to test feasibility. They are **not
validated results**.

---

## 1. Research landscape

Live search, 2018–2026, weighted to 2022–2026. Five findings constrain everything.

**1.1 PINNs for inverse heat conduction are saturated.** E-PINN for space-dependent IHCPs;
physics-informed hierarchical neural operators (PIHNO) mapping discrete temperature
observations to continuous heat sources; temperature-field inversion of heat-source systems;
decomposed physics-based compressive sensing for sparse inverse heat source detection.
Method-level contributions in inverse heat problems are closed to a newcomer.

**1.2 Chip thermal surrogate / operator learning is saturated.** DeepOHeat (DAC 2023,
arXiv:2302.12949), Enhanced Operator Learning for 3D-IC (ASP-DAC 2025), DeepOHeat-v1
(arXiv:2504.03955). Requires floorplans that are not public.

**1.3 PINNs for datacenter/GPU thermal are now actively occupied.** A knowledge-embedded PINN
for GPU-centric datacenter HVAC control (Feb 2026) reporting >30% steady-state temperature
error reduction over vanilla PINN and 10–18% HVAC power savings; a physics-aware framework for
short-term GPU power forecasting in AI datacenters (arXiv:2605.04074); a 2025 review of PINNs
for electronics and battery thermal management. These groups have cooling-plant access and
control loops. **Competing on GPU thermal control or forecasting is not viable.**

**1.4 PINN extrapolation is contested, not established.** The literature documents that "PINNs
often exhibit poor extrapolation performance outside the training domain and are highly
sensitive to the choice of activation functions." There is a dedicated 2025 paper on *improving*
PINN extrapolation via transfer learning (arXiv:2507.12659) and one on *Limitations of PINNs*
(arXiv:2508.21559). The closest positive evidence is from a different device class: a
physics-constrained network reconstructing motor temperature and extrapolating from 23/35 °C
down to −7 °C at 0.64–0.80 °C MAE.

**1.5 Structural problem for PINNs in this domain — stated honestly up front.** Tractable chip
thermal models are *lumped, linear, low-dimensional* ODEs. PINNs earn their keep on nonlinear,
high-dimensional PDEs with scarce data. A two-state linear ODE with 1.19 M samples per node is
close to the worst case for a PINN: classical identification and Kalman-style input estimation
dominate. Any PINN-centered candidate in this domain must therefore find a regime where the
data is genuinely *scarce* and the physics genuinely *nonlinear* — otherwise it is decoration.

**One candidate survives that test, and the survival condition is empirically verified in §11.**

---

## 2. Candidate comparison

| ID | Family | Falsifiable question | PINN genuinely needed? | Verdict |
|---|---|---|---|---|
| **A** | GPU/HBM coupled thermal dynamics | Does a two-node model beat one-node on held-out HBM temperature? | **No** — P, T_core, T_mem all measured; no latent state. Classical state-space ID is strictly better. | **REJECT for PINN.** Strong project, wrong method. |
| **B** | Thermal prediction under telemetry degradation | Does physics recover accuracy lost to quantization/downsampling? | Weak — for a linear model this is classical quantized-observation estimation (Wang/Yin/Zhao; Gaussian-sum filtering). | **REJECT** |
| **C** | Cross-GPU / cross-facility generalization | Does physics transfer where black-box ML does not? | Moderate | Confounded (facility, cooling, workload). **DEMOTE** |
| **D** | Thermal parameter identification | Can R, C be recovered from telemetry? | **No** — three ARX coefficients, three unknowns; closed-form. | **REJECT** |
| **E** | Thermal anomaly prediction | Can physics improve unlabeled anomaly detection? | Moderate | Owned by dataset authors (RUAD, FGCS 2023); labels are 15-min aggregated availability alerts. **REJECT** |
| **F** | **Power → temperature dynamics in the data-scarce hot regime** | **Does a physics-constrained model outperform pure ML where training data is scarce but the model is actually needed?** | **Yes — see §10** | **WINNER** |
| **G** | Missing-sensor reconstruction | Can a held-out core/HBM sensor be predicted from its neighbours? | Moderate | Needs die geometry (POWER9 logical→physical core map is not public). **REJECT — unfalsifiable without layout** |
| **H** | Quantized sensor → latent temperature recovery | Can latent T be recovered from 1 °C data? | **No** — classical, and GLASSCHIP's own quantization-aware PINN already lost to a gradient-boosted tree in all five conditions. | **REJECT** |

### Additional directions brainstormed and discarded
PINN + uncertainty (bootstrap already suffices); PINN + online adaptation (no deployment
target); PINN + fleet learning (buzzword stack without a question); PINN + digital twin (no twin
exists); PINN + reliability/aging (no public labelled degradation data). None had a real
scientific question behind the phrase.

---

## 3. Prior-art stress test

| Work | Class | Bearing on the winner |
|---|---|---|
| Knowledge-embedded PINN for GPU-datacenter HVAC control (Feb 2026) | **STRONG PARTIAL OVERLAP** | Closest live competitor. Targets *control* with facility access; reports gains over vanilla PINN. Does not evaluate whether physics helps in the data-scarce thermal tail, and uses no public fleet data. |
| Physics-aware short-term GPU power forecasting for AI datacenters (arXiv:2605.04074) | RELATED | Forecasting power, not thermal response; different direction of the map. |
| PINNs for electronics/battery thermal management — review (Preprints 2025) | SUPPORTING | Establishes the area is active and reviewed; a review existing means novelty claims must be narrow. |
| E-PINN / PIHNO / inverse heat-source PINNs (2022–2026) | **DIRECT OVERLAP on method** | Any *method* contribution in physics-informed inverse heat problems is taken. The winner must be an *evaluation* contribution, not a method one. |
| DeepOHeat line (DAC 2023 → ASP-DAC 2025 → v1 2025) | DIFFERENT PROBLEM | Design-time field surrogates; needs floorplans. |
| *Limitations of PINNs: Smart Grid Surrogation* (arXiv:2508.21559); *Improving PINN extrapolation via transfer learning* (arXiv:2507.12659) | **SUPPORTING — and load-bearing** | These establish that the extrapolation advantage is an open question, which is exactly what makes evaluating it a legitimate contribution rather than a foregone conclusion. |
| Motor temperature reconstruction with wide-temperature-range physics-constrained NN | **CLOSEST POSITIVE ANALOGUE** | Same question, different device class (electric motor, not processor), lab-scale not fleet-scale. Its existence validates the concept and leaves the chip domain open — but it also means the finding "physics helps extrapolation" would not be surprising. Must be cited and distinguished. |
| PINNs for control-oriented building thermal modelling (Applied Energy 2022; Build. Env. 2023); Physically Consistent NNs (Applied Energy 2022) | PARTIAL OVERLAP | RC + NN hybrids for thermal, buildings. Establishes the architecture; the regime-scarcity question is not their subject. |
| Ellis/Shin et al., SC'21 (10.1145/3458817.3476188) | SUPPORTING — must cite | Descriptive characterisation of Summit power/thermal; no modelling. |

**No direct overlap found** for the winner as an *evaluation* question. **Direct overlap exists**
for any attempt to claim a new physics-informed *method*. The winner must be framed accordingly,
and this constraint is not negotiable.

---

## 4. Three-persona debate

**Dreamer.** Physics-informed thermal models could become the standard way to predict processor
behaviour in regimes too rare or too dangerous to sample — throttling onset, cooling failure,
transient excursions. If physics genuinely rescues the data-poor tail, the same argument applies
to every safety-critical rare-regime prediction problem in systems.
*Currently achievable:* the fleet-scale evaluation on Summit GPUs. *Small extension:* per-device
parameter distributions. *Major extension:* cross-facility transfer. *Speculative:* everything
about deployment, control, or digital twins.

**Practical Researcher.** Drop control, drop deployment, drop the twin. The evaluation is the
project. Data is on disk (12 GB derived Summit), the physics is a two-state linear ODE plus a
learned correction, and the prototype is hours away. But be clear-eyed: this is a *method
evaluation* paper. Its ceiling is lower than the non-PINN GPU identification project already
identified in the previous audit. Do not let this branch displace that one — run the GO/KILL
test first and let the result decide.

**Critic.** "Why is this not another PINN paper?" — because PINN is the object of study, not the
tool; the deliverable is an answer about when physics helps, not a new architecture. "Physics
here is trivial." — correct, and that is a feature: an honest test needs physics simple enough
that the comparison is not confounded by implementation choices. "Your regime split is
arbitrary." — it is not: the split is set by where production hardware actually spends its time,
which is measured, not chosen. "Pure ML will win anyway with 1.19 M samples per node." — in the
bulk, probably yes; the question is the tail. "Then you are testing a straw man." — only if the
tail is uninteresting, and thermal models exist precisely to predict the tail. "If PINN loses,
you have nothing." — wrong; a rigorous negative on a widely-asserted claim, at fleet scale on
real silicon, is publishable and useful.

**Convergence.** All three accept the candidate *conditional on the prototype*. The Critic's
strongest surviving objection — that the result may simply reproduce the known "PINNs
extrapolate poorly" finding — is real and cannot be dismissed in advance. It is the reason the
decision below is INVESTIGATE FURTHER rather than BUILD.

---

## 5. Novelty ranking

| Rank | Candidate | Problem | Method | Experimental | Dataset | Significance | Generalizability | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 1 | **F — physics in the data-scarce thermal regime** | 7 | 3 | 8 | 7 | 6 | 6 | **58/100** |
| 2 | C — cross-facility transfer | 6 | 3 | 6 | 7 | 5 | 6 | 52/100 |
| 3 | A — GPU/HBM coupling (as a PINN project) | 7 | 2 | 5 | 8 | 7 | 5 | 48/100 |
| — | B, D, E, G, H | — | — | — | — | — | — | <40, rejected |

Method novelty is deliberately scored low across the board. In this domain, after §3, it should be.

## 6. Feasibility ranking
1. **F — 88/100.** Data local and verified; two-state ODE; prototype in hours; ~0 new infrastructure.
2. A — 88/100 (but not a PINN project).
3. C — 60/100 (cross-facility confounds; M100 lacks per-GPU power).

## 7. Publication ranking
1. **F — 66/100.** Measurement/evaluation venues; modest but real.
2. A — 76/100 **as a non-PINN identification paper** (see previous audit).
3. C — 50/100.

## 8. Rejected directions

- **B, D, H (quantization / parameter recovery / latent temperature):** the model is linear and
  the classical solutions are better-founded. GLASSCHIP's own quantization-aware PINN already
  lost to a gradient-boosted tree in all five conditions — this is settled empirically, in-house.
- **E (anomaly detection):** owned by the dataset authors; labels at the wrong timescale.
- **G (missing-sensor reconstruction):** requires the POWER9 logical→physical core map, which is
  not public. Without geometry there is no heat equation to inform the network, and no
  falsifiable spatial claim.
- **Operator learning / DeepONet / FNO on chip thermal:** saturated and floorplan-dependent.
- **Anything targeting GPU thermal control:** occupied by groups with facility access.
- **A as a PINN project:** rejected *as a PINN project only*. All states and the input are
  measured, so there is no latent-state problem. It remains the strongest overall project in
  this domain — as classical physics-constrained identification. The previous audit's
  recommendation stands unchanged.

---

## 9. Winning research question

> **On real production GPUs, does embedding a lumped thermal energy balance into a neural model
> improve prediction of temperature in the high-temperature regime — where operational data is
> scarce but thermal models are actually needed — relative to both a purely data-driven model
> and a purely classical RC model trained on the same data?**

**Hypothesis.** In the bulk regime (~33 °C median) a black-box model wins on accuracy and
physics adds nothing. In the sparse hot tail (>55 °C, ~0.2% of samples) the black-box model
degrades sharply while the physics-constrained hybrid degrades gracefully, because the RC
backbone continues to extrapolate where the data ends.

**Failure condition, stated in advance.** Falsified if any of: the hybrid does not beat the
black-box model in the hot tail; the pure classical RC model matches the hybrid (physics alone
suffices, the network is decoration); or the hybrid's advantage disappears once the black-box
baseline is reweighted or resampled toward the tail. **The third is the sharpest self-test and
must be run** — it is the difference between a real finding and an artifact of class imbalance.

---

## 10. Why PINN is genuinely necessary — the three-way distinction

| | Bulk regime (~33 °C, abundant) | Hot tail (>55 °C, ~0.2%) |
|---|---|---|
| **Classical RC** | Adequate; misses nonlinearity | Extrapolates, but cannot represent leakage feedback, fan-control response, or throttling |
| **Pure ML** | **Best** — abundant data | Degrades; almost no training support, and no constraint preventing physically impossible output |
| **Physics-informed hybrid** | Comparable, no advantage | **Hypothesised best** — RC backbone anchors extrapolation, learned term captures nonlinearity where data exists |

**What the PINN does that ordinary ML cannot:** constrain predictions to satisfy an energy
balance where training data is absent, so error grows gracefully rather than arbitrarily.
**What it does that classical physics cannot:** represent the temperature-dependent
nonlinearities — leakage feedback, cooling-control response, throttling — that a linear RC model
structurally cannot express.

Neither advantage is assumed. Both are measured against the other two arms. **The comparison is
the contribution**, and §1.4 establishes that the answer is genuinely open.

**The condition that makes this a legitimate PINN problem is verified, not asserted** (§11): the
regime of interest is data-poor even though the dataset overall is enormous. That is the one
configuration in this domain where §1.5's structural objection does not apply.

---

## 11. Dataset

**Primary: Summit per-component power and thermal.** OSTI/OLCF DOI 10.13139/OLCF/1861393,
CC-BY-4.0, public, downloadable; companion github.com/at-aaims/summit_power_and_thermal_data.
Already present locally (`v2_research/summit/derived/`, read-only for this branch).

Verified by direct inspection, not from the paper:

| Signal | Range | Resolution | Coverage |
|---|---|---|---|
| `p0_gpu{0,1,2}_power` (per-GPU) | 17–400 W | float, 21,243 unique values | 99.997% |
| `gpu{0..5}_core_temp` | 25.0–72.4 °C (fleet sample) | float, 4,079 unique | 99.997% |
| `gpu{0..5}_mem_temp` (HBM2) | 23.0–55.0 °C | float, 5,254 unique | 99.996% |

Sampling 10 s; 6 GPUs × 4,626 nodes; 58 hosts locally.

**The verified regime-scarcity property — the reason this candidate exists** (12 hosts sampled):

| | value |
|---|---|
| Median GPU core temperature | **33 °C** |
| 99th percentile | ~51 °C |
| Fleet maximum observed | **72.4 °C** |
| Fraction of time > 50 °C | **~1.7%** |
| Fraction of time > 55 °C | **~0.2%** |
| Hosts reaching > 55 °C | 12 / 12 |

Enormous data overall; **the hot regime is ~0.2% of it**. Data-poor exactly where the model
matters. This is a measured property of production hardware, not a contrived split.

**Secondary: M100 ExaData** (Scientific Data 10:288, CC-BY). GPU core/mem temperatures reach
83 °C — hotter than Summit — but **`gv100card0` per-GPU power is identically zero across
10.7 M rows** (verified). Usable only as a temperature-regime reference, never to drive a
physical model. Do not design any experiment that needs M100 GPU power.

**Synthetic data: Class A — real data sufficient.** No simulation required or recommended.

---

## 12. Minimum prototype

```
Summit host a07n04, GPU0, within-segment
        ↓
P = p0_gpu0_power ; T = gpu0_core_temp   (10 s, floats)
        ↓
Split by REGIME, not by time:
   train on samples with T < 45 °C ; test on samples with T > 55 °C
        ↓
Three arms, identical inputs and split:
   (1) classical  : C dT/dt = P − (T − T_sink)/R   [3 params, least squares]
   (2) pure ML    : small MLP / GBT on (T, P, ΔP, lags) → T[n+1]
   (3) hybrid     : arm-1 RC backbone + small learned residual term
        ↓
Metric: multi-step out-of-sample RMSE on the HOT test set
        + physical admissibility (R > 0, C > 0, fitted T_sink near ~21 °C coolant)
        + the imbalance control: re-run arm 2 with tail reweighting
        ↓
GO / KILL
```

Scope: one host, one GPU, three models, one figure. Hours, no GPU compute, no new infrastructure.
Everything lives in `research_pinn_chip/prototype/`; nothing imports GLASSCHIP code.

---

## 13. Today's GO / KILL test

**GO** if, on the hot test set, the hybrid beats the pure-ML arm by a margin that **survives tail
reweighting** of the ML baseline, and the classical arm alone does not match the hybrid.

**KILL** if any of: pure ML wins after reweighting (physics adds nothing — the apparent gain was
class imbalance); the classical RC arm matches the hybrid (the network is decoration); or all
three fail badly in the hot regime (the lumped model does not describe this package, and the
premise collapses).

**If KILL:** stop immediately, do not add complexity to rescue it, and fall back to the
non-PINN GPU die↔HBM identification project from the previous audit — which requires no PINN
and scored higher overall.

---

## 14. September–October 2026 publication potential

**Moderate, and lower than the non-PINN alternative — stated plainly.**

Realistic venues if the prototype returns GO: **IPDPS Measurements, Modeling and Experiments**
(abstract 1 Oct, paper 8 Oct 2026 — very tight for a greenfield branch), **CCGrid 2027**
(abstract 24 Nov, paper 1 Dec 2026 — the realistic target), **ICPE 2027** (2027 deadline not
announced at audit time; verify in September), and **FGCS / JPDC** rolling as the floor.

Not viable: DAC/ICCAD (design-time, floorplan-based), SC/HPDC main tracks, and dedicated SciML
venues — the contribution would be an evaluation, not a method, and §3 shows the method space is
closed.

**Sequencing advice, unchanged from the previous audit and reinforced here:** the finished
GLASSCHIP paper is journal-submittable now and should be submitted on its own schedule. This
branch is exploratory. Let the GO/KILL result — not enthusiasm for PINNs — decide whether it
receives further time.

---

FINAL WINNER:
Physics-informed learning in the data-scarce high-temperature regime of production GPUs — a three-way evaluation (classical RC vs pure ML vs physics-constrained hybrid) of whether embedded thermal physics rescues prediction where operational data is scarce but thermal models are actually needed.

RESEARCH QUESTION:
On real production GPUs, does embedding a lumped thermal energy balance into a neural model improve temperature prediction in the high-temperature regime — which constitutes only ~0.2% of observed operation yet is the regime thermal models exist to predict — relative to both a purely data-driven model and a purely classical RC model trained on identical data?

PINN ROLE:
The physics constraint is the object of study, supplying an energy-balance backbone that is hypothesised to keep predictions bounded and physically admissible where training data is effectively absent, and the entire contribution is the honest measurement of whether it actually does.

DATASET:
Summit per-component power and thermal measurements (OSTI/OLCF DOI 10.13139/OLCF/1861393, CC-BY-4.0) — per-GPU power 17–400 W with GPU core and HBM temperatures at 10 s, 6 GPUs × 4,626 nodes, already local and verified; M100 ExaData as a temperature-regime reference only, since its per-GPU power channel is identically zero.

NOVELTY:
58/100

IMPACT:
62/100

FEASIBILITY:
88/100

PUBLICATION POTENTIAL:
66/100

TODAY'S PROTOTYPE:
On one Summit host and one GPU, split the data by temperature regime (train T < 45 °C, test T > 55 °C) and fit three arms on identical inputs — a three-parameter classical RC model, a black-box regressor, and an RC backbone plus a small learned residual — then compare multi-step out-of-sample RMSE on the hot test set, with the black-box arm re-run under tail reweighting as the decisive control against class imbalance.

DECISION:
INVESTIGATE FURTHER
