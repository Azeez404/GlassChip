# FINAL SUBMISSION STRATEGY

Audit date: 2026-08-23. Supersedes the previous 1–2-day-horizon version of this file.
Target window: September–October 2026. Strategic only — no numbers re-validated (Phase 3B
44/44 accepted as given), no manuscript/figure/table/artifact/source modification, no commits.

---

## 1. What this paper actually is

**Question.** Compact thermal models of HPC nodes are identified from the machine's own
telemetry. That telemetry has a *quality* — resolution, rate, spatial aggregation — which is
a property of the instrumentation, not the hardware. Is the identified parameter a property
of the machine, or of the meter?

**Intervention.** Degradation of the *measurements only*, on fixed hardware and workload:
F1 = 1 °C quantization, F2 = 10 s→20 s decimation, F3 = hottest-core proxy, F4 = all three.
F0 is the reference regime.

**Dependent variable.** Identified effective τ = −Δt/ln α from a frozen first-order ARX.
Secondary: analytic vs block-bootstrap CI width; out-of-sample residual R²; online rolling-τ
alert rate.

**Strongest result (C4).** The quantized estimate (~116 s) falls below the minimum (~205 s)
of the full-quality distribution across all 116 sampled host-sockets.

**Weakest results.** §7.7 (online rolling-τ null against no labels) and §7.4 (residual
prediction null). Both honest, both thin, both add attack surface.

**Genuinely distinctive.** One thing: sizing a known measurement bias against an empirically
measured heterogeneity distribution from the same system.

**Established prior art / known principles demonstrated.** Everything else — quantization
biases LS estimates (errors-in-variables), analytic i.i.d. CIs understate variance under
dependence (Künsch), identifiability ≠ predictability, and HPC node thermal ID under 1 °C
quantization (Bartolini group). The manuscript concedes all of this correctly.

**Community.** HPC facility operations and operational data analytics (OLCF, CINECA, LRZ,
Sandia), datacenter thermal modelling, thermal digital-twin calibration. Not ML. Not
control-theoretic system ID.

**What the paper is today.** A competent, honest, highly reproducible single-machine
empirical study whose entire novelty rests on one comparison, with two structural weaknesses
a reviewer will find immediately: **one machine**, and **one-point-per-axis simulated
degradation with no dose–response**.

**What it could become by October — and this is the finding of this audit.** The repository
already contains everything needed to remove both structural weaknesses at once, and I did
not know this when writing the previous version of this file.

---

## 2. What this research could become

### 2.1 The decisive discovery in the repository

Three facts, verified directly against the working tree and against publisher/vendor sources:

1. **`src/alignment/` (1,180 LOC with tests) targets M100, not Summit.** `AsofAligner`,
   `HeterogeneousTimeSeriesBuilder`, and `FleetDriver` are built and tested against the M100
   ExaData record: causal backward as-of matching, per-metric staleness bounds, explicit
   missingness flags, native-interval estimation, nothing interpolated or fabricated.
2. **M100 data is on disk now** — `data/raw/21-03/` (1.2 GB, March 2021), five plugins,
   104 IPMI metrics, and a locked, working loader (`src/loader/`).
3. **M100's native measurement regime *is* Summit's F4 condition.** Verified by direct
   inspection of the raw Parquet: `p0_core0_temp` is **int32 (1 °C quantized), 20 s sampling
   (dt median/p05/p95 all 20.0 s), single-core rather than socket-mean**. `p0_power` is
   likewise int32 at 20 s. Ganglia metrics sit at ~60 s and ~90 s.

And the fact that makes the comparison scientifically defensible rather than confounded:

4. **Both machines are the same IBM node platform.** Summit is IBM AC922 (2× POWER9 22C,
   6× V100); Marconi100 is IBM Power System AC922 (2× POWER9 16C, 4× V100)
   [TOP500 system record; CINECA hardware page]. Same vendor, same node family, same CPU
   architecture. What differs is core count, GPU count, cooling (Summit direct water; M100
   RDHx liquid loop with recorded ambient), facility, workload mix, and — the variable of
   interest — **the measurement pipeline**.

**Consequence.** Summit F4 is not an arbitrary synthetic perturbation. It is a *simulation of
a real, deployed measurement regime that exists on a near-identical machine*, and the data to
test that simulation is already local. The project has, without apparently intending to,
assembled a natural experiment.

### 2.2 Testing each proposed direction against the evidence

**A. Broader measurement-quality study (jitter, missingness, staleness, sensor heterogeneity).**
Partly supported. The alignment module makes staleness and missingness *measurable* axes on
M100, which no HPC thermal-ID paper appears to treat as an identification variable. But
adding six axes to one machine multiplies claims without adding external validity. **Verdict:
one new axis at most, and only if it comes free with the M100 work.**

**B. A thermal-identification benchmark.** Not supported, and the Critic is right about why:
two datasets and a handful of obvious perturbations is a wrapper, not a benchmark. Benchmarks
earn citations through adoption, and adoption requires a community already competing on the
task. No such community exists here. **Verdict: DO NOT. Ship the degradation harness as a
reproducibility artifact, not as a claimed contribution.**

