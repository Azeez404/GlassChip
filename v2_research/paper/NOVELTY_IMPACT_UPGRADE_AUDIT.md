# NOVELTY + IMPACT UPGRADE AUDIT

Audit date: 2026-08-23. Strategy only — no manuscript, figure, table, Phase 2/3 artifact,
`src/`, or `tests/` modification; nothing committed; no experiments run.

**Two corrections to earlier advice, stated up front because both change decisions:**

1. The previous strategy audit named the **M100 replication** as the single highest-value
   extension. Inspection of the per-unit contents of the Phase 2B artifact changes that
   ordering. A cheaper, lower-risk, confound-free extension with equal or greater novelty
   exists inside data already computed. M100 drops to second priority.
2. In the course of this audit I initially read the "degradation compresses apparent fleet
   heterogeneity" result as holding across conditions. It does not. Checked in α-space, the
   effect **reverses for quantization** and survives only for spatial aggregation. The
   corrected version is in §1.9 and it is more interesting than the original — but the
   uncorrected version would have been an overclaim.

---

## 1. Scientific core

**1.1 The deepest question this project can actually answer.** Not "does coarse telemetry
bias a fitted parameter" — errors-in-variables answered that decades ago. The question the
data can uniquely answer is:

> When a fleet of nominally identical nodes is measured coarsely, is the *structure* of its
> apparent thermal heterogeneity — the spread between units, and the ordering of which units
> are fast or slow — preserved, distorted, or manufactured by the measurement?

**1.2 Strongest empirical relationship demonstrated.** Measurement condition → identified τ,
under fixed hardware and workload, with per-unit pairing across all five conditions.

**1.3 What is merely a consequence of the estimator.** More than the manuscript admits.
τ = −Δt/ln α is a strongly nonlinear map, near-singular as α→1. Any statement about the
*dispersion* of τ is partly a statement about that map. Verified directly from the locked
artifact:

| Condition | τ IQR ratio vs F0 | α IQR ratio vs F0 | CV(1−α) |
|---|---|---|---|
| F0 full | 1.000 | 1.000 | 0.465 |
| F1 quantized | **0.168** | **2.024** | 0.383 |
| F2 downsampled | 3.410 | 1.022 | 0.539 |
| F3 spatial | **0.165** | **0.461** | 0.248 |
| F4 combined | 0.191 | 0.728 | 0.183 |

Read this carefully. In τ-space, quantization looks like a 6× *compression* of fleet
dispersion. In the underlying α, it is a 2× *expansion* — the classical, expected direction
for measurement noise. **The apparent F1 homogenization is an artifact of the τ
parameterization, not a property of the system.** F3 and F4 compress in *both* spaces and on
the scale-free CV(1−α), so those are real.

This is the most important internal finding of the audit, in both directions: it kills one
tempting claim and it hands the paper a genuine, self-critical methodological result.

**1.4 What could become a general principle if framed properly.** That reporting an
identification result in a physically-intuitive but nonlinear reparameterization (τ rather
than α) can manufacture an apparent population-level effect that does not exist in the
estimated parameter. Modest in scope, real, and demonstrable from data already in hand.

**1.5 Interesting but not publication-worthy alone.** The online rolling-τ null (§7.7). The
residual-prediction null (§7.4). The socket-pair correlation. Each is one honest paragraph,
none is a contribution.

**1.6 Single strongest result.** Currently C4 (quantized estimate below the sampled fleet
minimum). After the upgrade in §12, it should be the **rank-preservation collapse under
spatial aggregation** — Spearman ρ(τ_F0, τ_F3) ≈ 0.44, ρ(τ_F0, τ_F4) ≈ 0.46, against
ρ(τ_F0, τ_F2) ≈ 0.96. Spearman is invariant to monotone reparameterization, so unlike the
dispersion result it is immune to the objection in §1.3.

**1.7 Single weakest part.** The F2 anomaly, still unexplained in the manuscript: for a true
first-order process τ is invariant to decimation, so 394 s → 910 s says the process is not
first-order and F0 is a reference regime rather than ground truth.

