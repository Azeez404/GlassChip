# Literature, Citations and Novelty Assessment

Background research supporting the manuscript's related-work section and its positioning.
Consolidated from the separate literature documents produced during analysis.


---

## Related-work outline

*(source: `v2_research/paper_analysis/related_work_outline.md`)*

## Related Work — outline (no prose yet)

### 1. HPC / supercomputer thermal modeling
- **Knows:** node/fleet thermal behavior of real supercomputers is modeled from measurements; RC/ARX identification on in-production HPC nodes exists, including under 1°C temperature quantization (P1–P3); spatiotemporal node-temperature models exist (P4); M100/Summit datasets released (P12, P13); facility RC on M100 (P5).
- **Does not establish:** a controlled same-hardware manipulation of measurement quality, or how quantization/sampling/spatial choices *bias* the identified parameter.
- **Support:** P1, P2, P3, P4, P5, P12, P13.
- **GLASSCHIP fit:** same domain and model class; we add the measurement-quality ablation and bias quantification.

### 2. Thermal / dynamical system identification
- **Knows:** first-order RC/ARX identification is standard; identifiability theory (structural vs practical) is mature.
- **Does not establish:** the effect on a real HPC fleet, or the artifact-vs-heterogeneity comparison.
- **Support:** P1–P3, P10, P11.
- **GLASSCHIP fit:** we use the standard estimator unmodified (frozen), as a probe.

### 3. Measurement quality and system identification
- **Knows:** quantized observations bias parameter estimates (errors-in-variables); estimator design under quantization is a mature field (P6–P8). iid/analytic uncertainty underestimates variance for temporally dependent data; moving-block bootstrap is the standard remedy (P9).
- **Does not establish:** these effects, controlled and quantified, on real supercomputer thermal measurements; nor the precise-but-biased demonstration in this domain; nor a comparison to natural fleet variation.
- **Support:** P6, P7, P8, P9.
- **GLASSCHIP fit:** we demonstrate the *known mechanisms* empirically, on a real 116-unit fleet, and quantify their size relative to natural heterogeneity.

### 4. Physics-informed / residual learning
- **Knows:** identifiable parameters do not guarantee predictive accuracy; good calibration fit can fail out-of-sample (P10, P11). Physics-informed models for thermal ID exist.
- **Does not establish:** that improving measurement quality sharpens identification without improving OOS residual prediction on real HPC data.
- **Support:** P10, P11.
- **GLASSCHIP fit:** our identification-vs-residual-predictability dissociation is a domain demonstration with honest OOS + permutation null.

### 5. Online thermal monitoring / change detection
- **Knows:** HPC anomaly/thermal monitoring is an active area (context).
- **Does not establish:** whether an online effective-τ statistic is a *useful* standalone monitor.
- **Support:** [WEB VERIFICATION REQUIRED — add 1–2 HPC monitoring refs].
- **GLASSCHIP fit:** we report a negative operational boundary (computable ≠ useful).

### 6. Gap addressed by this study
No prior work runs a **controlled, same-hardware measurement-quality ablation on a real supercomputer fleet** that (a) quantifies effective-τ bias across quantization/sampling/spatial conditions, (b) shows the bias can exceed natural unit-to-unit variation, (c) demonstrates precise-but-biased uncertainty, (d) shows higher measurement quality does not improve OOS residual prediction, and (e) reports the online-computable-but-not-useful monitoring boundary. Each ingredient is individually known; the **controlled empirical combination on real fleet data** is the contribution.

---

## Literature matrix

*(source: `v2_research/paper_analysis/literature_matrix.md`)*

## Literature Matrix — closest prior art

All URLs are from a live search; **DOIs marked [VERIFY]** must be confirmed before
citing (not fabricated). Compact form: the 20 audit fields are captured as columns
+ an Overlap/Difference note per paper. Real vs synthetic, thermal model, param-ID,
measurement manipulation, fleet, OOS, uncertainty, online are encoded in columns.