**C. Heterogeneous-sampling alignment pipeline as the contribution.** Not supported *as
software*. `AsofAligner` is good engineering, but "we wrote a careful as-of join" is not a
research contribution — as-of joins are standard in every time-series library. **It becomes
research only if an experiment shows that the alignment choice measurably biases an
identified parameter**, i.e. staleness bound → τ bias. That experiment does not exist yet.
**Verdict: the pipeline is an enabler and an artifact, not the headline. Its one research-
grade use is as a degradation axis.**

**D. Measurement uncertainty vs real heterogeneity — "when does a measurement artifact become
indistinguishable from a real hardware difference?"** Strongly supported and already
half-done. This is C4 generalised, and it is the most interesting question in the project.
**Verdict: this is the thesis. Promote it from a result to the organising question.**

**E. Identification vs prediction.** Supported as a *subsidiary* null, not as a headline.
Establishing it convincingly would need multiple model classes across multiple systems — a
separate paper. **Verdict: keep as one section, do not expand.**

**F. Digital-twin calibration.** Motivation only. No twin exists. **Verdict: cite as
why-it-matters, never claim.**

**G. Measurement-quality-aware SciML.** Repackaging. The PINN produced nothing; an ML framing
recruits reviewers who reject on method novelty. **Verdict: DO NOT.**

### 2.3 The one extension worth doing

Not "replicate on M100" — a naïve cross-machine comparison of τ *levels* is confounded by
core count, GPU count, cooling, and workload, and the Critic would be right to kill it.

The defensible version compares **sensitivities, not levels**:

> Measure dτ/d(measurement quality) — the *gradient* of identified τ with respect to
> quantization step and sampling interval — independently on Summit and on M100, and ask
> whether the measurement-sensitivity of thermal identification is a reproducible property of
> POWER9/AC922 thermal identification or an artifact of one facility's data.

A sensitivity is a within-machine derivative. Cross-machine comparison of within-machine
derivatives is robust to exactly the confounds (core count, cooling, workload, ambient) that
destroy a comparison of levels. This single reframing:

- takes the study from n=1 machine to n=2, killing the external-validity objection;
- **makes the dose–response sweep necessary rather than optional** — it is the object being
  compared — which kills the one-point-ablation objection with the same experiment;
- converts F4 from "a synthetic corner" into "a prediction about a real deployed regime that
  we then test";
- and produces a publishable result under **either** outcome:
  - *concordant gradients* → measurement-degradation simulation is a validated tool, and
    thermal parameters identified from M100-class telemetry (i.e. much of the published
    CINECA thermal-ID literature) carry a quantifiable, estimable regime bias;
  - *discordant gradients* → you cannot emulate a coarse measurement regime by degrading a
    fine one, which is a sharper and more surprising cautionary result than the current paper's.

Two-outcome-publishable is the property that makes this worth 6 weeks of a student's time.

---

## 3. Three-persona debate

### Round 1 — Dreamer proposes

"Measurement-Regime Sensitivity of Thermal System Identification: A Two-Machine Study." Add
the staleness axis from `src/alignment/`, the missingness axis, a full 4×4 degradation grid on
both machines, an identifiability-envelope derivation, and release it as a benchmark with a
leaderboard. Target SC27 or TPDS.

### Round 2 — Practical Researcher cuts

| Idea | Class |
|---|---|
| Cross-machine **sensitivity** comparison (Summit vs M100) | **HIGH VALUE / MEDIUM COST** — data local, loader locked, aligner built and tested, identification code frozen and reusable. ~2–3 weeks. |
| Quantization + decimation dose–response sweep (both machines) | **HIGH VALUE / LOW COST** — same pipeline, more parameter values. It *is* the sensitivity measurement. ~4–6 days incl. re-validation. |
| Staleness/missingness axis via `AsofAligner` (M100 only) | **HIGH VALUE / MEDIUM COST**, but scope risk. It is the only genuinely unstudied axis, and it is the one thing that turns the alignment module from software into research. **Include only if the sensitivity study lands by mid-September.** |
| Full 4×4 grid on both machines | LOW VALUE / HIGH COST — combinatorics without added inference. |
| Identifiability envelope (synthetic ground truth) | HIGH VALUE / HIGH COST — 2+ weeks, and it is a different paper. **Defer.** |
| Benchmark + leaderboard | **DO NOT DO** — no competing community; pure wrapper risk. |
| SciML / PINN reframing | **DO NOT DO.** |
| Digital-twin claim | **DO NOT DO.** |
| SC27 / TPDS target | **DO NOT DO** — novelty still insufficient even upgraded. |

Achievable product by October: **the current paper + cross-machine sensitivity + dose–response,
in 10 pages, double-anonymous.**

### Round 3 — Critic attacks the survivor

1. **Confounds are not eliminated, only reduced.** 22C vs 16C sockets, 6 vs 4 GPUs, direct
   water vs RDHx, different workload mixes, and M100 has variable recorded ambient where
   Summit effectively does not. If the gradients disagree, you cannot tell me whether the
   degradation model failed or the machines differ. **This is the central scientific risk and
   it is real.**
