# Paper Claim Audit (Phase 3D)

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

## Novelty positioning (from Phase 3C novelty_verdict.md)
Prior art [L]: quantization bias (P6–P8), block bootstrap (P9), identifiability≠prediction (P10/P11), HPC thermal ID under quantization (P1–P3). Differentiated [I/V]: the controlled same-hardware combination + the C4 artifact-vs-fleet comparison (no prior art found). Verdict: YELLOW — empirical limits study; use "to the best of our reviewed literature".
