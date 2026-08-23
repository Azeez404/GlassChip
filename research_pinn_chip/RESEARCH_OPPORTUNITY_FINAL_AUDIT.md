# RESEARCH OPPORTUNITY — FINAL AUDIT
## PINN + semiconductor degradation: Candidates A, B, C

Audit only. No code, no prototype, no dataset creation, nothing committed. Every dataset claim
below was verified by fetching the source or extracting the source PDF — not taken from an
abstract.

---

## VERDICT

# NO VIABLE PINN PROJECT FOUND.

All three candidates fail, and they fail on **verified facts**, not on judgement calls:

| Candidate | Fatal finding | Evidence |
|---|---|---|
| **A — Hidden degradation state** | The degradation state in the only usable public dataset is **directly measured**, not hidden. Where a latent state does exist, extended Kalman and particle filters already estimate it successfully on this exact data. Direct PINN prior art exists. | NASA PHM 2011 paper, extracted: *"A single feature is used to assess the health state of the device (ΔR_DS(ON))"*; *"an extended Kalman filter and a particle filter were used as examples for model-based techniques. Both methods were able to provide valid results."* |
| **B — Cross-device generalization** | **No public dataset has enough devices.** The published NASA MOSFET prognostics analysis uses **one device (#36)** over ~210 minutes. The best multi-device power-cycling dataset (gEOL) is 21.51 MB and **subscription-gated**. | Extracted from NASA paper: *"Device #36 was used to test the RUL predictions... at t_p: 140, 150, ... 210 minutes"*; IEEE DataPort gEOL listing |
| **C — Sparse-observation degradation** | This is the **standard PINN sparse-data experiment**, run in every domain, and the specific claim is already published for degradation. The data is a single scalar over ~210 minutes with an already-irregular sampling rate — subsampling it is a toy exercise. | Literature: *"PINNs demonstrate capacity to infer latent degradation kinetics from sparse and noisy observations"* — already stated as an established capability |

This is the **fourth** structurally distinct direction to die in this research programme, and the
consistency of the failure mode is itself the finding. See §7.

**Recommendation: stop the PINN search. Proceed with the non-PINN alternative in §9.**

---

## 1. Dataset verification (this is what decided the audit)

I inspected sources directly rather than citing landing pages.

### NASA MOSFET thermal-overstress aging — *the primary candidate dataset*

Source: NASA Ames Prognostics Data Repository / NASA Open Data Portal. Reference publication
extracted in full (NTRS 20140010628, PHM Society 2011, 10 pages).

| Property | **Verified value** |
|---|---|
| Device | IRF520Npbf power MOSFET, TO-220 package, 100 V |
| Aging | Thermal + power cycling to failure |
| Failure mechanism | **Die-attach degradation** (single mechanism assumed) |
| Health feature | **ΔR_DS(ON)**, normalised ON-state resistance — a **single scalar** |
| Devices in published analysis | **One — "device #36"** |
| Duration | **~210 minutes** to failure |
| Sampling | **"These measurements do not have a fixed sampling rate due to the nature of the implementation"** — irregular |
| Failure threshold | Crisp, 0.05 increase in ΔR_DS(ON) |
| Established baselines | Gaussian process regression; **extended Kalman filter; particle filter** — *"Both methods were able to provide valid results"* |
| License | Not specified on the NASA portal; the data-file resource is not directly listed on the dataset page (only the publication PDF) |

**Three killers in one table.** The health state is a measured scalar, not a hidden state. There
is one device. Classical Bayesian filters already solve it.

### Other datasets checked

| Dataset | Verified status | Usable? |
|---|---|---|
| NASA IGBT accelerated aging (data.gov `7wwx-fk77`) | IRG4BC30KD, 600 V/15 A, thermal cycling, V_ge / V_ce / I_c. Comparable tiny scale. **Already used in published PINN RUL work.** | No — occupied |
| **gEOL power-cycling dataset** (IEEE DataPort, Dec 2023) | SiC MOSFET on-resistance for lifetime estimation. **21.51 MB, requires IEEE DataPort subscription** | **No — not freely public, and tiny** |
| PHM degradation-dataset survey (arXiv:2403.13694) | Exists; semiconductor entries could not be extracted cleanly from the PDF | Inconclusive — flagged honestly |
| Large SiC aging campaigns | Literature describes building one as an **aspiration**, e.g. work that "aims to develop a large accelerated aging dataset of SiC devices under various conditions" | **Does not yet exist publicly** |

**Conclusion: there is no public, freely accessible, multi-device semiconductor aging dataset of
the size that Candidates A/B/C require.** This alone ends the direction, independent of novelty.

---

## 2. Physics investigation

The physics here is genuinely simple and explainable, which is the one thing that *did* work out.

**Plain English:** every time the device heats up and cools down, the solder layer holding the
silicon die to its package is squeezed and stretched, because silicon and metal expand by
different amounts. Tiny cracks accumulate. Cracked solder conducts heat worse and electricity
worse, so the device's ON-state resistance creeps up. When it has crept up by about 5%, the part
is called failed.

The governing relations from the literature:

- **Arrhenius / thermally activated damage:** rate ∝ exp(−E_a / (k·T_j)). Damage accelerates
  exponentially with junction temperature.
- **Coffin–Manson thermal fatigue:** cycles-to-failure ∝ (ΔT_j)^(−n). Bigger temperature swings
  kill faster.
- **Miner's rule accumulation:** total damage = Σ (cycles at condition i / cycles-to-failure at
  condition i).
