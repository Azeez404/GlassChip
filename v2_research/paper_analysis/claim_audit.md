# Claim Audit

Classification: [V] demonstrated by our experiments · [I] inference · [L] literature.

## Supported claims
- [V] Measurement quality changes the identified effective τ substantially: ratios vs F0 = 1.00 / 0.29 / 2.31 / 0.72 / 0.89 (F0–F4); quantization 394→116 s, downsampling 394→910 s.
- [V] The τ shifts are bootstrap-confirmed (medians reproduce point estimates; 0% invalid fits).
- [V] Block-bootstrap CIs are wider than analytic CIs; F1 has a narrow CI around a biased τ → precision ≠ accuracy. Bootstrap quantifies, does not remove, the bias.
- [V] Higher measurement quality does not materially improve out-of-sample residual prediction; strongest model (HGB) ≤ 0.066, sometimes higher under degraded conditions; all perm-null p95 < 0.
- [V] Fleet: 116/116 units valid; median τ 439 s; P05–P95 275–1200 s; min 205 s; socket corr 0.789; median relative difference 24.2%.
- [V] The quantization-induced estimate (116 s) falls below the observed full-fidelity fleet range (min 205 s).
- [V] Rolling τ is computable online (~0.041 ms/window) but OOS alert rate ≈ baseline/null; short-window τ is not a validated standalone monitor (computable ≠ useful).

## Inference (not proven mechanisms)
- [I] Quantization → errors-in-variables attenuation of α; downsampling → aliasing of faster dynamics. Plausible, not independently demonstrated.
- [I] The small nonlinear residual R² is likely a discretization artifact (it is higher under degraded fidelity), not recovered thermal physics.
- [I] Measurement artifacts could mislead a real digital-twin calibration.

## Literature (to verify before drafting Related Work)
- [L] HPC/node thermal system identification is prior art; "richer observation → sharper identification" is textbook. [WEB VERIFICATION REQUIRED]

## FORBIDDEN claims (must never appear)
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