2. **You cannot measure Summit's F0-equivalent on M100.** M100 has no fine-grained regime —
   you can only degrade *further* (2 °C, 40 s). So the two gradients are measured over
   different, non-overlapping segments of the degradation axis. Comparing them assumes local
   linearity you have not established.
3. **Single month of M100 data (March 2021)** against Summit's multi-month coverage. Seasonal
   and workload-mix differences are unaddressed.
4. **The alignment module is standard.** As-of joins with staleness bounds exist in pandas,
   kdb+, and every market-data stack. Presenting it as novel invites contempt.
5. **F2 remains unexplained** in the current manuscript. For a true first-order process τ is
   invariant to decimation; 394→910 s says the process is not first-order and F0 is not ground
   truth. Unaddressed, this undermines the whole reference regime.
6. **"Fleet" still means 116 of 9,252 sockets.**
7. **Two nulls still padding.**

**"What would force me to accept this?"** Three things: (a) the gradients are compared over an
*overlapping* degradation range, not extrapolated; (b) the ambient covariate is used, not
ignored, since M100 measures it; (c) the paper states in advance what concordance and
discordance would each mean, so it cannot be accused of post-hoc narration.

### Round 4 — Dreamer repairs, without inventing evidence

Objection 2 is the sharpest and it is answerable with the data in hand: **Summit can be
degraded *into and past* M100's native regime.** Summit at (1 °C, 20 s, single-core) = F4 is
M100's native point. Degrade Summit further to (2 °C, 40 s) and degrade M100 to (2 °C, 40 s)
as well, and the two machines now share an **overlapping degradation range** — [1 °C→2 °C,
20 s→40 s] — over which both gradients are measured directly rather than extrapolated. That
is the experiment. It resolves objection 2 completely and costs no extra data.

Objections 1 and 3 are mitigated, not eliminated: include ambient as a covariate on M100
(it is recorded at 20 s), stratify by workload regime using the power signal, and state the
residual confounds plainly. Objections 5, 6, 7 are prose fixes already on the must-fix list.

### Round 5 — Practical Researcher reduces to what fits

Overlapping-range design confirmed as the plan. Staleness axis demoted to optional. Ambient
covariate: include as a reported stratification, not as a structural model change (changing
the model order or regressor set would unfreeze V1 and invalidate locked artifacts — do not).
Single-month M100 limitation: state it, do not fix it.

### Round 6 — Critic's final rejection case

"Two supercomputers of the same vendor family, one month of data on one of them, a first-order
model that the authors' own F2 result shows is misspecified, and a conclusion that coarse
telemetry biases fitted parameters — which errors-in-variables theory already predicts. The
contribution is that the *magnitude* is measurable and reproducible across facilities. That is
a real but modest contribution, appropriate for a measurements track or a systems journal, not
for a top-tier conference."

**Converged.** All three accept that characterisation. It is accurate, and it is enough.

### Convergence

**Strongest contribution that can be honestly built:**
> The sensitivity of identified thermal parameters to measurement quality is itself
> measurable, and — over an overlapping degradation range on two IBM AC922/POWER9
> supercomputers with independent telemetry pipelines — we report whether that sensitivity
> reproduces across facilities. On Summit the induced shift exceeds the natural spread across
> all 116 sampled host-sockets, establishing that a telemetry choice can bias a fitted thermal
> parameter beyond real unit-to-unit variation.

**Must absolutely NOT claim:**
> That τ is physical, or that F0 is ground truth. That the machines are equivalent, or that any
> cross-machine difference in *level* is attributable to measurement. That the degradation
> model is validated in general (only over the tested range). That the alignment module is
> methodologically novel. That the residual is unpredictable, or that τ has been evaluated as
> a monitor. That this constitutes a benchmark, a framework, or a digital twin.

---

## 4. Finished-product test

October 2026. Repo + paper. A researcher finds it. Why would they care?

| Would they… | Today | After the extension |
|---|---|---|
| **Learn something from the empirical result** | Maybe — one striking number from one machine | **Yes** — "measurement-regime bias is reproducible across facilities, and here is its magnitude" is a fact operators can act on |
| **Cite it** | Occasionally, as a caution footnote | **Yes** — anyone identifying thermal models from M100 or Summit telemetry now has to cite the bias estimate, and the CINECA thermal-ID line is directly implicated |
| **Compare against it** | No | Only weakly — there is no task to beat |
| **Reproduce it** | Yes — this is already a genuine strength (frozen model, seeds, raw hash, one-command regeneration) | Yes, and now on two public datasets |
| **Extend it** | Unlikely | **Yes** — the degradation harness applied to a third machine is an obvious follow-up, and the staleness axis is left explicitly open |
| **Use the benchmark** | n/a | **No — and do not build one.** |
| **Use the alignment pipeline** | Unlikely | **Plausibly yes**, but only as a by-product: anyone joining EXAMON IPMI (20 s) to Ganglia (60/90 s) faces this exact problem, and a tested, staleness-bounded, non-fabricating aligner with a report is genuinely reusable. Ship it, document it, do not claim it. |