- **Observation model:** ΔR_DS(ON) increases monotonically with accumulated damage.

Now the audit questions that matter:

| Question | Answer |
|---|---|
| What is measured? | ΔR_DS(ON), junction temperature, electrical terminals |
| What is hidden? | Crack area / accumulated damage D |
| Is the equation differentiable? | Yes |
| **Is the hidden state identifiable from the data?** | **Only trivially.** With one monotone scalar observation and a monotone damage→resistance map, D is a reparameterisation of ΔR_DS(ON). You are not recovering a hidden state; you are relabelling the measured one. |
| Valid over the regime? | Coffin–Manson and Miner are empirical and calibrated per package; with one device you cannot fit their exponents and validate them |
| Can a PINN meaningfully use it? | **No** — see §3 |

**This is the crux of Candidate A.** "Hidden degradation state" sounds like a latent-variable
problem, but with a single monotone observable driving a single monotone latent, the map is
invertible and the latent adds no information. The NASA authors recognised this: they treat
ΔR_DS(ON) directly as *the* health state.

---

## 3. PINN justification test

The hard question for each candidate: *what does the physics provide that the data does not?*

| Candidate | Claimed advantage | Verdict |
|---|---|---|
| A | Recovers hidden damage state | **FAIL.** State is a monotone reparameterisation of the measurement. And EKF/particle filter already do latent-state estimation on this data, successfully. Beating a particle filter on a 1-D latent state with known dynamics is the same trap that killed the GPU prototype: low dimension + known physics ⇒ classical Bayesian filtering wins. |
| B | Physics reduces device-specific data needed | **FAIL on data, not on logic.** The argument is sound; there is no dataset with enough devices to test it. Leave-one-device-out with N≈1–10 has no statistical power. |
| C | Physics regularises sparse observations | **FAIL on novelty.** This is the canonical PINN demonstration, published across domains, and specifically claimed for degradation already. |

Baseline comparison for Candidate A, honestly: linear regression on log-resistance, a Gaussian
process (published), an EKF (published), a particle filter (published), and a simple Arrhenius
fit are all appropriate — and the published ones already work. A PINN enters a solved
low-dimensional problem with no structural advantage.

---

## 4. Prior-art audit

Searched 2020–2026 across arXiv, IEEE Xplore, ACM DL, ScienceDirect, Springer, Nature, NASA
NTRS, IEEE DataPort — with and without the term "PINN".

| Work | Overlap | Effect |
|---|---|---|
| *Remaining useful lifetime estimation for discrete power electronic devices using physics-informed neural network* — **Scientific Reports 2023** (s41598-023-37154-5) | **DIRECT — Candidate A** | PINN for RUL of discrete power electronics on the NASA dataset. Reported physics-informed RNN gains: MSE −38.86%/−35.69% in-sample, −24.7%/−51.3% out-of-sample. **This is Candidate A, published.** |
| *Physics-informed Neural Network Approach for Early Degradation Trajectory Prediction of Power Semiconductor Modules* (2025) | **DIRECT — Candidate A** | Degradation trajectory prediction for power semiconductor modules, physics-informed. |
| *Physics-Informed Condition Monitoring of SiC Power Modules* (arXiv:2608.08363, 2026) | **DIRECT — Candidate A** | Physics-grounded features incl. a **Miner-rule cumulative damage accumulator** from junction temperature. The "hidden damage state" framing, already executed. |
| *Meta-Learning and Knowledge Discovery based PINN for RUL* (arXiv:2504.13797, 2025) | **DIRECT — Candidate B** | Meta-learning + PINN for RUL — few-shot adaptation across conditions is the core of Candidate B. |
| *Joint estimation of battery SOH and RUL via degradation encoding and implicit PINN* (J. Power Sources 2026) | STRONG PARTIAL | Latent degradation encoding + implicit PINN. Adjacent device class, same idea. |
| *BPINN-EM-Post* (arXiv:2503.17393) | PARTIAL | Bayesian PINN for stochastic electromigration damage — the electromigration variant already exists. |
| *Toward accurate RUL and SoH estimation using reinforced graph-based PINN with dynamic weights* (arXiv:2507.09766) | PARTIAL | Cross-condition PINN RUL with adaptive weighting. |
| NASA PHM 2011 (Celaya et al.) | **FOUNDATIONAL — and it pre-empts A** | GP + EKF + particle filter on ΔR_DS(ON); both model-based filters valid. |