| # | Paper (short) | Yr | Venue | Real? | HPC? | Thermal RC/ARX | Quant manip | Sampling manip | Fleet | OOS ML resid | Uncertainty | Online |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | Thermal Model Identification of Computing Nodes in HPC Systems (Bartolini et al.) — ieeexplore 8863115 | ~2019 | IEEE | yes | **yes** | yes | handles 1°C quant (to overcome) | no | node(s) | no | limited | no |
| P2 | Thermal model identification of supercomputing nodes in production — ieeexplore 7793664 | ~2016 | IEEE | yes | yes | yes | handles quant | no | node | no | no | no |
| P3 | Robust identification of thermal models for in-production HPC clusters (ML data selection) — arXiv:1810.01865 | 2018 | arXiv | yes | yes | yes | handles quant | no | cluster | no | some | no |
| P4 | Spatiotemporal Modeling of Node Temperatures in Supercomputers — arXiv:1505.06275 | 2015 | arXiv | yes | yes | statistical | no | no | fleet | no | yes | no |
| P5 | A Configurable Thermal-Dynamic Model (Marconi100) — arXiv:2607.28962 | 2026 | arXiv | yes | yes (facility) | RC (facility) | no | no | facility | no | some | no |
| P6 | System Identification with Quantized Observations (Wang/Yin/Zhao) — RG 229101105 | ~2010 | book/Automatica | n/a | no | generic | **core topic** | no | n/a | no | yes | no |
| P7 | Asymptotically efficient estimation using quantized outputs — Automatica S0005109807000970 | 2008 | Automatica | n/a | no | generic | **core** | no | n/a | no | yes | no |
| P8 | Parametric System Identification Using Quantized Data — arXiv:1804.10015 | 2018 | arXiv | n/a | no | generic | **core** | no | n/a | no | yes | no |
| P9 | Künsch, Jackknife/Bootstrap for stationary observations (moving-block bootstrap) — Ann. Statist. | 1989 | Ann. Statist. | n/a | no | n/a | no | dependence | n/a | no | **core (MBB)** | no |
| P10 | Think before you fit: parameter identifiability, sensitivity, uncertainty — arXiv:2508.18853 | 2025 | arXiv | n/a | no | ODE | no | no | n/a | no | yes | no |
| P11 | Parameter identifiability & model selection (PDE cell invasion) — PMC10914513 | 2024 | J venue | n/a | no | PDE | no | no | n/a | good-fit≠predict | yes | no |
| P12 | M100 ExaData dataset — Nature Sci Data, 10.1038/s41597-023-02174-3 | 2023 | Nat SciData | yes | yes | dataset | — | — | fleet | — | — | — |
| P13 | Summit per-component power+thermal dataset — 10.13139/OLCF/1861393 | 2022 | OLCF/OSTI | yes | yes | dataset | — | — | fleet | — | — | — |

### Overlap / Difference (decision-critical)
- **P1–P3 (closest prior art).** *Overlap:* HPC node thermal RC/ARX identification from real measurements **with 1°C temperature quantization present.** *Difference:* they **overcome** quantization to obtain an *accurate* model; they do **not** run a controlled same-hardware ablation, do **not** quantify τ **bias** across measurement-quality conditions, do **not** show precise-but-biased uncertainty, do **not** compare artifact bias to fleet heterogeneity, and do **not** test residual OOS predictability or online monitoring. → threatens C1/C2 framing, not C3–C6.
- **P6–P8 (quantized system ID).** *Overlap:* quantization biases parameter estimates (errors-in-variables). *Difference:* generic/theoretical, not thermal, not HPC, no fleet, no fidelity-vs-heterogeneity, no dissociation. Establishes the **mechanism** [L]; makes our *phenomenon* expected, our *demonstration on real HPC fleet* the increment.
- **P9 (block bootstrap).** *Overlap:* iid/analytic intervals underestimate variance for dependent data; MBB is the fix. *Difference:* our Phase 2C **uses** this; it makes "analytic CI narrower than bootstrap" **expected/textbook**, so C3's novelty is the *bias* (precision≠accuracy) on HPC thermal, not the CI-width gap.
- **P10–P11 (identifiability vs prediction).** *Overlap:* good-fit parameters ≠ good prediction under new conditions is known. *Difference:* systems-biology/ODE/PDE, not measurement-quality-controlled, not HPC, not OOS residual on real fleet. Makes our C5 a *domain demonstration*, not a new principle.
- **P4/P5/P12/P13.** Context: supercomputer temperature modeling and the datasets we use; none run the measurement-quality ablation.

---

## Citation evidence

*(source: `v2_research/paper_analysis/citation_evidence.md`)*

## Citation Evidence

Each entry: citation · stable URL · DOI (⚠ = verify before use, not fabricated) ·
exact claim it supports · evidence type. No DOI is asserted without verification.

### HPC thermal identification (closest prior art)
- **Bartolini et al., "Thermal Model Identification of Computing Nodes in HPC Systems," IEEE.**
  https://ieeexplore.ieee.org/document/8863115/ · DOI ⚠[VERIFY] · Supports: HPC node thermal RC identification from real measurements with 1°C quantization exists (prior art). · Primary.
- **"Thermal model identification of supercomputing nodes in production environment," IEEE.**
  https://ieeexplore.ieee.org/document/7793664/ · DOI ⚠[VERIFY] · Supports: in-production HPC thermal ID prior art. · Primary.
- **"Robust identification of thermal models for in-production HPC clusters with ML-based data selection," arXiv:1810.01865.**
  https://arxiv.org/abs/1810.01865 · Supports: HPC cluster thermal ID under quantization; models achieve error < 1°C quantization step. · Primary.
- **"Spatiotemporal Modeling of Node Temperatures in Supercomputers," arXiv:1505.06275.**
  https://arxiv.org/abs/1505.06275 · Supports: fleet-scale supercomputer node temperature modeling exists. · Primary.
- **"A Configurable Thermal-Dynamic Model … Marconi100," arXiv:2607.28962.**
  https://arxiv.org/abs/2607.28962 · Supports: recent RC thermal modeling calibrated on M100 (facility level). · Primary.