**Minimum finished product that makes the answers "yes":** the current manuscript, plus the
overlapping-range two-machine sensitivity result, plus the four prose must-fixes, plus a
tagged, documented repo release containing the degradation harness and the aligner. Nothing
else.

---

## 5. Novelty score

Scored for the **October product** (the two-machine sensitivity study), with the
current-manuscript score in parentheses where it differs.

| # | Dimension | /10 | Class | Justification |
|---|---|---|---|---|
| 1 | Problem novelty | 6 (5) | CONTEXTUAL | "Is the parameter a property of the machine or the meter?" is under-asked in HPC; standard in metrology. Reframing to *sensitivity* sharpens it. |
| 2 | Method novelty | 3 (2) | KNOWN | Frozen ARX + OLS + delta method + block bootstrap. The only methodological move is measuring a gradient over an overlapping range — good design, not new method. |
| 3 | Experimental-design novelty | 8 (6) | **STRONG** | The overlapping-degradation-range two-machine natural experiment is a genuinely good design and the strongest thing in the project. |
| 4 | Empirical-result novelty | 6 (5) | DISTINCTIVE | Cross-facility reproducibility (or failure) of measurement sensitivity is a new empirical fact either way. |
| 5 | Dataset/context novelty | 5 (4) | CONTEXTUAL | Two public datasets, neither new; the pairing (same AC922 platform, independent telemetry pipelines) is the novel part. |
| 6 | Comparative novelty | 7 (7) | DISTINCTIVE | Artifact-vs-heterogeneity sizing remains the core; no direct prior art found. |
| 7 | Practical significance | 7 (6) | DISTINCTIVE | Directly actionable, and now implicates a real body of published M100-derived thermal work. |
| 8 | Generalizability | 5 (3) | CONTEXTUAL | Two machines, same vendor family, one month on one of them. Better than n=1; still not general. |
| 9 | Literature-gap strength | 5 (5) | CONTEXTUAL | Still a gap in *combination*; each ingredient remains prior art. |
| 10 | Overall publishability novelty | 6 (5) | CONTEXTUAL | Comfortable for a measurements track or a good systems journal; short of a flagship. |

- **Raw novelty: 58/100** (current manuscript: 48)
- **Conservative novelty: 52/100** (current manuscript: 38)
- **Venue-adjusted:** ~75/100 for IPDPS *Measurements, Modeling, and Experiments* /
  CCGrid / FGCS-class; ~20/100 for SC main track or TPDS; ~10/100 for any ML venue.

> **Novel enough to publish somewhere?** **Yes — and after the extension, comfortably, with a
> real shot at a respectable conference rather than only a journal.**
>
> **Novel enough for a flagship ML/AI venue?** **No.** Not now, not in October, not with any
> honest amount of additional work in this window. These are not the same question and the
> project should stop treating flagship venues as the reference point.

---

## 6. Prior-art stress test (live, independent of Phase 3C)

Searched 2018–2026 across HPC thermal ID, quantized system ID, sampling/temporal-resolution
effects, measurement-induced parameter bias, fleet thermal heterogeneity, thermal digital
twins, identification-vs-prediction, Summit and M100 datasets, thermal anomaly detection, and
empirical-limits/reproducibility studies — including conceptual (not keyword) searches for
degradation-induced parameters moving into or below natural fleet variation, and for
validation of simulated sensor degradation against genuinely coarse real measurements.

| Work | Class | Effect |
|---|---|---|
| Bartolini group — HPC node thermal model ID under 1 °C quantization, in-production, free cooling (IEEE Xplore 8863115; 7793664; arXiv:1810.01865) | **PARTIAL OVERLAP — closest prior art, and now directly implicated** | They *overcome* quantization to obtain an accurate model on CINECA-class machines; you *measure the bias it induces* on the same class of machine. The extension makes this relationship pointed rather than adjacent: your M100 result estimates the regime bias carried by parameters identified the way they identify them. State the distinction in one sentence in §1 or a reviewer collapses the two. |
| Ellis, Shin, Karimi, Oles, Dash, Wang — SC'21, *Revealing power, energy and thermal dynamics of a 200PF pre-exascale supercomputer* (10.1145/3458817.3476188) | **PARTIAL OVERLAP — still uncited; still a visible hole** | The canonical characterisation paper for your exact system and data, by your dataset's authors. Characterises fleet-scale power/thermal behaviour; does not identify models or vary measurement quality. Cite it. |
| Borghesi et al., *M100 ExaData*, Scientific Data 10:288 (10.1038/s41597-023-02174-3) | SUPPORTING PRIOR ART | Becomes a primary dataset citation rather than background context once the extension lands. Confirms 980+ nodes, 2020-03-09→2022-09-28, EXAMON, RDHx liquid cooling. |
| Quantized-observation system ID (Wang/Yin/Zhao; *Automatica* 2008; arXiv:1804.10015) | SUPPORTING PRIOR ART | Owns the mechanism. Already conceded in §3.3 — correct. |
| Künsch 1989 / Liu–Singh 1992 | SUPPORTING PRIOR ART | Owns the uncertainty method. Conceded in §3.4. |
| *Exploring the Utility of Graph Methods in HPC Thermal Modeling*, ICPE 2024 Companion (10.1145/3629527.3652895) | DIFFERENT PROBLEM | Different modelling approach, no measurement-quality axis. Useful as evidence that HPC thermal modelling is live at ICPE — a venue signal. |
| *Toward Data Center Digital Twins via Knowledge-based Model Calibration and Reduction*, ACM TOMACS (10.1145/3604283) | DIFFERENT PROBLEM | Motivation for §10. TOMACS itself expects simulation methodology this work does not have. |
| Tier-0 datacenter room thermal characterization (10.1007/978-3-030-67077-1_1); variability/heterogeneity in green supercomputing | SUPPORTING PRIOR ART | Support the *denominator* of C4 — that node-to-node thermal heterogeneity is real and measurable. Cite one. |
| Molan et al., RUAD (FGCS 2023); rule-based thermal anomaly detection (ISC-W 2022, 10.1007/978-3-031-23220-6_18) | DIFFERENT PROBLEM | Detection, not identification. Relevant only to §7.7. Venue signal for FGCS. |
| Sensor-simulation validation / domain-gap literature (autonomous driving, computational imaging) | **DIFFERENT PROBLEM — but methodologically load-bearing** | Validating a simulated degradation model against genuinely degraded real data is an established methodological standard in those communities and is **absent from HPC telemetry modelling**. This is the strongest available justification for the extension, and it is a citable framing rather than a claimed contribution. |