Explicit statement located in the recent literature: *"Hidden states represent unobservable but
decisive intrinsic state variables that drive equipment degradation... PINNs demonstrate capacity
to infer latent degradation kinetics from sparse and noisy observations."* **That sentence is the
thesis of Candidates A and C, already asserted and published.**

---

## 5. Novelty scoring

Scale: 0 solved · 1 trivial variation · 2 incremental · 3 meaningful extension · 4 strong ·
5 distinctive.

| Candidate | Core | Supporting | Experimental | Dataset | Generalization | **Class** |
|---|---|---|---|---|---|---|
| A — Hidden state | 0 | 1 | 1 | 0 | 1 | **0–1: already solved / trivial variation** |
| B — Cross-device | 2 (idea) | 1 | 2 | 0 (no data) | 2 | **1: untestable, so unrealisable** |
| C — Sparse observation | 0 | 1 | 1 | 0 | 1 | **0: standard PINN demo** |

| Axis (0–100) | A | B | C |
|---|---|---|---|
| Novelty | 12 | 22 | 8 |
| Scientific significance | 25 | 40 | 15 |
| **PINN necessity** | **10** | 35 | 15 |
| **Dataset quality** | 20 | **5** | 20 |
| Data availability | 45 | 10 | 45 |
| Feasibility | 70 | 15 | 70 |
| Experimental clarity | 55 | 30 | 60 |
| Generalization potential | 15 | 45 | 15 |
| Reviewer defensibility | 12 | 20 | 10 |
| Publication potential | 15 | 18 | 10 |
| **Overall (not an average)** | **14** | **16** | **11** |

Scores are not averaged, per instruction. A is capped by PINN-necessity 10 and direct prior art.
B is capped by dataset quality 5 — a good idea with no data is not a project. C is capped by
novelty 8.

---

## 6. Reviewer attacks (all three fail at attack #1)

**Candidate A.** *"Your 'hidden' state is a monotone function of your measured ΔR_DS(ON) — what
exactly is hidden?"* No answer. *"A particle filter already does this on your dataset, in a 2011
paper — why a PINN?"* No answer. *"Scientific Reports 2023 published PINN RUL for discrete power
electronics; what is new?"* No answer. *"Where is the physical ground truth for crack area?"*
There is none. *"Does the gain survive giving the baseline the same data?"* Untested, and the
GPU prototype says probably not.

**Candidate B.** *"You claim cross-device generalization from one device."* Fatal.
*"Leave-one-device-out with N<10 — what is your confidence interval?"* Meaningless.
*"Meta-learning PINN for RUL was published in 2025."* Fatal.

**Candidate C.** *"Sparse-data PINN experiments exist in every domain since 2019."* Fatal.
*"Your full dataset is one scalar over 210 minutes at irregular intervals — what does 1%
subsampling even mean?"* Fatal.

None of these attacks can be answered experimentally, because they are about the dataset and the
prior art, not about model performance.

---

## 7. Why this keeps happening — the structural finding

Four independent directions have now died, and the pattern is consistent enough to state as a
conclusion rather than a run of bad luck:

1. **GPU hot-regime thermal prediction** — killed *experimentally*: classical RC 4.88 °C,
   XGBoost 4.44 °C, PINN 27.81 °C with physics-induced runaway.
2. **Thermal fields / hotspots / IR drop** — physics is known and linear, so classical solvers
   and CV surrogates win; and geometry-dependent formulations need floorplans that are
   proprietary for exactly the chips with public telemetry.
