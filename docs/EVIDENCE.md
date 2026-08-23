# Claim-to-Evidence Trail

Auditability record for GLASSCHIP-V2: every manuscript claim mapped to the artifact that
supports it, plus the numerical-consistency and artifact-inventory checks. Consolidated from
the separate claim-audit documents produced during analysis.


---

## Paper-level claim audit

*(source: `v2_research/paper/claims/paper_level_claim_audit.md`)*

## PHASE 3D — PAPER-LEVEL CLAIM AUDIT

Audit only. `manuscript.md` was not modified. Authoritative sources:
paper_results_manifest.json and the Phase 3C literature/novelty files.

### 1. Executive verdict

**GREEN.** Every substantive claim in Sections 1-11 is supported by the locked
artifacts or verified literature, correctly classified, numerically consistent
with the manifest (validator 44/44), worded no more strongly than the evidence
permits, aligned with the Phase 3C YELLOW novelty position, and free of
forbidden claims. No substantive correction is required. One optional wording
note (the word "causal" used in the signal-processing sense) is recorded below.

### 2. Claim inventory

| ID | Section | Class | Evidence | Status | Notes |
|---|---|---|---|---|---|
| C1 | 1 / 7.1 / 8.1 | V | 2B/2C; manifest tau_point, ratios | PASS | "identified effective parameter", not physical behaviour |
| C2 | 1 / 7.1 | V | 2B; 393.8->115.8 (0.29x) | PASS | quantization shift |
| C3 | 1 / 7.1 | V | 2B; 393.8->910.5 (2.31x) | PASS | downsampling shift |
| C4 | 7.2 / 8.3 | V | 2C; boot medians = points, 0% invalid | PASS | "not corrected by bootstrap" stated |
| C5 | 7.3 / 8.3 | V(+I) | 2C; analytic vs bootstrap CI; F1 tight+shifted | PASS | precision != accuracy framed as demonstration |
| C6 | 1 / 7.4 / 8.4 | V | 2A/2B; HGB<=0.066, null p95<0 | PASS | "not materially improve", never "unlearnable" |
| C7 | 7.4 | V | 2B; degraded >= F0 | PASS | prevents cleaner-than-data story |
| C8 | 7.5 / 8.5 | V | 2D; 116/116, 439/205/1200/2596 | PASS | fleet range |
| C9 | 1 / 7.6 / 8.2 | V | 2C+2D; 116 < 205 | PASS | STRONGEST; "empirical comparison", not causal |
| C10 | 7.5 / 8.5 | V | 2D; r=0.789, 24.2% | PASS | explicitly descriptive, no cause |
| C11 | 1 / 7.7 / 8.6 | V | 2E; 0.041 ms; OOS 0.102 ~ baseline 0.103 | PASS | "computable != useful" |
| C12 | 2.4 / 3.7 / 8.7 | I/L | novelty_verdict.md | PASS | "to the best of our reviewed literature" |
| C13 | 3.1 | L | P1-P5,P12,P13 | PASS | HPC thermal ID conceded as prior art |
| C14 | 3.3 | L | P6-P8 | PASS | quantization bias conceded as prior art |
| C15 | 3.4 | L | P9 (verified) | PASS | block bootstrap conceded as prior art |
| C16 | 3.5 | L | P10,P11 | PASS | identifiability!=prediction conceded as prior art |
| C17 | 4.x/5.x/6.x | (method) | frozen V1 + configs | PASS | methodological description, not empirical claim |
| C18 | 8.7 | I | novelty_verdict.md | PASS | contribution = controlled combination + C9 |

No DUPLICATE, UNSUPPORTED, or WEAKEN statuses. Method descriptions (Sections
4-6) assert no empirical result and are excluded from claim scoring.

### 3. Numerical consistency

Validator `validate_results.py`: **44/44 PASS, data_ok=True**. Manuscript values
cross-checked against the manifest:

| Quantity | Manuscript | Manifest | Result |
|---|---|---|---|
| tau F0/F1/F2/F3/F4 (point) | 394/116/910/283/352 | 393.8/115.8/910.5/282.6/352.0 | PASS |
| ratios | 1.00/0.29/2.31/0.72/0.89 | 1.000/0.294/2.306/0.718/0.893 | PASS |
| bootstrap medians | 394/116/909/283/352 | 393.9/115.6/908.5/282.9/351.8 | PASS |
| analytic CI (38.7/4.1/178.7/10.7/15.4) vs bootstrap (79.0/8.3/254.2/19.0/23.3) | as stated, kept distinct | matches | PASS |
| residual HGB max / linear / null | 0.066 / ~0 / p95<0 | 0.066 / 0.001 / negative | PASS |
| fleet 116, 439/552/365, 205/275/1200/2596 | as stated | matches | PASS |
| socket 0.789 / 102.5 / 24.2% | as stated | matches | PASS |
| subset 394 vs rest 440 | as stated | matches | PASS |
| streaming 0.041 ms; 0.102 vs 0.103; +0.0004; 0.62; 0.004 | as stated | matches | PASS |
| swing ~8x vs natural P95/P05 ~4.4x | as stated | 4.37x | PASS |

No discrepancies, including rounding. All prose values are rounded consistently
with the canonical (unrounded) figures.

### 4. Scientific-strength audit

- tau is described throughout as "identified effective thermal response time" /
  "identified model parameter", and explicitly "not a directly measured physical
  R.C constant" (Sections 1, 5.2, 8.1, 9.1). No overclaim.
- The manuscript states "changes in the identified effective parameter, not
  changes in the physical thermal behaviour" (7.1, 8.1). Correct distinction; the
  forbidden inversion is not present.
- Residual: "not materially predictable/learnable", HGB <= 0.066, permutation
  null reported; explicitly "we do not conclude that the residual contains no
  structure, nor that it is exactly zero" (8.4). No overclaim.
- Phase 2E: "computable ... but ... does not ... provide a useful standalone
  monitoring signal" (7.7, 8.6). No monitor/detector claim.
No overclaims found.

### 5. Novelty audit

Aligned with Phase 3C (YELLOW). The manuscript concedes as prior art: HPC thermal
identification (3.1, 8.7), quantization bias (3.3, 8.2), bootstrap under
dependence (3.4), identifiability-vs-prediction (3.5, 8.7). Conservative hedge
"to the best of our reviewed literature" appears in 2.4 and 3.7. No instance of
"novel", "first", "unprecedented", "state-of-the-art", "breakthrough", or "new
framework/method" as a self-claim. Strongest contribution is correctly the
fleet-vs-artifact comparison (C9), embedded in the controlled study. PASS.

### 6. Causality audit