**1.8 Doing more work than the manuscript acknowledges.** The Phase 2B artifact stores
`taus` as a **20-element per-unit list for every condition** — fully paired across F0–F4.
The manuscript uses only the medians. Every per-unit analysis below is already computed and
sitting unread on disk. This is the single largest missed opportunity in the project.

**1.9 Looking more impressive than it is.** Three things. The "0.29×" ratio is reported as a
scalar; per-unit it ranges **0.18–0.52**, so it is a distribution, not a factor. The τ-space
dispersion collapse (§1.3). And `src/alignment/` — good engineering, but an as-of join with
staleness bounds is standard, and it is not a research contribution until an experiment shows
the staleness bound biases an identified parameter.

**1.10 Smallest conceptual upgrade with large impact.** Stop reporting condition-level
medians and start reporting **per-unit paired outcomes**. Same data, no new computation,
and it changes what the paper is about.

---

## 2. Hidden novelty

Live search, 2018–2026, conceptual rather than keyword-matched.

| Prior work | Class | Bearing |
|---|---|---|
| Bartolini group HPC node thermal ID under 1 °C quantization (IEEE Xplore 8863115, 7793664; arXiv:1810.01865) | **PARTIAL OVERLAP — closest** | They overcome quantization for accuracy on single nodes; nothing on cross-unit rank or population structure. |
| Quantized-observation system ID (Wang/Yin/Zhao; *Automatica* 2008; arXiv:1804.10015) | SUPPORTING | Owns the single-estimator bias mechanism. Says nothing about population-level ordering. |
| Nonlinear mixed-effects **shrinkage** literature (e.g. PubMed 22993107, "Shrinkage in nonlinear mixed-effects population models"); noise-free variance estimation for heterogeneity (PMC4408041); attenuation bias in rating-scale regression (PMC11063000) | **PARTIAL OVERLAP — and the most dangerous find in this audit** | Establishes in statistics/pharmacometrics that estimation error inflates apparent between-unit variance, that shrinkage obscures correlations among random effects, and that observed dispersion overstates true dispersion. A statistically literate reviewer will cite this. **Cite it first yourself.** Note the distinction: that literature predicts *inflation*; F3/F4 show *compression* in both parameterizations, which additive-error theory does not predict. |
| Chip-multiprocessor thermal sensor placement — readings differing from true max core temperature by up to 12.6 °C with 16 sensors/core, ~10.6% of thermal emergencies missed | **SUPPORTING — directly relevant to F3** | Establishes that spatial sensing choice biases *temperature*. Does not address identified *dynamic parameters* or cross-unit ordering. This is the remaining distinction and it is a real one. |
| Künsch 1989 / Liu–Singh 1992 | SUPPORTING | Owns the uncertainty method. |
| Ellis/Shin et al. SC'21 (10.1145/3458817.3476188) | PARTIAL — **still uncited** | Canonical Summit characterisation by the dataset authors. Still a visible hole. |
| Borghesi et al., M100 ExaData, *Scientific Data* 10:288 | SUPPORTING | Second dataset. |
| Kalibre / TOMACS datacenter twin calibration (10.1145/3604283); Tier-0 room thermal characterization (10.1007/978-3-030-67077-1_1) | DIFFERENT PROBLEM | Motivation and heterogeneity-is-real support. |
| Sensor-simulation validation / domain-gap literature (autonomous driving, computational imaging) | DIFFERENT PROBLEM, methodologically load-bearing | Validating simulated degradation against real degraded data is standard there and absent in HPC telemetry. Framing support only. |

**No DIRECT OVERLAP found** for any claim in this project.

### Gap assessment

