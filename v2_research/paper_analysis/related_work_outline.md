# Related Work — outline (no prose yet)

## 1. HPC / supercomputer thermal modeling
- **Knows:** node/fleet thermal behavior of real supercomputers is modeled from measurements; RC/ARX identification on in-production HPC nodes exists, including under 1°C temperature quantization (P1–P3); spatiotemporal node-temperature models exist (P4); M100/Summit datasets released (P12, P13); facility RC on M100 (P5).
- **Does not establish:** a controlled same-hardware manipulation of measurement quality, or how quantization/sampling/spatial choices *bias* the identified parameter.
- **Support:** P1, P2, P3, P4, P5, P12, P13.
- **GLASSCHIP fit:** same domain and model class; we add the measurement-quality ablation and bias quantification.

## 2. Thermal / dynamical system identification
- **Knows:** first-order RC/ARX identification is standard; identifiability theory (structural vs practical) is mature.
- **Does not establish:** the effect on a real HPC fleet, or the artifact-vs-heterogeneity comparison.
- **Support:** P1–P3, P10, P11.
- **GLASSCHIP fit:** we use the standard estimator unmodified (frozen), as a probe.

## 3. Measurement quality and system identification
- **Knows:** quantized observations bias parameter estimates (errors-in-variables); estimator design under quantization is a mature field (P6–P8). iid/analytic uncertainty underestimates variance for temporally dependent data; moving-block bootstrap is the standard remedy (P9).
- **Does not establish:** these effects, controlled and quantified, on real supercomputer thermal measurements; nor the precise-but-biased demonstration in this domain; nor a comparison to natural fleet variation.
- **Support:** P6, P7, P8, P9.
- **GLASSCHIP fit:** we demonstrate the *known mechanisms* empirically, on a real 116-unit fleet, and quantify their size relative to natural heterogeneity.

## 4. Physics-informed / residual learning
- **Knows:** identifiable parameters do not guarantee predictive accuracy; good calibration fit can fail out-of-sample (P10, P11). Physics-informed models for thermal ID exist.
- **Does not establish:** that improving measurement quality sharpens identification without improving OOS residual prediction on real HPC data.
- **Support:** P10, P11.
- **GLASSCHIP fit:** our identification-vs-residual-predictability dissociation is a domain demonstration with honest OOS + permutation null.

## 5. Online thermal monitoring / change detection
- **Knows:** HPC anomaly/thermal monitoring is an active area (context).
- **Does not establish:** whether an online effective-τ statistic is a *useful* standalone monitor.
- **Support:** [WEB VERIFICATION REQUIRED — add 1–2 HPC monitoring refs].
- **GLASSCHIP fit:** we report a negative operational boundary (computable ≠ useful).

## 6. Gap addressed by this study
No prior work runs a **controlled, same-hardware measurement-quality ablation on a real supercomputer fleet** that (a) quantifies effective-τ bias across quantization/sampling/spatial conditions, (b) shows the bias can exceed natural unit-to-unit variation, (c) demonstrates precise-but-biased uncertainty, (d) shows higher measurement quality does not improve OOS residual prediction, and (e) reports the online-computable-but-not-useful monitoring boundary. Each ingredient is individually known; the **controlled empirical combination on real fleet data** is the contribution.