### Quantized system identification (mechanism = quantization biases parameters)
- **Wang, Yin, Zhao, "System Identification with Quantized Observations."**
  https://www.researchgate.net/publication/229101105 · DOI ⚠[VERIFY] · Supports: quantized observations bias/complicate parameter estimation. · Primary/background.
- **"Asymptotically efficient parameter estimation using quantized output observations," Automatica (2008).**
  https://www.sciencedirect.com/science/article/abs/pii/S0005109807000970 · DOI ⚠[VERIFY] · Supports: estimator design under quantization; naive LS biased. · Primary.
- **"Parametric System Identification Using Quantized Data," arXiv:1804.10015.**
  https://arxiv.org/abs/1804.10015 · Supports: uniform quantization → estimation bias (EIV view). · Primary.

### Uncertainty under temporal dependence (block bootstrap)
- **Künsch, H.R. (1989), "The Jackknife and the Bootstrap for General Stationary Observations," Annals of Statistics 17(3).**
  https://www.researchgate.net/publication/2355926 · DOI ⚠[VERIFY] · Supports: iid/analytic intervals underestimate variance for dependent data; moving-block bootstrap preserves dependence (our Phase 2C method). · Foundational.
- **Liu & Singh (1992), moving block bootstrap.** ⚠[VERIFY full citation] · Supports: same as above (independent MBB). · Foundational.

### Identifiability vs predictive accuracy (dissociation is known)
- **"Think before you fit: parameter identifiability, sensitivity and uncertainty in systems biology models," arXiv:2508.18853.**
  https://arxiv.org/abs/2508.18853 · Supports: identifiable ≠ predictive; weak identifiability undermines prediction. · Background.
- **"Parameter identifiability and model selection for PDE models of cell invasion," PMC10914513.**
  https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10914513/ · DOI ⚠[VERIFY] · Supports: good calibration fit ≠ prediction under new conditions. · Background.

### Datasets used
- **M100 ExaData, Nature Scientific Data (2023), DOI 10.1038/s41597-023-02174-3.** (context; not our primary Summit data.) · Primary dataset.
- **Summit long-term per-component power & thermal, OLCF, DOI 10.13139/OLCF/1861393.** https://doi.org/10.13139/OLCF/1861393 · Our primary dataset. · Primary dataset.

⚠ All [VERIFY] DOIs: confirm exact DOI/venue/year on the publisher page before the paper is submitted. Do not cite as final until verified.

---

## Novelty verdict

*(source: `v2_research/paper_analysis/novelty_verdict.md`)*

## Novelty Verdict

### Executive verdict
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

### What is definitely prior art [L]
- Quantization biases parameter estimation (errors-in-variables). P6–P8.
- iid/analytic CIs underestimate variance under temporal dependence; MBB fixes it. P9.
- Identifiable-but-not-predictive / good-fit-≠-prediction. P10, P11.
- HPC node thermal RC/ARX identification from real measurements **with 1°C
  quantization present**. P1–P3.

### What is partially differentiated (YELLOW)
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

### What appears genuinely differentiated (GREEN)
- **C4** comparing the measurement-induced τ bias against the **natural fleet
  distribution** (quantized 116 s below the entire 116-unit fleet minimum 205 s).
  No prior art found doing this quantitative artifact-vs-heterogeneity comparison.
  This is the strongest single differentiator.

### What we must NOT claim
Physical R·C; failure/degradation prediction; validated monitor; "unlearnable";
PINN superiority; a *new principle* (quantization bias / precision≠accuracy /
identifiability≠prediction are all known); causal socket explanation; that HPC
thermal ID is itself novel.

### Strongest defensible contribution
The **controlled, real-fleet quantitative comparison of measurement-induced τ
bias against natural unit-to-unit variation (C4), embedded in the identification-
vs-prediction dissociation (C5) and the online negative (C6)** — i.e., a caution
that measurement choices can bias identified thermal parameters beyond the range
of genuine hardware heterogeneity, while buying no residual predictability.

### Weakest contribution
**C2/C3 as standalone claims** — restating known quantization-bias and CI-
underestimation results; must be framed as demonstration-in-context, never as
discovery.

### Reviewer attack scenarios
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

### Recommended paper positioning
An **HPC/systems empirical limits study**: *"Measurement quality can bias the
identified thermal model of a supercomputer beyond natural fleet variation, and
better measurements do not make the residual more predictable."* A caution for
HPC thermal digital-twin calibration — not a method, not a monitor.

### Venue implications
HPC/systems workshops (SC/ICPP/CLUSTER-affiliated), *JPDC*/*FGCS*, or
reproducibility / negative-results / applied-scientific-ML tracks. **Not** a
flagship ML or novelty-driven venue. A short/workshop paper is the honest target.

### Kill criteria
Abandon/redirect only if: (a) a prior paper is found that already runs a
controlled measurement-quality ablation on HPC thermal ID **and** compares the
bias to fleet heterogeneity (would collapse C4) — not found so far; or (b) the
target venue requires methodological novelty the study does not have. Neither is
currently the case → proceed with the conservative framing.