| Gap | Evidence available | Closest prior work | Overlap | Remaining distinction | Novelty | Confidence |
|---|---|---|---|---|---|---|
| **A** quality → parameter sensitivity | Full F0–F4, per-unit | Quantized system ID | PARTIAL | Magnitudes on real HPC | Low–moderate | High |
| **B** artifact vs fleet variation | C4, computed | None found | — | The comparison itself | Moderate | High |
| **C** degradation sim → real coarse telemetry | Requires M100 run | Sensor-sim validation (other domains) | DIFFERENT | First in HPC telemetry | Moderate–high | Medium |
| **D** cross-machine sensitivity | Requires M100 run | None found | — | Whole thing | Moderate–high | Medium |
| **E** measurement-induced *apparent* heterogeneity | **Computed; direction corrected in §1.3** | Mixed-effects shrinkage | PARTIAL | Compression (F3/F4) is opposite to the classical inflation prediction, and holds in α-space | **Moderate–high** | Medium-high |
| **F** parameter instability from resolution | Per-unit ratios 0.18–0.52 | Errors-in-variables | PARTIAL | Bias is *unit-dependent*, so no global correction factor exists | Moderate | High |
| **G** coarse telemetry creating apparently different "virtual machines" | **ρ_s ≈ 0.44 for F3/F4 — but CI at n=20 is [−0.06, 0.80]** | Sensor placement literature | SUPPORTING only | Rank-level invalidity of cross-unit comparison | **High if n=116** | **Low at n=20, high at n=116** |
| **H** telemetry preprocessing dominating physical heterogeneity | Partly (C4 + E + G) | None found | — | Combination | Moderate–high | Medium |
| **I** report measurement-sensitivity alongside estimates | Recommendation, not result | Reporting-guideline literature generally | DIFFERENT | Modest, honest | Low–moderate | High |
| **J** identification reliability envelope | **Not supported** — needs synthetic ground truth | Practical identifiability literature | PARTIAL | Would be a different paper | n/a | High that it is out of scope |

**Gap G is the prize, and it is currently underpowered.** ρ = 0.436 at n = 20 has a
bootstrap 95% CI of [−0.059, 0.798]. The point estimate is striking; the interval is useless.
Everything in §11–§12 follows from that single fact.

---

## 3. Novelty opportunities

### Class A — FREE (existing artifacts, no new computation)
1. **Per-unit paired ratio distributions** instead of scalar ratios (F1: 0.18–0.52). Kills the
   implicit assumption that a global calibration factor could correct the bias.
2. **Rank-preservation analysis**, ρ_s(τ_F0, τ_Fk) per condition. Transform-invariant.
3. **α-space / scale-free dispersion cross-check** (§1.3). Self-critical, cheap, and it is the
   kind of check that earns a system-identification reviewer's trust.
4. **Artifact-to-heterogeneity ratio**, |Δτ| / IQR(τ_fleet) — C4 expressed as a number rather
   than a sentence.
5. **Degradation-mode taxonomy** from 1–3: quantization *scales down and disperses*;
   downsampling *preserves order and inflates*; spatial aggregation *flattens and reorders*.
   Three qualitatively different failure modes, free from data already computed.
6. **F2 explanation** as model-order misspecification (~150 words).
7. **Subset-representativeness already computed** (subset median 394 vs remaining-96 median 440).

### Class B — CHEAP (<1–2 days)
8. Quantization/decimation dose–response on the existing 20-unit subset.
9. Bootstrap CIs on the rank correlations and dispersion ratios.
10. Ambient-stratified reporting once M100 is in play.

### Class C — MODERATE (days)
11. **F0–F4 ablation across all 116 fleet units** — the pivotal item; see §12.
12. M100 native-regime identification and cross-machine sensitivity comparison.
13. Staleness-bound axis via `AsofAligner` on M100.

### Class D — EXPENSIVE
14. Synthetic-ground-truth identifiability envelope (gap J). **Do not do** — different paper.
15. Third machine. No data. **No.**

### Class E — PROJECT DETOUR
16. Benchmark with leaderboard. **No** — no competing community exists; it is a wrapper.
17. Any PINN/SciML reframing. **No.** The PINN is a discarded baseline.
18. Digital-twin system. **No.** No twin exists.

---

## 4. Minor novelty stack

The paper does not need one revolutionary claim. It needs three defensible ones that share a
single thesis. Best stack evaluated:

| Stack | Novelty | Significance | Effort | Reviewer resistance | Overclaim risk |
|---|---|---|---|---|---|
| **S1: rank distortion + unit-dependent bias + artifact-vs-heterogeneity, all at n=116** | **High** | **High** — invalidates cross-unit thermal comparison under single-sensor telemetry | **Moderate (Class C, one run)** | **Low–moderate** — transform-invariant, statistically powered, and not predicted by errors-in-variables | **Low** |
| S2: dose–response curve + uncertainty envelope + resolution threshold | Moderate | Moderate | Cheap–moderate | Moderate — "threshold" is arbitrary without validation | **Moderate–high** |
| S3: artifact + heterogeneity + identification/prediction dissociation (current paper) | Low–moderate | Moderate | Free | Moderate — two nulls padding one positive | Low |
| S4: degradation + as-of alignment + reproducibility protocol | Low | Low–moderate | Moderate | **High** — reviewers read this as software, not science | Moderate |
| S5: S1 + cross-machine M100 replication | **Highest** | **Highest** | High | Low | Moderate — confounds |

**Recommended: S1, with S5 as the stretch if time allows.** S1's three components share one
thesis, are mutually reinforcing, come from a single experimental run, and none requires new
data. S4 is a trap. S2's "threshold" is unvalidated branding.

---

## 5. Strongest research question

| Question | Evidence now | Evidence needed | Novelty | Appeal | Feasible | Risk |
|---|---|---|---|---|---|---|
| A — how does quality bias identification? | Full | none | Low (textbook) | Low | Yes | Reads as known |
| B — when is resolution insufficient? | Partial | Threshold validation | Moderate | Moderate | Partly | Arbitrary threshold |
| **C — can artifacts create apparent heterogeneity exceeding real heterogeneity?** | **Strong (C4 + §1.3 + rank)** | **n=116 for power** | **High** | **High** | **Yes** | Low |
| D — misleading models despite low prediction error? | Partial (§7.4) | More model classes | Moderate | Moderate | Partly | Two nulls |
| E — transferability across telemetry regimes? | Needs M100 | M100 run | Moderate–high | High | Yes | Confounds |
| F — stability envelope? | Weak | Synthetic truth | High | High | **No** | Different paper |
| G — predict reliability from telemetry alone? | None | Substantial | High | High | **No** | Fantasy now |
| **H — how much observed variation is physical vs measurement-induced?** | **Strong** | **n=116** | **High** | **High** | **Yes** | Low |

**Chosen — a fusion of C and H:**

> When a fleet of nominally identical nodes is measured coarsely, how much of its apparent
> thermal heterogeneity — both the spread between units and the ordering of which units are
> fast or slow — is physical, and how much is manufactured by the measurement?