3. **Leakage–temperature feedback** — killed on *verified data*: the signal is ~0.1–0.3 W on a
   35 W baseline and fully confounded, since power causes temperature.
4. **Semiconductor degradation (this audit)** — the latent state is not latent, the classical
   filters already work, and no multi-device public dataset exists.

**The generalisation:** physics-informed neural learning pays off when the physics is
high-dimensional or nonlinear, the operator is unknown, and labels are scarce relative to model
complexity. Computer-chip and device problems accessible with *public* data are the opposite:
low-dimensional, linear or monotone, with known operators and either abundant telemetry or a
handful of devices. In that corner, classical estimation — least squares, Kalman, particle
filtering, sparse solvers — is not merely competitive, it is the right tool.

This is a legitimate, reportable conclusion. It is also a much more useful thing to know now
than after another six weeks of implementation.

---

## 8. Final kill test

The kill condition was set as: *KILL if PINN does not outperform the strongest baseline under
sparse-data or unseen-device conditions.*

It is worse than that. For Candidate A the strongest baselines (EKF, particle filter) are
**already published as working on the exact dataset**, and for Candidate B the unseen-device
experiment **cannot be run at all** for want of devices. The kill condition is met before a line
of code is written — which is the cheapest possible way to meet it.

---

## 9. Recommended non-PINN alternative

Two things are worth the remaining time, in this order.

### First — submit the work that is already finished
The GLASSCHIP measurement-quality manuscript is complete, internally consistent, reproducible,
and journal-submittable. Target **FGCS or JPDC** (rolling submission). This is the only asset in
the portfolio with a near-certain outcome, and it is being delayed by the search for a
neural-network angle it does not need.

Before submitting, the four must-fixes from the earlier strategy audit still apply: resolve the
12 `[VERIFY]` citations; stop calling 116 sockets "the fleet"; explain the F2 decimation anomaly;
cite Ellis/Shin SC'21 and state that the 1 Hz Summit source is not in the public release.

### Second — the strongest genuine research available
**Measurement-based identification of GPU die-to-HBM thermal coupling across production GPUs**
(detailed in `RESEARCH_OPPORTUNITY_HUNT.md`). Scored Novelty 68 / Impact 76 / Feasibility 88.

Why it beats every PINN candidate examined: the data is verified and local (per-GPU power
17–400 W plus **two** measured thermal states at float resolution, 6 GPUs × 4,626 nodes); the
inverse problem is well-posed; the physics is a two-node energy balance explainable in four
sentences; HBM thermal coupling is a live constraint on AI accelerators whose published values
are all simulated; and both possible outcomes are publishable. It needs no neural network, and
that is a feature — it removes the single hardest reviewer question from the paper.

If a physics-informed component is still wanted afterwards, the honest option is the structural
UDE horizon-stability test from `RESEARCH_OPPORTUNITY_HUNT_V2.md` (Novelty 34, workshop ceiling),
appended as a half-day experiment once that harness exists. It should not lead.

---

## 10. What would change this verdict

Stated so the direction can be reopened on evidence rather than on hope:

- A **public, freely downloadable, multi-device** semiconductor aging dataset appearing — say
  ≥50 devices across ≥3 stress conditions with run-to-failure trajectories. The literature shows
  groups are working toward this; when one lands, Candidate B becomes testable overnight.
- Access to a **multi-physics** degradation setting where the latent state is genuinely
  higher-dimensional than the observation, rather than a monotone reparameterisation of it.
- Laboratory access to run a power-cycling campaign — explicitly out of scope here.

Until one of those changes, adding a neural network to this research programme is not justified
by the evidence.

---

# FINAL DECISION

**KILL**

All three candidates fail. Candidate A fails because the hidden state is not hidden and
classical Bayesian filters already solve it on the same dataset, with direct PINN prior art in
Scientific Reports 2023 and two 2025–2026 follow-ups. Candidate B fails because the published
NASA MOSFET prognostics analysis rests on a **single device over 210 minutes**, and the only
multi-device power-cycling dataset located is subscription-gated at 21.51 MB — cross-device
generalization cannot be tested. Candidate C fails because sparse-observation PINN demonstration
is the most-replicated experiment in the field and the specific degradation claim is already
published.

# NO VIABLE PINN PROJECT FOUND.

**Strongest non-PINN alternative:** submit the finished GLASSCHIP measurement-quality paper to
FGCS/JPDC, then pursue measurement-based GPU die-to-HBM thermal coupling identification —
verified public data, well-posed physics, no neural network required.
