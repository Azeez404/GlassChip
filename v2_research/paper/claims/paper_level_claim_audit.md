# PHASE 3D — PAPER-LEVEL CLAIM AUDIT

Audit only. `manuscript.md` was not modified. Authoritative sources:
paper_results_manifest.json and the Phase 3C literature/novelty files.

## 1. Executive verdict

**GREEN.** Every substantive claim in Sections 1-11 is supported by the locked
artifacts or verified literature, correctly classified, numerically consistent
with the manifest (validator 44/44), worded no more strongly than the evidence
permits, aligned with the Phase 3C YELLOW novelty position, and free of
forbidden claims. No substantive correction is required. One optional wording
note (the word "causal" used in the signal-processing sense) is recorded below.

## 2. Claim inventory

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

## 3. Numerical consistency

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

## 4. Scientific-strength audit

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

## 5. Novelty audit

Aligned with Phase 3C (YELLOW). The manuscript concedes as prior art: HPC thermal
identification (3.1, 8.7), quantization bias (3.3, 8.2), bootstrap under
dependence (3.4), identifiability-vs-prediction (3.5, 8.7). Conservative hedge
"to the best of our reviewed literature" appears in 2.4 and 3.7. No instance of
"novel", "first", "unprecedented", "state-of-the-art", "breakthrough", or "new
framework/method" as a self-claim. Strongest contribution is correctly the
fleet-vs-artifact comparison (C9), embedded in the controlled study. PASS.

## 6. Causality audit

Allowed causal scope (within-Summit, same-hardware measurement-quality ablation)
is respected. Explicit non-causal disclaimers present for: socket/host
differences ("descriptive property only ... do not attribute it to ... any
cause", 8.5; 9.8), the M100 comparison ("no causal cross-machine claim", 4.1,
9.3), and the mechanism ("errors-in-variables ... aliasing ... we did not
causally isolate them ... not established findings", 9.9). The word "causal" also
appears in the signal-processing sense ("causal, online statistic ... uses no
future data", 7.7/8.6) - not a scientific causal claim. PASS.

## 7. Threats-to-validity audit

All ten required limitations present in Section 9 (items 1-12) and supporting
text: (1) effective tau [9.1]; (2) single-system external validity [9.2]; (3)
Tjmax proxy [9.4]; (4) residual not exactly zero, HGB ~0.066 [9.5]; (5) "not
materially learnable" not "unlearnable" [9.5, 8.4]; (6) M100 contextual/confounded
[9.3]; (7) no labeled anomaly/failure events [9.6, 8.6]; (8) no deployed digital
twin [9.7]; (9) no causal socket/host diagnosis [9.8]; (10) 2E not a useful
monitor [9.6, 8.6]. Also present: temporal resolution [9.10], spatial aggregation
[9.11], bootstrap scope [9.12], reproducibility subsection. PASS.

## 8. Citation audit

In-text keys P1-P15 and Liu-Singh each map to exactly one reference entry, and
every reference entry is cited. No citation is used to support a claim stronger
than its source (P1 = HPC thermal ID under quantization on Galileo, matching the
"prior art" framing; P9 verified; P12 verified, used only as context; P14 verified
by DOI). [VERIFY] preserved on the 13 not-yet-confirmed entries. No fabricated
DOI/citation introduced (STEP 8 scope; not re-verified here). PASS.

## 9. Forbidden-claim scan

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

## 10. Required changes

**None required (GREEN).** Optional (non-blocking) wording note only: the term
"causal/causally" for the online estimator (7.7, 8.6) is used in the
signal-processing sense (no future data) and is disambiguated in-text; a future
copy-edit could substitute "using only past samples" to remove any chance of
misreading. This is stylistic, not a scientific correction, and is not made in
this step.

## 11. Final gate

**GREEN — no substantive correction required.** The manuscript is scientifically
clean: claims are supported and correctly classified, numbers are consistent with
the locked manifest, novelty is conservatively scoped, causal language stays
within the within-Summit ablation, all required limitations are present, and no
forbidden claim appears (all flagged terms are compliant disclaimers, prior-art
citations, or the benign signal-processing sense of "causal").

---

### Integrity (this step)
Raw SHA-256 prefix 9898170b...996e unchanged; src/ clean; Phase 2A-2E and
Phase 3B/3C artifacts byte-identical; only
`v2_research/paper/claims/paper_level_claim_audit.md` was created; no commit;
manuscript.md not modified.