This is strictly stronger than the current question. It subsumes C4 as a corollary, it makes
the per-unit data load-bearing, it is not answered by errors-in-variables theory (which
concerns a single estimator, not a population's rank structure), and it is answerable with one
additional run of existing frozen code.

---

## 6. New metric candidates

| Candidate | Definition | Meaning | Verdict |
|---|---|---|---|
| **Rank preservation** | ρ_s(τ_F0, τ_Fk) over units | Does the regime preserve *which* unit is faster? | **INTRODUCE — but do not name or brand it.** Spearman's ρ needs no rebranding. Invariant to monotone reparameterization, so immune to §1.3. Directly operational: if ρ is low, cross-unit comparison under that regime is invalid regardless of bias correction. |
| **Artifact-to-heterogeneity ratio** | \|τ_Fk − τ_F0\| / IQR(τ_fleet) | Artifact size in units of real spread | **INTRODUCE, unbranded.** Free, interpretable, normalised, and it is C4 stated quantitatively. Report alongside the raw shift, never instead of it. |
| MDI (branded version of the above) | same | same | **REJECT the branding.** An acronym on a ratio of two reported numbers invites "you invented a metric to have a contribution." |
| Measurement sensitivity dτ/dq | gradient over degradation | Local sensitivity | **DEFER.** Only meaningful with the dose–response sweep, and it is a result, not a metric. |
| Identification Stability Index | composite | — | **REJECT.** Pure branding; composite of things better reported separately. |
| Telemetry Adequacy Threshold | coarsest config with τ within tolerance | Provisioning guidance | **REJECT for this paper.** The tolerance is arbitrary and unvalidated; presenting it as a threshold invites "on what basis?" Say it in prose in §10 instead. |
| Artifact/natural variation ratio | as above | duplicate | Same as row 2. |

Two metrics, both unbranded, both computable from existing artifacts. That is the right
number. A paper of this novelty level introducing four named metrics reads as compensating.

---

## 7. Finished-product analysis

| Candidate product | Verdict |
|---|---|
| Measurement-quality **benchmark** | **No.** Two datasets and five obvious perturbations, with no community competing on the task. A wrapper. |
| Thermal-identification **robustness protocol** | **Partially yes** — as a reported *practice* ("report ρ_s across your measurement regimes before comparing units"), not as shipped software. |
| **Telemetry adequacy test** | No. Requires a validated threshold that does not exist. |
| **Parameter stability analysis** | Yes — this is essentially what S1 is. |
| **Cross-machine validation study** | Yes, if M100 lands. Secondary. |
| Diagnostic **tool** | No. The diagnostic is two lines of scipy; shipping it as a tool overstates it. |
| **Reproducibility package** | Yes, and already largely built. Ship it; do not claim it as the contribution. |
| Measurement-quality **characterization methodology** | Overreach for one machine and one model order. |

**Strongest realistic finished product:** *An empirical study, with a fully reproducible
artifact, showing that telemetry choices distort a supercomputer fleet's apparent thermal
heterogeneity — in magnitude, in dispersion, and in rank order — and that the distortion can
exceed the real hardware differences the fleet exhibits; together with the two simple,
unbranded diagnostics needed to detect the problem before comparing units.* No framework, no
benchmark, no tool.

---

## 8. Five-reviewer attack

**R1 — HPC systems researcher.**
Likes: real Summit data, 116 units, operational relevance, reproducibility.
Objects: "your ablation used 20 of 116 units — why?" **Currently unanswered, and it is the
easiest objection in the paper to make.** Demands: the full fleet.
Cheapest neutralizer: run F0–F4 on all 116. **Worth doing — it is §12.**

**R2 — System identification expert.**
Likes: frozen estimator, block bootstrap, honest τ-vs-R·C discipline.
Objects: (a) τ is a nonlinear reparameterization of α and your dispersion claims are
transform-dependent; (b) F2's decimation shift proves first-order misspecification.
Answered by: nothing currently. Neutralizer: the α-space table (§1.3) and the F2 paragraph —
both free. **Do both.** R2 is the reviewer most likely to reject and most cheaply satisfied.

**R3 — Scientific ML researcher.**
Likes: the permutation null and chronological OOS protocol.
Objects: R² ≤ 0.066 is thin; the PINN is undermotivated.
Answered by: §7.4 and §9.5 already, adequately. Neutralizer: compress §7.4, keep the null.
**Do not expand.** R3 is not the target reviewer and should not be courted.

**R4 — Measurement / experimental-methods researcher.**
Likes: the controlled same-hardware ablation; this is their idea of a clean design.
Objects: one point per axis, no dose–response; and no validation of simulated degradation
against real coarse telemetry.
Neutralizer: the dose–response sweep (Class B) and, ideally, M100. **Do the sweep; M100 if time.**

**R5 — Hostile general reviewer.**
Objects: "errors-in-variables is textbook; this is a known effect on a new dataset."
Answered by: nothing in the current framing — the manuscript concedes this openly, which is
honest but leaves the reviewer's argument standing.
Neutralizer: **the rank result.** Errors-in-variables predicts attenuation of an estimator; it
does not predict that the *ordering* of a population is destroyed. This is the only available
answer to R5 and it requires n=116 to be statistically defensible.

### The three objections that will determine acceptance
1. **R1 — "why only 20 of 116 units?"** Cheap, obvious, and currently unanswerable.
2. **R5 — "this is textbook errors-in-variables."** Only the rank result answers it.
3. **R2 — "your dispersion effects are an artifact of the τ parameterization."** Correct as
   stated for F1, and free to fix.

All three are resolved by the same single change plus one free table.

---

## 9. Title optimization

| # | Title | Group | Reviewer reading | Strength | Risk | Venue |
|---|---|---|---|---|---|---|
| 1 | Measurement Quality, Thermal Identification, and Residual Predictability in Supercomputer Temperature Measurements *(current)* | A | Three topics, no thesis | Accurate | **Announces the two nulls in the title**; no claim | FGCS |
| 2 | How Telemetry Resolution Biases Thermal Model Identification on a Supercomputer | B | Clear, modest | Clear | Sounds textbook to R5 | FGCS/JPDC |
| 3 | **Measured or Real? Telemetry Choices Distort the Apparent Thermal Heterogeneity of a Supercomputer Fleet** | C | Sharp thesis, testable | **Strong** | Needs the n=116 result to earn "distort" | **IPDPS MME** |
| 4 | Apparent Thermal Heterogeneity: Separating Measurement Artifacts from Hardware Variation Across 116 Supercomputer Sockets | B/E | Precise, quantified | Strong | Long | IPDPS/CCGrid |
| 5 | When Coarse Telemetry Reorders Your Fleet: Rank Distortion in Thermal Model Identification | C | Memorable, specific | Strong | "Reorders" must be firm at n=116 | IPDPS MME |
| 6 | Telemetry Resolution Can Exceed Hardware Variation in Supercomputer Thermal Model Identification | B | Direct claim | Strong | Slightly flat | CCGrid/FGCS |
| 7 | On the Sensitivity of Identified Thermal Parameters to Telemetry Quality in HPC Systems | A | Safe | Safe | Forgettable | JPDC |
| 8 | Measurement-Induced Heterogeneity in Supercomputer Thermal Models | C | Compact, strong | Strong | Compresses to near-slogan | IPDPS |
| 9 | What Does a Fitted Thermal Time Constant Measure? Telemetry Effects on Identification Across a 116-Socket Fleet | E | Thoughtful | Good | Question titles read soft at IPDPS | FGCS |
| 10 | Quantization, Sampling, and Spatial Aggregation: Three Distinct Failure Modes in HPC Thermal Identification | D/E | Taxonomy-forward | Good | Taxonomy must be earned at n=116 | IPDPS/CCGrid |

**Selected: #4** — *Apparent Thermal Heterogeneity: Separating Measurement Artifacts from
Hardware Variation Across 116 Supercomputer Sockets.*

It states the thesis, quantifies the scope, avoids every forbidden word, survives a hostile
reading, and — critically — the "116" commits the paper publicly to the full-fleet ablation,
which is exactly the discipline this project needs. #3 is the better title if the rank result
lands strongly; decide after the run.

**A title change IS required.** The current title names the two weakest results in the paper.

---

## 10. Venue impact

Deadlines verified live in the preceding strategy audit (2026-08-23); unchanged here.

| Venue | Scope fit | Fit now | Fit after upgrade | Novelty expectation | Window | Difficulty | Does the upgrade change eligibility? |
|---|---|---|---|---|---|---|---|
| **IPDPS 2027 MME** | Strong — track explicitly covers measurement, modelling, experiments, energy/power/accuracy | Low | **High** | High | abstract 1 Oct, paper 8 Oct 2026, double-anonymous, 10 pp | High | **Yes — decisively.** The rank result at n=116 is what makes this submittable rather than aspirational. |
| **CCGrid 2027** | Good | Low–moderate | **High** | Moderate–high | abstract 24 Nov, paper 1 Dec 2026 | Moderate–high | **Yes.** Pre-committed fallback; 8 weeks after IPDPS with reviews in hand. |
| **FGCS** | Strong; right reviewer pool (CINECA/RUAD line) | **Adequate today** | High | Moderate | Rolling | Moderate | No — eligible either way. **This is the floor that de-risks everything.** |
| **JPDC** | Good | Adequate | High | Moderate | Rolling | Moderate | No. |
| ICPE 2027 | Good (HPC thermal modelling has appeared there) | Low | Moderate–high | Moderate | **2027 deadline not announced at audit time** | Moderate | Possibly; verify in September. |
| HPC-ODA / HPCMASPA 2027 | **Best topical fit** | High | High | Low–moderate | ~11 months out | Low | No — but slow. |
| SC 2027 / TPDS | Fine topic, short novelty | Very low | Low–moderate | Very high | — | Very high | **No. Do not submit.** |
| HPDC / ICS / PPoPP | Poor scope fit | Very low | Very low | Very high | — | Very high | **No.** |
| TOMACS | Weak — wants simulation methodology | Very low | Low | High | Rolling | High | **No.** |
| Any ML/SciML venue | None | — | — | — | — | — | **No.** |

Optimizing P(accept) × impact × feasibility: **the upgrade moves the ceiling from
"journal-only" to "IPDPS MME is a real shot with CCGrid as a soft landing," at a cost of days
rather than weeks.** That is the best available trade in the project.

---

## 11. Minimum / Optimal / Ambitious

### VERSION 1 — MINIMUM
**Changes:** All Class A items (per-unit ratios, rank analysis, α-space cross-check,
artifact-to-heterogeneity ratio, degradation taxonomy, F2 explanation), the four must-fixes
from the prior audit, title change. **No new experiments.**
Experiments: none. Compute: none. Time: **3–5 days.**
Novelty 46 · Impact 48 · Reviewer resistance moderate · Ceiling **FGCS/JPDC** ·
Acceptance improvement **+10–14 pp at journal level; does not open IPDPS**
(the rank result stays underpowered at n=20 and R1's "why 20 units?" stays unanswered).

### VERSION 2 — OPTIMAL ✅ **RECOMMENDED**
**Changes:** Version 1, **plus the F0–F4 ablation extended to all 116 fleet units**, plus
bootstrap CIs on the rank and dispersion statistics, plus the cheap dose–response sweep on the
20-unit subset. Restructure around the §5 question; C4 becomes a corollary.
Experiments: one (Class C, existing frozen code; Phase 2D already proved 116-unit runs).
Compute: ~5× the Phase 2D fleet run — hours to a day of wall time, embarrassingly parallel.
Time: **1.5–2.5 weeks total.**
Novelty **62** · Impact **68** · Reviewer resistance **low–moderate** · Ceiling **IPDPS MME,
CCGrid fallback, FGCS floor** · Acceptance improvement **+25–30 pp, and it changes which
venues are eligible at all.**
Why this is the recommendation: one run simultaneously resolves all three
acceptance-determining objections from §8, converts the strongest finding from suggestive to
statistically defensible, and requires no new data, no new infrastructure, and no new method.

### VERSION 3 — AMBITIOUS
**Changes:** Version 2 plus M100 native-regime identification and the cross-machine
sensitivity comparison over the overlapping degradation range; optionally the staleness axis.
Experiments: two–three. Time: **4–6 weeks**, i.e. consuming essentially the whole window.
Novelty **70** · Impact **76** · Reviewer resistance low · Ceiling IPDPS MME with a stronger
case · Acceptance improvement **+30–35 pp**.
**What makes it risky:** it puts the 8 October deadline at genuine risk for a marginal gain
over Version 2; the cross-machine comparison introduces confounds (22C vs 16C sockets, 6 vs 4
GPUs, direct-water vs RDHx cooling, one month of M100 data) that Version 2 does not have; and
if M100 returns an ambiguous result, the temptation will be to narrate it post-hoc.
**Do Version 2 first and completely. Add M100 only if the 116-unit run is finished and written
up by mid-September.**

---

## 12. Highest-ROI single change

> **Run the existing, frozen F0–F4 identification across all 116 fleet units instead of the
> 20-unit subset, and report per-unit paired outcomes: the distribution of per-unit degradation
> ratios, the rank correlation ρ_s(τ_F0, τ_Fk) per condition, and the change in dispersion
> reported in both τ and α.**

Why this and nothing else:

- **Novelty.** It is the only change that moves the paper off "errors-in-variables on a new
  dataset." Classical theory predicts that measurement error attenuates an estimator and
  inflates apparent between-unit variance. It does not predict that spatial aggregation
  destroys the *ordering* of a fleet (ρ_s ≈ 0.44) while downsampling preserves it (ρ_s ≈ 0.96).
  That contrast is a new empirical fact about a real system, and it is invisible in the medians
  the manuscript currently reports.
- **Impact.** If it holds at n=116, the operational conclusion is sharp and actionable: under
  single-sensor (hottest-core) telemetry — which is what Marconi100 and many facilities
  natively record — *ranking nodes by fitted thermal parameter is not valid*, and no bias
  correction fixes it, because the damage is to order rather than to scale.
- **Feasibility.** Zero new data, zero new code, zero new method. The 116-unit path already
  exists and ran in Phase 2D; the F0–F4 conditions already exist in Phase 2B. This is the two
  being composed.
- **Reviewer survivability.** It is the single change that answers all three
  acceptance-determining objections at once: R1's "why only 20 units," R5's "this is textbook,"
  and — via the accompanying α-space table — R2's "your dispersion result is a transform
  artifact."

The honest caveat, which must be stated in the paper rather than discovered by a reviewer: at
n = 20 the rank effect has a bootstrap 95% CI of [−0.06, 0.80] and **cannot currently be
claimed**. The entire value of this change is that it converts a striking-but-unpublishable
observation into a defensible one. If the effect evaporates at n = 116, that is a genuine and
publishable negative — and the paper still has C4, the per-unit ratio dispersion, and the
α-space methodological caution, so Version 2 has no downside branch.

---

## 13. Final scores

| Dimension | Current | Potential after Version 2 | Basis |
|---|---|---|---|
| **Novelty** | **38** | **62** | Currently one comparison (C4) on known mechanisms. After: a population-structure result that errors-in-variables does not predict, plus a degradation-mode taxonomy, plus a self-critical parameterization caution. |
| **Impact** | **40** | **68** | Currently a caution. After: an actionable invalidation of cross-unit thermal comparison under single-sensor telemetry, which is a common configuration. |
| **Feasibility** | **85** | **80** | Currently near-complete. Slight decrease reflects one added run and a restructure inside a fixed window. |
| **Publishability** | **62** | **78** | Currently journal-grade. After: IPDPS MME becomes a real shot with CCGrid as a soft landing and FGCS as a guaranteed floor. |

### Best scientific positioning
Position this as a study of **apparent heterogeneity**, not of parameter bias. The field
already accepts that coarse measurement biases an estimator; what it has not been shown is
that a telemetry choice can restructure how an entire fleet *appears* — compressing the
dispersion between units and, under single-sensor aggregation, scrambling which units look
fast or slow — by more than the real hardware differences between those units. That reframing
costs nothing, uses data already computed, subsumes the current C4 headline as a corollary, and
is the only available framing that answers the "textbook" objection rather than conceding it.

### Best finished-product form
An empirical study with a reproducible artifact, not a framework, benchmark, or tool. What a
researcher receives: a quantified account of how three telemetry degradations distort a
116-socket fleet's apparent thermal structure in three qualitatively different ways; two
simple, unbranded diagnostics (rank preservation across regimes; artifact size in units of
fleet IQR) they can apply to their own facility before comparing nodes; and a one-command
reproduction path. Nothing about that requires shipping software as a contribution, and
claiming otherwise would weaken it.

### Best upgrade
One run of frozen code over 116 units instead of 20, analysed per-unit and paired. It is the
rare change that raises novelty and impact while *reducing* reviewer risk, because the same
result that makes the paper interesting is also the answer to the three objections most likely
to sink it. Everything else on the Class A list is free and should be done alongside it; the
M100 extension should follow only if this is finished and written by mid-September.

### Biggest trap
Two, and they pull in opposite directions. The first is **branding**: inventing named metrics
(MDI, stability indices, adequacy thresholds) and calling `src/alignment/` a framework, in the
hope that vocabulary substitutes for novelty. Reviewers read that as compensation, and it would
convert a modest, credible paper into an overclaiming one. The second is **the τ trap** — the
one this audit walked into and caught in §1.3. Reporting dispersion in a nonlinear
reparameterization manufactured a 6× "homogenization" effect for quantization that reverses to
a 2× expansion in α. Any claim about population spread must be shown in both parameterizations
or restricted to rank statistics. Publishing the τ-space version unchecked would have been the
single most damaging error available to this project.

---

FINAL RECOMMENDATION:
EXTEND

HIGHEST-ROI CHANGE:
Run the existing frozen F0–F4 ablation across all 116 fleet units instead of the 20-unit subset, and report per-unit paired outcomes — the distribution of per-unit degradation ratios, the rank correlation ρ_s(τ_F0, τ_Fk) per condition, and the dispersion change in both τ and α. One run of existing code, no new data, and it simultaneously answers the three objections most likely to determine acceptance.

EXPECTED NOVELTY:
62/100

EXPECTED IMPACT:
68/100

EXPECTED PUBLISHABILITY:
78/100