Allowed causal scope (within-Summit, same-hardware measurement-quality ablation)
is respected. Explicit non-causal disclaimers present for: socket/host
differences ("descriptive property only ... do not attribute it to ... any
cause", 8.5; 9.8), the M100 comparison ("no causal cross-machine claim", 4.1,
9.3), and the mechanism ("errors-in-variables ... aliasing ... we did not
causally isolate them ... not established findings", 9.9). The word "causal" also
appears in the signal-processing sense ("causal, online statistic ... uses no
future data", 7.7/8.6) - not a scientific causal claim. PASS.

### 7. Threats-to-validity audit

All ten required limitations present in Section 9 (items 1-12) and supporting
text: (1) effective tau [9.1]; (2) single-system external validity [9.2]; (3)
Tjmax proxy [9.4]; (4) residual not exactly zero, HGB ~0.066 [9.5]; (5) "not
materially learnable" not "unlearnable" [9.5, 8.4]; (6) M100 contextual/confounded
[9.3]; (7) no labeled anomaly/failure events [9.6, 8.6]; (8) no deployed digital
twin [9.7]; (9) no causal socket/host diagnosis [9.8]; (10) 2E not a useful
monitor [9.6, 8.6]. Also present: temporal resolution [9.10], spatial aggregation
[9.11], bootstrap scope [9.12], reproducibility subsection. PASS.

### 8. Citation audit

In-text keys P1-P15 and Liu-Singh each map to exactly one reference entry, and
every reference entry is cited. No citation is used to support a claim stronger
than its source (P1 = HPC thermal ID under quantization on Galileo, matching the
"prior art" framing; P9 verified; P12 verified, used only as context; P14 verified
by DOI). [VERIFY] preserved on the 13 not-yet-confirmed entries. No fabricated
DOI/citation introduced (STEP 8 scope; not re-verified here). PASS.

### 9. Forbidden-claim scan

Whole-manuscript scan; every hit classified. No TRUE VIOLATION.

| Line(s) | Term | Classification |
|---|---|---|
| 6, 23 | "physical R.C constant" | COMPLIANT NEGATION (defines effective tau) |
| 32, 106, 463, 473, 551 | "causal(ly) ... online" | BENIGN (signal-processing: uses only past data; stated) |
| 189-192, 676, 714 | "anomaly detection" | COMPLIANT (titles/citations of prior-art P14/P15) |
| 195 | "useful standalone monitor" | COMPLIANT NEGATION ("does not establish whether ...") |
| 222 | "not used for any causal claim" | COMPLIANT DISCLAIMER (M100) |
| 561 | "validated monitoring result" | COMPLIANT NEGATION ("rather than a ...") |
| 586 | "no causal cross-machine claim" | COMPLIANT DISCLAIMER |
| 593 | "unlearnable or exactly zero" | COMPLIANT DISCLAIMER ("avoid any claim that ...") |
| 602 | "causally isolate" | COMPLIANT DISCLAIMER (mechanism not established) |
| 639 | "failure prediction" etc. | COMPLIANT DISCLAIMER ("no claim of ...") |

No occurrences of "physical thermal behaviour change", "RUL", "cooling-fault
detection", "deployment-ready", "PINN failed", "universal framework", or
"breakthrough" as assertions.

### 10. Required changes

**None required (GREEN).** Optional (non-blocking) wording note only: the term
"causal/causally" for the online estimator (7.7, 8.6) is used in the
signal-processing sense (no future data) and is disambiguated in-text; a future
copy-edit could substitute "using only past samples" to remove any chance of
misreading. This is stylistic, not a scientific correction, and is not made in
this step.

### 11. Final gate

**GREEN — no substantive correction required.** The manuscript is scientifically
clean: claims are supported and correctly classified, numbers are consistent with
the locked manifest, novelty is conservatively scoped, causal language stays
within the within-Summit ablation, all required limitations are present, and no
forbidden claim appears (all flagged terms are compliant disclaimers, prior-art
citations, or the benign signal-processing sense of "causal").

---

#### Integrity (this step)
Raw SHA-256 prefix 9898170b...996e unchanged; src/ clean; Phase 2A-2E and
Phase 3B/3C artifacts byte-identical; only
`v2_research/paper/claims/paper_level_claim_audit.md` was created; no commit;
manuscript.md not modified.

---

## Claim audit (conditions)

*(source: `v2_research/paper/claims/claim_audit.md`)*

## Paper Claim Audit (Phase 3D)

Mandatory. Every major claim: source · phase · classification [V]/[I]/[L] ·
metric · figure/table · reviewer attack · allowed vs forbidden wording.
Numbers trace to v2_research/paper_analysis/paper_results_manifest.json.

| # | Claim | Source phase | Class | Metric | Fig/Table | Reviewer attack | Allowed wording | Forbidden wording |
|---|---|---|---|---|---|---|---|---|
| 1 | Measurement quality changes identified effective τ | 2B/2C | V | ratios 0.29/2.31/0.72/0.89; 393.8→115.8→910.5 s | Fig2/Tab2 | "quantization bias is textbook (P6–P8)" | "measurement quality substantially changes the identified effective τ" | "quantization changes thermal behavior"; "physical R·C" |
| 2 | Shift is real, not an analytic artifact | 2C | V | boot median≈point; 0% invalid | Tab2 | "bootstrap-under-dependence known (P9)" | "block-bootstrap confirms the shift" | "bootstrap corrects the bias" |
| 3 | Precision ≠ accuracy | 2C | V→I | F1 CoV 0.018, ratio 0.29; boot CI>analytic | Fig2/Tab2 | "analytic CI underestimation is known (P9)" | "a precise-looking interval can surround a biased estimate" | "we discover precision≠accuracy" |
| 4 | Higher quality ≠ better residual prediction | 2A/2B | V | HGB≤0.066; degraded≥F0; null p95<0 | Fig3/Tab3 | "identifiable≠predictive known (P10/P11)" | "did not materially improve out-of-sample residual prediction" | "the residual is unlearnable"; "= 0" |
| 5 | Fleet generalization | 2D | V | 116/116; median 439; P05–P95 275–1200 | Fig4/Tab4 | — | "holds across the 116-unit fleet" | — |
| 6 | Artifact bias > natural variation (STRONGEST) | 2C+2D | V | 115.8 s < fleet min 205 s | Fig5 | "is 116 s physically implausible?" | "the quantization-induced estimate falls below the observed full-fidelity fleet range" | "quantization makes hardware faster"; "physically impossible" |
| 7 | Identification vs prediction dissociation | 2A/2B/2C | I(L) | combined | Fig2+Fig3 | "known principle" | "identification changes while residual prediction does not improve" | "new principle/discovery" |
| 8 | Online τ computable, not a useful monitor | 2E | V | 0.041 ms; OOS 0.102≈base 0.103; spread 0.62; confound 0.004 | Fig6/Tab4 | "monitoring is crowded" | "online-computable but not a validated standalone monitor" | "detects failures/anomalies/cooling faults"; "monitoring works" |
| 9 | τ meaning | 5.2 | — | α→τ | — | — | "effective thermal response time (identification parameter)" | "physical R·C constant" |
| 10 | Socket differences | 2D | V | r=0.789; 24.2% rel diff | Fig(2D) | — | "correlated but not identical (descriptive)" | "caused by cooling/position/workload" |
| 11 | Physics-MLP baseline | 2B | V | mlp_physics ≤0.050 | Tab3 | "is this a PINN paper?" | "a physics-constrained neural residual model, included as a baseline, did not materially improve OOS prediction" | "our PINN failed"; PINN as contribution |

### Novelty positioning (from Phase 3C novelty_verdict.md)
Prior art [L]: quantization bias (P6–P8), block bootstrap (P9), identifiability≠prediction (P10/P11), HPC thermal ID under quantization (P1–P3). Differentiated [I/V]: the controlled same-hardware combination + the C4 artifact-vs-fleet comparison (no prior art found). Verdict: YELLOW — empirical limits study; use "to the best of our reviewed literature".

---

## Final numerical consistency

*(source: `v2_research/paper/claims/final_numerical_consistency.md`)*

## PHASE 3D — FINAL NUMERICAL CONSISTENCY AUDIT

Audit only. `manuscript.md` was not modified. Authoritative source:
`paper_analysis/paper_results_manifest.json` (canonical, unrounded), cross-checked
with `validate_results.py` (44/44 PASS).

### 1. Executive verdict

**GREEN.** Every quantitative statement in Sections 1-11 traces to the canonical
manifest. All rounding is consistent; no scientifically meaningful contradiction,
unit error, swapped estimate, or unsupported number was found. Analytic and
bootstrap intervals are reported distinctly and never swapped; the manuscript does
not claim the bootstrap "removes" or "corrects" bias.

### 2. Quantitative claim inventory

| ID | Section | Quantity | Manuscript | Canonical (manifest) | Status |
|---|---|---|---|---|---|
| N1 | 1,7.1,8.1 | tau F0 | 394 s (394 s) | 393.816 | PASS (round) |
| N2 | 1,7.1,8.1 | tau F1 | 116 s | 115.839 | PASS (round) |
| N3 | 1,7.1,8.1 | tau F2 | 910 s | 910.461 | PASS (round) |
| N4 | 7.1 | tau F3 | 283 s | 282.629 | PASS (round) |
| N5 | 7.1,8.1 | tau F4 | 352 s | 351.987 | PASS (round) |
| N6 | 1,7.1,2.4 | ratios | 0.29/2.31/0.72/0.89 | 0.2935/2.3064/0.7180/0.8931 | PASS (round) |
| N7 | 7.2 | boot medians | 394/116/909/283/352 | 393.92/115.63/908.55/282.85/351.82 | PASS (round) |
| N8 | 7.3 | analytic CI widths | 38.7/4.1/178.7/10.7/15.4 s | same | PASS |
| N9 | 7.3 | bootstrap CI widths | 79.0/8.3/254.2/19.0/23.3 s | same | PASS |
| N10 | 7.4 | HGB max OOS R^2 | 0.066 | 0.06633 (F4) | PASS (round) |
| N11 | 7.4 | linear F0 | "near zero (about 0.001)" | 0.0012 | PASS |
| N12 | 7.4 | HGB F0/F1/F2/F3 | 0.034/0.055/0.006/0.046 | 0.0338/0.0553/0.0063/0.0459 | PASS (round) |
| N13 | 7.5 | fleet valid | 116/116 | 116 | PASS |
| N14 | 7.5 | fleet median | 439 s | 438.891 | PASS (round) |
| N15 | 7.5 | fleet mean/std | 552 s / 365 s | 551.73 / 364.66 | PASS (round) |
| N16 | 7.5 | IQR | 376-588 s | 376-588 | PASS |
| N17 | 7.5,7.6 | P05/P95 | 275 s / 1200 s | 274.58 / 1199.87 | PASS (round) |
| N18 | 7.5,7.6 | min/max | 205 s / 2596 s | 205.447 / 2596.205 | PASS (round) |
| N19 | 7.5,8.5 | socket corr | 0.789 | 0.78878 | PASS (round) |
| N20 | 7.5,8.5 | socket abs/rel diff | 102.5 s / 24.2% | 102.5 / 0.24173 | PASS (round) |
| N21 | 7.5,8.5 | subset/rest | 394 s / 440 s | 394 / ~440 | PASS (round) |
| N22 | 1,7.6,8.2 | quantized < fleet min | 116 < 205 | 115.839 < 205.447 | PASS |
| N23 | 7.6 | fidelity swing vs natural | ~8x vs ~4.4x | 0.29->2.31 (~7.9x); P95/P05=4.37x | PASS |
| N24 | 7.7,8.6 | runtime | 0.041 ms | 0.041378 | PASS (round) |
| N25 | 7.7,8.6 | OOS/baseline alert | 0.102 / 0.103 | 0.10196 / 0.10343 | PASS (round) |
| N26 | 7.7 | OOS-baseline diff | +0.0004 | +0.000443 | PASS (round) |
| N27 | 7.7 | units OOS>baseline | ~51% | 0.51 | PASS |
| N28 | 7.7,8.6 | window rel spread | 0.62 | 0.61954 | PASS (round) |
| N29 | 7.7,8.6 | power-confound corr | 0.004 | 0.003572 | PASS (round) |
| N30 | 4.3,7.5 | hosts/sockets/units | 58 / 2 / 116 | 58x2=116 | PASS |
| N31 | 5.5 | bootstrap B / block | 500 / ~640 s (64/32 pairs) | B=500; 640 s | PASS |
| N32 | 4.4 | rows | ~73.9M -> ~67.3M | derived_manifest (labeled source) | PASS (attributed) |

### 3. tau consistency

Point estimates (394/116/910/283/352 s) appear identically in Abstract, 7.1, and
8.1; the Abstract additionally gives the exact subset median (~394 s). No section
reports a conflicting tau value. tau is uniformly "identified effective thermal
response time" and defined as tau = -dt/ln(alpha) (5.2), never a physical R.C
constant.

### 4. Bootstrap / uncertainty consistency

Bootstrap medians (394/116/909/283/352 s) match the point estimates within
rounding and are labeled as bootstrap medians. The five analytic-vs-bootstrap CI
pairs (38.7/79.0, 4.1/8.3, 178.7/254.2, 10.7/19.0, 15.4/23.3 s; 7.3) are correct
and in the right order (bootstrap wider in every case). The manuscript states the
bootstrap "does not remove the measurement-induced shift ... it only confirms that
the shift persists" (8.3) and "does not correct measurement-induced parameter
bias" (9.12). No swap or "correction" claim.

### 5. Residual prediction consistency

Linear "near zero (about 0.001)"; HGB per-condition 0.034/0.055/0.006/0.046/0.066
with maximum 0.066 (7.4, Table 3); permutation null "at or below zero in every
condition"; explicit "several degraded conditions match or exceed the full-quality
value". Wording is "not materially improve/predictable"; no "zero"/"unlearnable".
Consistent with manifest.

### 6. Fleet consistency

116/116, median 439, mean 552, std 365, IQR 376-588, P05/P95 275/1200, min/max
205/2596, socket 0.789 / 102.5 s / 24.2%, subset 394 vs rest 440 — all appear in
7.5 and are echoed consistently in 8.5. The 116 < 205 comparison (7.6, 8.2, and
Abstract) is framed as identified parameters ("an identified effective response
time that no full-quality unit in the fleet exhibits"), not physical behaviour.

### 7. Streaming consistency

Runtime 0.041 ms; OOS 0.102 vs baseline 0.103 (diff +0.0004); ~51% units
OOS>baseline; rel spread 0.62; power-confound 0.004 — appear consistently in 7.7
and 8.6. No "real-time useful" or "validated monitor" wording; "computable != useful"
is used. (Window-sensitivity values 0.112/0.117/0.102 are in the Phase 2E artifact
but are not quoted in the manuscript; nothing to reconcile.)

### 8. Equation / unit consistency

Model T[n+1] = alpha*T[n] + beta*P[n] + gamma (5.1, 6.1) and tau = -dt/ln(alpha)
(5.2, 5.4) are stated consistently. dt = 10 s for F0/F1/F3 and 20 s for F2/F4
(5.2, matching conditions). Units checked: seconds for tau/CI/fleet; milliseconds
only for runtime (0.041 ms); R^2 dimensionless; correlation dimensionless (0.789);
alert rate as a fraction (0.102), percentage only for "24.2%" and "~51%"; counts
58/2/116 exact. No unit/scale error found.

### 9. Figure / table consistency

In-text references match canonical artifacts: Table 1 (conditions F0-F4), Table 2
(tau identification: point, bootstrap, analytic/bootstrap CoV+CI, ratios), Table 3
(residual OOS by model + null), Table 4 (fleet + streaming); Figure 2 (tau vs
condition with analytic+bootstrap), Figure 3 (residual OOS + null), Figure 4 (fleet
distribution), Figure 5 (fidelity vs fleet range), Figure 6 (streaming OOS vs
baseline). Condition labels and ordering (F0->F4) are consistent throughout.

### 10. Cross-section consistency

Repeated values are identical across sections within rounding: tau 394/116/910/283/
352 (Abstract, 7.1, 8.1); fleet median 439 (7.5, 8.5, Threats); min 205 (7.6, 8.2,
9); HGB 0.066 (Abstract, 7.4, 8.4, 9.5); runtime 0.041 ms (7.7, 8.6); alert 0.102
vs 0.103 (7.7, 8.6). No contradictory number appears in any section.

### 11. Unsupported or mismatched numbers

**None.** Two scan artifacts were investigated and cleared: (a) a "0.103" match at
the DOI line is the substring "0.103" inside "10.1038/..." (M100 DOI), not a data
value; (b) the F3 CI pair "10.7 s versus 19.0 s" spans a line break but is present
and correct. Neither is a discrepancy.

### 12. Final gate

**GREEN — all quantitative claims trace correctly; rounding is consistent.** No
scientifically meaningful numerical contradiction and no unsupported quantitative
claim. Analytic vs bootstrap intervals are distinct and correctly ordered; no
"bootstrap corrects bias" wording; no unit errors; figure/table references are
accurate.

---

#### Integrity (this step)
Raw SHA-256 prefix 9898170b...996e unchanged; src/ clean; Phase 2A-2E and
Phase 3B/3C artifacts byte-identical; manuscript.md unchanged (not edited this
step); validator 44/44 PASS. Only this file
(`v2_research/paper/claims/final_numerical_consistency.md`) was created. No commit.

---

## Claim-evidence matrix

*(source: `v2_research/paper_analysis/claim_evidence_matrix.md`)*

## Claim → Evidence Matrix

| Claim | Experimental evidence [V] | Literature evidence [L] | Strength | Safe wording | Unsafe wording (avoid) |
|---|---|---|---|---|---|
| Measurement quality shifts identified τ | 2B/2C: ratios 1.00/0.29/2.31/0.72/0.89; 394→116 s, 394→910 s | P6–P8 (quantization biases params); P1–P3 (HPC ID under quant) | **strong [V], known mechanism [L]** | "measurement quality substantially changes the identified effective τ" | "we discover that quantization biases parameters" (known) |
| τ shift is real, not an analytic artifact | 2C: bootstrap medians = point estimates; 0% invalid | P9 (MBB valid for dependence) | strong | "block-bootstrap confirms the shift" | "bootstrap corrects the bias" |
| Precision ≠ accuracy | 2C: F1 narrow CI (CoV 0.018) around biased τ (ratio 0.29) | P9 (analytic CI underestimates variance); P6–P8 | moderate–strong | "a precise-looking interval can surround a biased estimate" | "we are first to show precision≠accuracy" |
| Higher quality ≠ better residual prediction | 2A/2B: linear≈0; HGB≤0.066; degraded ≥ F0; null p95<0 | P10, P11 (identifiable≠predictive) | strong [V] | "higher measurement quality did not materially improve out-of-sample residual prediction" | "the residual is unlearnable" |
| Fleet generalization | 2D: 116/116; median 439 s; P05–P95 275–1200 | P4 (fleet temp modeling) | strong | "holds across the 116-unit fleet" | (n/a) |
| Artifact bias > natural variation | 2C+2D: F1 116 s < fleet min 205 s | — (no prior art found) | **strong + differentiated** | "the quantization-induced estimate falls below the observed full-fidelity fleet range" | "quantization makes the hardware physically faster" |
| Identification-vs-prediction dissociation | 2B/2C/2A combined | P10, P11 (concept known) | moderate (domain demo) | "identification improves while residual prediction does not" | "we discover a new principle" |
| Online τ computable but not useful monitor | 2E: 0.041 ms; OOS≈baseline; spread 0.62; confound~0 | HPC monitoring context [VERIFY] | strong [V] negative | "τ is online-computable but not a validated standalone monitor" | "τ detects failures / anomalies / cooling faults" |
| τ meaning | effective τ from ARX α | identifiability theory | — | "effective thermal time constant" | "physical R·C constant" |
| Socket differences | 2D: r=0.789, 24.2% rel diff | — | descriptive only | "sockets are correlated but not identical (descriptive)" | "caused by cooling/position/workload" |

---

## Analysis-stage claim audit

*(source: `v2_research/paper_analysis/claim_audit.md`)*

## Claim Audit

Classification: [V] demonstrated by our experiments · [I] inference · [L] literature.

### Supported claims
- [V] Measurement quality changes the identified effective τ substantially: ratios vs F0 = 1.00 / 0.29 / 2.31 / 0.72 / 0.89 (F0–F4); quantization 394→116 s, downsampling 394→910 s.
- [V] The τ shifts are bootstrap-confirmed (medians reproduce point estimates; 0% invalid fits).
- [V] Block-bootstrap CIs are wider than analytic CIs; F1 has a narrow CI around a biased τ → precision ≠ accuracy. Bootstrap quantifies, does not remove, the bias.
- [V] Higher measurement quality does not materially improve out-of-sample residual prediction; strongest model (HGB) ≤ 0.066, sometimes higher under degraded conditions; all perm-null p95 < 0.
- [V] Fleet: 116/116 units valid; median τ 439 s; P05–P95 275–1200 s; min 205 s; socket corr 0.789; median relative difference 24.2%.
- [V] The quantization-induced estimate (116 s) falls below the observed full-fidelity fleet range (min 205 s).
- [V] Rolling τ is computable online (~0.041 ms/window) but OOS alert rate ≈ baseline/null; short-window τ is not a validated standalone monitor (computable ≠ useful).

### Inference (not proven mechanisms)
- [I] Quantization → errors-in-variables attenuation of α; downsampling → aliasing of faster dynamics. Plausible, not independently demonstrated.
- [I] The small nonlinear residual R² is likely a discretization artifact (it is higher under degraded fidelity), not recovered thermal physics.
- [I] Measurement artifacts could mislead a real digital-twin calibration.

### Literature (to verify before drafting Related Work)
- [L] HPC/node thermal system identification is prior art; "richer observation → sharper identification" is textbook. [WEB VERIFICATION REQUIRED]

### FORBIDDEN claims (must never appear)
- ❌ τ is a physical R·C constant
- ❌ failure prediction / remaining-useful-life
- ❌ degradation prediction
- ❌ cooling-fault or thermal-interface diagnosis
- ❌ universal thermal model / framework
- ❌ PINN superiority (this is not a PINN paper)
- ❌ "the residual is unlearnable" (use "not materially learnable out-of-sample")
- ❌ validated real-time monitor
- ❌ causal explanation of socket/host τ differences
- ❌ any causal claim outside the within-Summit ablation

Automated guard: `validate_results.py` enforces the numeric facts (44 checks); table/figure text is reviewed against this list. No generated wording asserts a forbidden claim.

---

## Artifact inventory

*(source: `v2_research/paper_analysis/artifact_inventory.md`)*

## Phase 2 Artifact Inventory (source of truth for the paper)

Read-only. No Phase 2 artifact is modified by the paper-analysis layer.

| Phase | Artifact | Type | Used by paper? | Source metric |
|---|---|---|---|---|
| 2A | counterfactual/phase2a_results.json | JSON | context only | τ median (394 s), OOS increment R² (~0.006) |
| 2B | observability_ablation/observability_ablation_results.json | JSON | **yes** | τ point per condition; residual OOS R² (5 models) + perm-null |
| 2B | observability_ablation/observability_ablation_table.csv | CSV | supplementary | per-condition summary |
| 2B | observability_ablation/fig1-3_*.png | PNG | superseded by fig02/03 | exploratory |
| 2C | phase2c_bootstrap/phase2c_bootstrap_results.json | JSON | **yes** | bootstrap τ median/CoV/CI; ratios vs F0; invalid % |
| 2C | phase2c_bootstrap/phase2c_bootstrap_table.csv | CSV | supplementary | analytic vs bootstrap |
| 2C | phase2c_bootstrap/fig1-3_*.png | PNG | superseded by fig02 | exploratory |
| 2D | phase2d_fleet/phase2d_results.json | JSON | **yes** | fleet τ stats; socket consistency; fidelity-vs-fleet |
| 2D | phase2d_fleet/phase2d_units.json | JSON | **yes** | per-unit τ (fig04/05 histogram) |
| 2D | phase2d_fleet/table1/2_*.md | MD | superseded by table04 | fleet + socket |
| 2D | phase2d_fleet/fig1-4_*.png | PNG | superseded by fig04/05 | exploratory |
| 2E | phase2e_streaming/phase2e_results.json | JSON | **yes** | OOS vs baseline alert; rel spread; power confound; runtime |
| 2E | phase2e_streaming/table1-3_*.md | MD | superseded by table04 | streaming |
| 2E | phase2e_streaming/fig1-5_*.png | PNG | superseded by fig06 | exploratory |
| raw | raw/a_fullperiod_10sec_58hosts_decomp/ | Parquet | never redistributed | SHA-256 9898170b…996e |
| V1 | src/baseline/classical_baseline.py | code | frozen model | ARX T[t+1]=αT[t]+βP[t]+γ |

The paper-analysis layer re-derives all paper tables/figures from the JSON source-of-truth files (never from the exploratory PNGs).