**Direct overlap: none found**, for either the current claim or the extension. Nothing was
found that (a) benchmarks a measurement-induced parameter shift against a same-system
population, or (b) validates a telemetry-degradation model against a second machine that
natively occupies the degraded regime.

**Residual novelty risk, stated honestly:** C4's novelty rests entirely on the
artifact-vs-heterogeneity *comparison*, not on the ablation. A reviewer who declines to credit
that comparison scores the paper at ~25/100 regardless of the extension. The extension's value
is that it adds a *second* independent load-bearing result, so the paper no longer has a single
point of failure.

---

## 7. Venue landscape for a September–October 2026 submission

Deadlines checked live 2026-08-23 against official conference pages. Acceptance rates omitted
throughout — none could be established from an official source, and inventing them is worse
than omitting them.

| Venue | Fit | Novelty expectation | Current readiness | October readiness | Required changes | Difficulty | Recommendation |
|---|---|---|---|---|---|---|---|
| **IPDPS 2027** — *Measurements, Modeling, and Experiments* track. Abstract **1 Oct 2026**, paper **8 Oct 2026** (firm, no extensions), 10 pp double-column, **double-anonymous, two-round**, Seattle 1–5 Jun 2027 | **Strong.** The track explicitly covers performance evaluation, energy/power/accuracy metrics, and experimental studies | High for the conference; the Measurements track is the most receptive entry point | Low | **High, if the extension lands** | Extension + all must-fixes + anonymisation | High | **TARGET.** The deadline falls exactly in the window and the track is purpose-built for this class of work. Competitive, but the abstract costs nothing and the two-round review returns usable feedback. |
| **CCGrid 2027** — Dallas–Fort Worth; abstract **24 Nov 2026**, paper **1 Dec 2026**, 10 pp IEEE | Good (cluster/grid systems; empirical studies welcome) | Moderate–high | Low | High | Same package, de-anonymised as required | Moderate–high | **PRE-COMMITTED FALLBACK.** Eight weeks after IPDPS — reviews in hand, near-zero rework. This sequencing is strictly dominant; commit to it now. |
| **FGCS (Elsevier)** — rolling | Strong. HPC monitoring/analytics/thermal; the CINECA/RUAD line publishes here, so the reviewer pool is the right one and already appears in the related work | Moderate | **Already adequate** | High | Must-fixes only | Moderate | **FLOOR — and this is what makes the whole strategy safe.** The current manuscript is submittable here today. Hold it in reserve; do not submit while pursuing IPDPS. |
| **JPDC (Elsevier)** — rolling | Good. Broad DC/HPC systems | Moderate | Adequate | High | Must-fixes only | Moderate | **Interchangeable with FGCS.** Pick one; they are not simultaneously submittable. |
| **ICPE 2027** (ACM/SPEC) — icpe2027.spec.org; **2027 deadline not yet announced** at time of audit; ICPE 2026 research abstracts were 3 Nov 2025, so a comparable Nov 2026 date is plausible but **unverified — do not plan around it** | Good — performance measurement and experimental evaluation, and HPC thermal modelling has appeared there | Moderate | Low | High | Extension | Moderate | **POSSIBLE.** Check the site in September; treat as a third option, not a plan. |
| **HPC-ODA @ SC 2027 / HPCMASPA @ Cluster 2027** | **Best topical fit that exists** — HPC-ODA's CFP scope reads like a description of this paper | Low–moderate | High | High | Must-fixes; compress to 8 pp | Low | **SAFE WORKSHOP OPTION**, but SC26 closed 12 Aug 2026 and 2027 deadlines are ~11 months out. Only relevant if IPDPS *and* CCGrid both fail. |
| **Cluster Computing / J. Supercomputing (Springer)** — rolling | Adequate | Lower | Adequate | High | Must-fixes | Low–moderate | **FALLBACK below FGCS.** |
| **SC 2027 main track / IEEE TPDS** | Topic fine, novelty short | High | Very low | Low | Structural — would need a third machine and a method contribution | Very high | **DO NOT SUBMIT.** |
| **ACM TOMACS** | Weak | High (simulation methodology) | Very low | Low | Would need the identifiability envelope | High | **DO NOT SUBMIT** in this window. |
| **HPDC / ICS / PPoPP** | Poor scope fit (systems software, programming models) | Very high | Very low | Very low | n/a | Very high | **DO NOT SUBMIT.** |
| **Any ML/SciML venue** | None | Very high method novelty | n/a | n/a | Would require an actual method | Very high | **DO NOT SUBMIT.** The PINN is a discarded baseline. |
| **Negative-results / reproducibility venues** | Partial | Low | High | High | — | Low | **DO NOT PRIORITISE** — mis-frames the paper and buries C4 beneath the two nulls. |

