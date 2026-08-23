# PHASE 3D — FINAL NUMERICAL CONSISTENCY AUDIT

Audit only. `manuscript.md` was not modified. Authoritative source:
`paper_analysis/paper_results_manifest.json` (canonical, unrounded), cross-checked
with `validate_results.py` (44/44 PASS).

## 1. Executive verdict

**GREEN.** Every quantitative statement in Sections 1-11 traces to the canonical
manifest. All rounding is consistent; no scientifically meaningful contradiction,
unit error, swapped estimate, or unsupported number was found. Analytic and
bootstrap intervals are reported distinctly and never swapped; the manuscript does
not claim the bootstrap "removes" or "corrects" bias.

## 2. Quantitative claim inventory

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

## 3. tau consistency

Point estimates (394/116/910/283/352 s) appear identically in Abstract, 7.1, and
8.1; the Abstract additionally gives the exact subset median (~394 s). No section
reports a conflicting tau value. tau is uniformly "identified effective thermal
response time" and defined as tau = -dt/ln(alpha) (5.2), never a physical R.C
constant.

## 4. Bootstrap / uncertainty consistency

Bootstrap medians (394/116/909/283/352 s) match the point estimates within
rounding and are labeled as bootstrap medians. The five analytic-vs-bootstrap CI
pairs (38.7/79.0, 4.1/8.3, 178.7/254.2, 10.7/19.0, 15.4/23.3 s; 7.3) are correct
and in the right order (bootstrap wider in every case). The manuscript states the
bootstrap "does not remove the measurement-induced shift ... it only confirms that
the shift persists" (8.3) and "does not correct measurement-induced parameter
bias" (9.12). No swap or "correction" claim.

## 5. Residual prediction consistency

Linear "near zero (about 0.001)"; HGB per-condition 0.034/0.055/0.006/0.046/0.066
with maximum 0.066 (7.4, Table 3); permutation null "at or below zero in every
condition"; explicit "several degraded conditions match or exceed the full-quality
value". Wording is "not materially improve/predictable"; no "zero"/"unlearnable".
Consistent with manifest.

## 6. Fleet consistency

116/116, median 439, mean 552, std 365, IQR 376-588, P05/P95 275/1200, min/max
205/2596, socket 0.789 / 102.5 s / 24.2%, subset 394 vs rest 440 — all appear in
7.5 and are echoed consistently in 8.5. The 116 < 205 comparison (7.6, 8.2, and
Abstract) is framed as identified parameters ("an identified effective response
time that no full-quality unit in the fleet exhibits"), not physical behaviour.

## 7. Streaming consistency

Runtime 0.041 ms; OOS 0.102 vs baseline 0.103 (diff +0.0004); ~51% units
OOS>baseline; rel spread 0.62; power-confound 0.004 — appear consistently in 7.7
and 8.6. No "real-time useful" or "validated monitor" wording; "computable != useful"
is used. (Window-sensitivity values 0.112/0.117/0.102 are in the Phase 2E artifact
but are not quoted in the manuscript; nothing to reconcile.)

## 8. Equation / unit consistency

Model T[n+1] = alpha*T[n] + beta*P[n] + gamma (5.1, 6.1) and tau = -dt/ln(alpha)
(5.2, 5.4) are stated consistently. dt = 10 s for F0/F1/F3 and 20 s for F2/F4
(5.2, matching conditions). Units checked: seconds for tau/CI/fleet; milliseconds
only for runtime (0.041 ms); R^2 dimensionless; correlation dimensionless (0.789);
alert rate as a fraction (0.102), percentage only for "24.2%" and "~51%"; counts
58/2/116 exact. No unit/scale error found.

## 9. Figure / table consistency

In-text references match canonical artifacts: Table 1 (conditions F0-F4), Table 2
(tau identification: point, bootstrap, analytic/bootstrap CoV+CI, ratios), Table 3
(residual OOS by model + null), Table 4 (fleet + streaming); Figure 2 (tau vs
condition with analytic+bootstrap), Figure 3 (residual OOS + null), Figure 4 (fleet
distribution), Figure 5 (fidelity vs fleet range), Figure 6 (streaming OOS vs
baseline). Condition labels and ordering (F0->F4) are consistent throughout.

## 10. Cross-section consistency

Repeated values are identical across sections within rounding: tau 394/116/910/283/
352 (Abstract, 7.1, 8.1); fleet median 439 (7.5, 8.5, Threats); min 205 (7.6, 8.2,
9); HGB 0.066 (Abstract, 7.4, 8.4, 9.5); runtime 0.041 ms (7.7, 8.6); alert 0.102
vs 0.103 (7.7, 8.6). No contradictory number appears in any section.

## 11. Unsupported or mismatched numbers

**None.** Two scan artifacts were investigated and cleared: (a) a "0.103" match at
the DOI line is the substring "0.103" inside "10.1038/..." (M100 DOI), not a data
value; (b) the F3 CI pair "10.7 s versus 19.0 s" spans a line break but is present
and correct. Neither is a discrepancy.

## 12. Final gate

**GREEN — all quantitative claims trace correctly; rounding is consistent.** No
scientifically meaningful numerical contradiction and no unsupported quantitative
claim. Analytic vs bootstrap intervals are distinct and correctly ordered; no
"bootstrap corrects bias" wording; no unit errors; figure/table references are
accurate.

---

### Integrity (this step)
Raw SHA-256 prefix 9898170b...996e unchanged; src/ clean; Phase 2A-2E and
Phase 3B/3C artifacts byte-identical; manuscript.md unchanged (not edited this
step); validator 44/44 PASS. Only this file
(`v2_research/paper/claims/final_numerical_consistency.md`) was created. No commit.
