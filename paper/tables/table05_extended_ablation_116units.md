# Table 5 — Extended ablation across all 116 sampled host-sockets (paired per unit)

Source: `artifacts/results/phase2f_ablation_116.json` (Phase 2F).
Reuses the frozen Phase 2B condition definitions, segmentation and estimator. Bootstrap
CIs are percentile intervals over 2000 resamples of the 116 paired units, seed 0.

| Condition | n paired | median tau (s) | per-unit ratio to F0, median [P05-P95] | Spearman rho vs F0 [95% CI] |
|---|---|---|---|---|
| F0 (full quality) | 116 | 438.9 | 1.000 (reference) | 1.000 (by construction) |
| F1 (1 degC quantization) | 116 | 141.8 | 0.327 [0.215-0.466] | 0.796 [0.705, 0.863] |
| F2 (20 s downsampling) | 116 | 1021.7 | 2.260 [1.703-5.473] | 0.820 [0.727, 0.883] |
| F3 (hottest-core proxy) | 116 | 307.1 | 0.686 [0.223-0.997] | 0.491 [0.324, 0.629] |
| F4 (combined) | 116 | 368.7 | 0.815 [0.295-1.196] | 0.499 [0.333, 0.635] |

## Dispersion checked in both parameterisations

tau = -dt/ln(alpha) is strongly nonlinear as alpha -> 1, so a change in tau-space dispersion
may be algebraic rather than physical. Every spread statistic is therefore also reported
in alpha-space and as the scale-free CV of (1 - alpha).

| Condition | tau IQR / F0 | alpha IQR / F0 | CV(1-alpha) | CV(1-alpha) at F0 | Narrowing in both? |
|---|---|---|---|---|---|
| F0 (full quality) | 1.000 | 1.000 | 0.369 | 0.369 | - |
| F1 (1 degC quantization) | 0.370 | 3.315 | 0.327 | 0.369 | **no** |
| F2 (20 s downsampling) | 3.446 | 1.227 | 0.476 | 0.369 | **no** |
| F3 (hottest-core proxy) | 0.363 | 0.843 | 0.279 | 0.369 | yes |
| F4 (combined) | 0.394 | 1.258 | 0.215 | 0.369 | **no** |

Only F3 narrows in both parameterisations. The apparent F1 narrowing in tau reverses in
alpha, so no claim of measurement-induced homogenisation is made.
