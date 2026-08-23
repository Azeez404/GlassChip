# Claim → Evidence Matrix

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