---

## 8. September–October strategy

The plan is three experiments and four prose fixes. Nothing else. If it slips, the FGCS floor
absorbs the failure.

### NOW → mid-September: build the extension

**E1 — Dose–response sweep on Summit (essential).**
Quantization ∈ {0.25, 0.5, 1.0, 2.0} °C × decimation ∈ {10, 20, 40} s, on the existing 20-unit
subset, using the frozen identification code.
1. *Objection solved:* one-point-per-axis ablation (Critic #6 in every review of this paper).
2. *Acceptance impact:* +8–12 pp on its own; **prerequisite** for E2, so its real value is
   larger. 3. *Time:* 4–6 days incl. re-validation. 4. *Compute:* trivial — same pipeline, more
   parameter values. 5. *Scientific value:* converts a point estimate into a measured gradient.
6. **Necessary? YES.**

**E2 — M100 sensitivity replication over the overlapping range (essential — this is the paper).**
Identify τ on M100 at native (1 °C, 20 s, single-core), then degrade to (2 °C, 40 s). Compare
the M100 gradient with the Summit gradient measured over the *same* [1→2 °C, 20→40 s] segment
from E1. Report ambient-stratified results since M100 records ambient at 20 s. Use the locked
loader; use `AsofAligner` only where metric rates actually differ.
1. *Objections solved:* single-machine external validity; simulated-vs-real degradation; and
   Critic's "you extrapolated" objection, via the overlapping range. 2. *Acceptance impact:*
   +15–20 pp, and it is what moves the paper from journal-only to conference-viable.
3. *Time:* 2–3 weeks. 4. *Compute:* moderate — 1.2 GB local, per-node independent, embarrassingly
   parallel. 5. *Scientific value:* highest in the project; publishable under either outcome.
6. **Necessary? YES.**

**E3 — Staleness/missingness axis via `AsofAligner` (optional, M100 only).**
Vary the per-metric staleness bound and measure the induced τ bias.
1. *Objection solved:* none currently raised — this is offence, not defence. It is the only
   genuinely unstudied degradation axis and the only thing that makes the alignment module
   research rather than software. 2. *Acceptance impact:* +3–5 pp; higher if a reviewer asks
   what the alignment code is for. 3. *Time:* 4–5 days. 4. *Compute:* low. 5. *Scientific value:*
   real but secondary. 6. **Necessary? NO — gate it on E2 completing by 15 September.**

**Not worth doing:**
- *Identifiability envelope on synthetic ground truth* — high value but 2+ weeks and it is a
  different paper. **Defer to the next cycle.**
- *Full 4×4×4 grid on both machines* — combinatorics without inference. **No.**
- *Third machine* — no data, no time. **No.**
- *Second-order ARX refit* — would unfreeze V1 and invalidate every locked artifact for a
  benefit the 150-word F2 explanation already captures. **No.**
- *Anything involving the PINN.* **No.**
- *Re-running Phase 3B–3D validation.* Already 44/44. **No.**
- *Building a benchmark, leaderboard, or "framework."* **No.**

### Mid-September → 8 October: finalise

Fold E1/E2 (and E3 if it landed) into the manuscript; apply the four must-fixes; restructure to
lead with sensitivity rather than with the F0–F4 table; compress to 10 pages; **anonymise for
IPDPS double-blind review** (a real task — the repo, the raw hash, and the phase naming all
leak identity, and the artifact link must be anonymised or withheld); register the abstract
1 Oct; submit 8 Oct. Tag a documented repo release.

Then hold. Do not submit anywhere else while IPDPS is under review. CCGrid opens 24 November
with reviews in hand.

---

## 9. Must-fix / Should-fix / Do-not-touch

### MUST FIX — genuine publication risks
1. **Resolve every [VERIFY] reference.** 12 of 15 entries carry it; arXiv:2607.28962 must be
   confirmed to exist as cited. Desk-reject and integrity risk. *3–5 h.*
2. **Stop calling 116 sockets "the fleet."** It is 58 hosts of 4,626 nodes. Use "the 116 sampled
   host-sockets," and restate C4 regime-relatively: *below the value this identification
   convention yields for every sampled unit.* *1 h — highest value-per-hour fix in the project.*
3. **Explain F2.** For a true first-order process τ is invariant to decimation; 394→910 s is
   evidence of unmodelled fast dynamics, so F0 is a *reference regime*, not ground truth.
   ~150 words. Currently the most exploitable hole; after the fix it becomes a finding — and
   the extension makes it *load-bearing*, because measuring a gradient presupposes knowing what
   the reference point means. *1–2 h.*
4. **Cite Ellis/Shin et al. SC'21**, and state in §4.1 that **the 1 Hz source is not in the
   public Summit release** (the package ships 10 s and 1 min means only — verified against the
   dataset companion site). Pre-empts "why not 1 Hz" and demonstrates command of the literature.
   *30 min.*

### SHOULD FIX — high value, not blockers
5. **Cut six contributions to four**, led by the sensitivity result, then C4, then C5, then C6.
6. **Report the artifact shift in units of sample spread** (shift ÷ IQR, ÷ σ) in §7.6/Table 4 —
   arithmetic on existing manifest numbers, no re-run. Turns an observation into a reusable diagnostic.
7. **One sentence separating this from the Bartolini line** — they overcome quantization, this
   measures its cost. Becomes more important, not less, once M100 is in the paper.
8. **Acknowledge T–P collinearity** (per-unit corr 0.94–0.98 in `derived_manifest.json`) as a
   conditioning caveat in §9.
9. **Halve §7.7/§8.6.** The online null costs more page-space and attack surface than its
   evidentiary weight justifies — and 10 pages will be tight.
10. **State the confounds of the M100 comparison explicitly and in advance** — 22C vs 16C, 6 vs
    4 GPUs, direct-water vs RDHx, one month vs multi-month, workload mix — together with a
    pre-stated reading of what concordance and discordance would each mean. Pre-registering the
    interpretation is what stops a reviewer calling the conclusion post-hoc.

### DO NOT TOUCH
- The frozen ARX, the τ definition, the −Δt/ln α convention, the model order, and the regressor
  set. Changing any of these unfreezes V1 and invalidates every locked artifact for no gain.
- **§9 Threats to Validity and the forbidden-claims discipline.** This is the project's single
  strongest asset with a hostile reviewer. Do not soften it to sound more confident.
- The bootstrap methodology, block length, and seeds.
- The permutation null and the chronological out-of-sample protocol.
- The 44/44 validated numbers, figures, tables, and the reproducibility pipeline.
- The decision not to present the PINN as a contribution.
- The locked loader and the frozen V1 preprocessor. `src/alignment/` is correctly additive —
  keep it that way.

---

## 10. Final paper identity

**Identity sentence.**
> This is primarily an empirical HPC measurement-quality study: it measures how strongly the
> resolution and sampling rate of a supercomputer's own thermal telemetry bias the thermal
> model identified from it, sizes that bias against the natural variation across units of the
> same machine, and tests whether that sensitivity reproduces on a second supercomputer of the
> same node architecture whose telemetry pipeline natively occupies the degraded regime.

**Elevator pitch (3 sentences).**
> Thermal models of supercomputer nodes are fitted to the machine's own telemetry, and that
> telemetry is coarse — rounded to whole degrees, sampled every 10–20 s, averaged over sensors.
> Degrading only the measurements on Summit, with hardware and workload fixed, moves the
> identified thermal response time by up to a factor of eight, and the 1 °C-quantized estimate
> falls below the value obtained for every one of 116 sampled host-sockets at full resolution.
> Because Marconi100 — the same IBM AC922/POWER9 platform — natively measures in exactly that
> degraded regime, we can test whether this measurement sensitivity is a reproducible property
> of the identification problem or an artifact of one facility's data pipeline.

**Reviewer-facing contribution (4 bullets).**
- A controlled, same-hardware, same-workload measurement-quality ablation on real Summit
  telemetry, with a frozen first-order ARX used purely as a probe, extended to a dose–response
  gradient over quantization step and sampling interval.
- The measurement artifact sized against real heterogeneity: the quantization-induced estimate
  falls below the value the same identification convention yields for all 116 sampled
  host-sockets — the artifact exceeds the observed unit-to-unit spread.
- A two-machine test of that sensitivity over an overlapping degradation range on Summit and
  Marconi100 — the same IBM AC922/POWER9 platform with independent telemetry pipelines —
  establishing whether measurement-regime bias reproduces across facilities.
- Two honest boundaries: higher measurement quality does not materially improve out-of-sample
  residual prediction (R² ≤ 0.066 against a permutation null), and the effective response time,
  though cheap to compute online (~0.041 ms/window), does not separate out-of-sample behaviour
  from baseline variability as a standalone statistic.

**Mentor-facing explanation.**
> *What we built.* A pipeline that takes a supercomputer's own temperature and power logs,
> fits a small physics-flavoured model to them, and — this is the point — can deliberately
> degrade those logs first, in precisely controlled ways: round the temperature to whole
> degrees, read it half as often, use one hot core instead of the average. Everything is
> frozen and seeded, so every number regenerates from one command.
>
> *What we measured.* How much the fitted "thermal response time" changes when only the
> measurement changes and the machine does not.
>
> *What we discovered.* It changes a lot — up to eightfold. And after rounding to 1 °C, the
> fitted value came out lower than for any of the 116 real sockets measured properly. A logging
> setting distorted the answer more than genuine differences between physical hardware did.
>
> *Why it matters.* Facilities are calibrating thermal "digital twins" from exactly this kind
> of telemetry. If two sites log at different precision, their calibrated models are not
> comparable — and nothing in the statistics will warn them, because the confidence intervals
> stay narrow while the estimate moves.
>
> *What we are expanding it into.* We found that the second dataset already in this repository,
> Marconi100, is the same IBM node platform as Summit but records temperature natively as whole
> degrees every 20 seconds — which is exactly the degraded condition we were simulating. So we
> can now stop simulating and check: does our degradation model predict what a real coarse
> measurement pipeline actually does? We measure how *sensitive* the fitted parameter is to
> measurement quality on each machine separately, over a range both machines can reach, and
> compare the sensitivities rather than the raw values — which is what makes the comparison
> survive the fact that the two machines differ in cooling, core count, and workload. If the
> sensitivities agree, degradation simulation becomes a validated tool and a large body of
> published thermal parameters carries a bias we can now estimate. If they disagree, that is a
> sharper warning still: you cannot fake a coarse measurement pipeline by coarsening a fine one.
> Either answer is worth publishing, which is why it is worth the six weeks.

---

## 11. Final GO / NO-GO

**GREEN.** There is a strong, concrete publication path, and — unusually — a guaranteed floor
beneath it.

The verdict is GREEN rather than YELLOW for four specific reasons: the current manuscript is
*already* submittable to FGCS/JPDC today, so the downside is bounded; the decisive extension
requires no new data (M100 is on disk), no new infrastructure (the aligner is built and
tested), and no new method; the extension is publishable under either experimental outcome;
and a real deadline (IPDPS 2027, 8 October) falls exactly in the stated window with a
pre-committed fallback eight weeks later.

The direction is **not** RED, and **not** merely "publish as-is." Of the five options posed:
**option 2 — extend it into a stronger version of the same research — is correct**, with one
precisely identified extension (the overlapping-range two-machine sensitivity study) and an
explicit rejection of options 3 and 4. Do not build a benchmark. Do not sell the alignment
pipeline as the contribution. Do not context-switch.

The honest risk: E2 may return a messy or ambiguous result that confounds cannot resolve.
Mitigation is structural, not hopeful — the within-machine gradients are confound-free and
publishable on their own, the cross-machine comparison is framed as a test rather than a claim,
and the FGCS floor absorbs total failure of the extension.

| Score | /100 | Why |
|---|---|---|
| **Publishability** | **74** | Current manuscript is already journal-submittable; the extension opens a conference path. Ceiling set by method novelty near zero and by two machines of the same vendor family. |
| **Novelty** | **52** (conservative; 38 for the current manuscript) | Experimental design 8/10 carries it. Method novelty stays low by design, and correctly so. |
| **Technical quality** | **80** | Frozen model, block bootstrap, chronological OOS, permutation null, hashed raw data, seeds, one-command regeneration, 44/44 validated, and now a tested additive alignment layer that never fabricates values. Held below 90 by the still-unexplained F2 behaviour and the unaddressed T–P collinearity. |
| **Venue fit** | **82** | A purpose-built track (IPDPS *Measurements, Modeling, and Experiments*) with a deadline inside the window, a pre-committed fallback, and a rolling-journal floor. The targeting problem flagged in the previous audit is now solved. |
| **Reviewer risk** | **52** (higher = riskier) | Down from 58. The two structural objections (one machine, one-point ablation) are addressed by the extension; the confound objection replaces them but is weaker and is pre-empted by the sensitivity framing. Unverified references remain the largest avoidable risk. |
| **Confidence** | **80** | Manuscript, claims, manifest, alignment source, tests, and raw M100 Parquet inspected directly; M100's native 1 °C / 20 s / int32 regime and the shared AC922/POWER9 platform verified against the data and against TOP500/CINECA records; all venue deadlines checked live. Residual uncertainty is execution risk on E2 and reviewer-draw variance. |

---

FINAL VERDICT:
GREEN

BEST REALISTIC VENUE:
IPDPS 2027 — *Measurements, Modeling, and Experiments* track (abstract 1 Oct 2026, paper 8 Oct 2026, double-anonymous, 10 pp), with CCGrid 2027 (1 Dec 2026) as the pre-committed fallback and FGCS/JPDC as the rolling floor.

NOVELTY:
52/100

PUBLISHABILITY:
74/100

ONE THING WE MUST DO:
Run the M100 sensitivity replication over the overlapping degradation range — measure dτ/d(quantization, sampling interval) on Summit across [1→2 °C, 20→40 s] and on Marconi100 across the same range, and compare the two gradients rather than the two τ levels. The data is already on disk, the aligner is already built and tested, and both possible outcomes are publishable.
