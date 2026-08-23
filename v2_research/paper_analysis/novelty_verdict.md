# Novelty Verdict

## Executive verdict
**YELLOW — proceed with a conservative, empirical-limits framing.** Every
*principle* GLASSCHIP relies on is already established: quantization biases
identified parameters (quantized system-ID literature), analytic/iid uncertainty
underestimates variance for dependent data (moving-block bootstrap, Künsch 1989),
good calibration ≠ good prediction (identifiability literature), and HPC node
thermal RC identification under 1°C quantization already exists (Bartolini group).
The contribution is therefore **not a new principle** but a **controlled empirical
demonstration and combination on a real 116-unit supercomputer fleet**, plus one
genuinely under-served quantitative result (artifact bias vs natural fleet
variation) and an honest operational negative. This is a limits/reproducibility
study, not a novelty breakthrough. Position accordingly.

## What is definitely prior art [L]
- Quantization biases parameter estimation (errors-in-variables). P6–P8.
- iid/analytic CIs underestimate variance under temporal dependence; MBB fixes it. P9.
- Identifiable-but-not-predictive / good-fit-≠-prediction. P10, P11.
- HPC node thermal RC/ARX identification from real measurements **with 1°C
  quantization present**. P1–P3.

## What is partially differentiated (YELLOW)
- **C1** same-hardware measurement-quality ablation — ablation framing is not
  common in HPC thermal ID, but HPC thermal ID + quantization handling exist.
- **C2** quantified τ bias (0.29–2.31×) across F0–F4 — the mechanism is textbook;
  the controlled per-condition quantification on real HPC is the increment.
- **C3** precise-but-biased demonstration — CI-underestimation is expected [L];
  showing a tight interval around a strongly biased τ on HPC thermal is a
  demonstration, not a discovery.
- **C5** identification-vs-residual-prediction dissociation — concept known;
  our value is the controlled measurement-quality manipulation + honest OOS + null.
- **C6** online-computable-but-not-useful τ monitor — negative operational result;
  niche, but HPC monitoring generally is crowded.

## What appears genuinely differentiated (GREEN)
- **C4** comparing the measurement-induced τ bias against the **natural fleet
  distribution** (quantized 116 s below the entire 116-unit fleet minimum 205 s).
  No prior art found doing this quantitative artifact-vs-heterogeneity comparison.
  This is the strongest single differentiator.

## What we must NOT claim
Physical R·C; failure/degradation prediction; validated monitor; "unlearnable";
PINN superiority; a *new principle* (quantization bias / precision≠accuracy /
identifiability≠prediction are all known); causal socket explanation; that HPC
thermal ID is itself novel.

## Strongest defensible contribution
The **controlled, real-fleet quantitative comparison of measurement-induced τ
bias against natural unit-to-unit variation (C4), embedded in the identification-
vs-prediction dissociation (C5) and the online negative (C6)** — i.e., a caution
that measurement choices can bias identified thermal parameters beyond the range
of genuine hardware heterogeneity, while buying no residual predictability.

## Weakest contribution
**C2/C3 as standalone claims** — restating known quantization-bias and CI-
underestimation results; must be framed as demonstration-in-context, never as
discovery.

## Reviewer attack scenarios
1. "Quantization bias is textbook (P6–P8)." → concede mechanism; stress the
   controlled real-HPC-fleet quantification and the fleet-comparison (C4).
2. "HPC thermal ID under quantization is done (P1–P3)." → concede; those
   *overcome* quantization for accuracy; we *characterize the bias* and its
   size vs heterogeneity, and add the residual-prediction and monitoring results.
3. "Analytic CIs underestimate variance — known (P9)." → concede; our point is
   *bias* (precision≠accuracy), not the CI-width gap.
4. "Identifiable≠predictive is known (P10/P11)." → concede principle; ours is a
   measurement-quality-controlled demonstration on real HPC with OOS+null.
5. "Negative/limits study, low novelty." → agree on framing; argue value =
   rigor, reproducibility, and the C4 quantitative result; target the right venue.

## Recommended paper positioning
An **HPC/systems empirical limits study**: *"Measurement quality can bias the
identified thermal model of a supercomputer beyond natural fleet variation, and
better measurements do not make the residual more predictable."* A caution for
HPC thermal digital-twin calibration — not a method, not a monitor.

## Venue implications
HPC/systems workshops (SC/ICPP/CLUSTER-affiliated), *JPDC*/*FGCS*, or
reproducibility / negative-results / applied-scientific-ML tracks. **Not** a
flagship ML or novelty-driven venue. A short/workshop paper is the honest target.

## Kill criteria
Abandon/redirect only if: (a) a prior paper is found that already runs a
controlled measurement-quality ablation on HPC thermal ID **and** compares the
bias to fleet heterogeneity (would collapse C4) — not found so far; or (b) the
target venue requires methodological novelty the study does not have. Neither is
currently the case → proceed with the conservative framing.
