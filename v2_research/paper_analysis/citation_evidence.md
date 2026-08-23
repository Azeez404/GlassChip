# Citation Evidence

Each entry: citation · stable URL · DOI (⚠ = verify before use, not fabricated) ·
exact claim it supports · evidence type. No DOI is asserted without verification.

## HPC thermal identification (closest prior art)
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

## Quantized system identification (mechanism = quantization biases parameters)
- **Wang, Yin, Zhao, "System Identification with Quantized Observations."**
  https://www.researchgate.net/publication/229101105 · DOI ⚠[VERIFY] · Supports: quantized observations bias/complicate parameter estimation. · Primary/background.
- **"Asymptotically efficient parameter estimation using quantized output observations," Automatica (2008).**
  https://www.sciencedirect.com/science/article/abs/pii/S0005109807000970 · DOI ⚠[VERIFY] · Supports: estimator design under quantization; naive LS biased. · Primary.
- **"Parametric System Identification Using Quantized Data," arXiv:1804.10015.**
  https://arxiv.org/abs/1804.10015 · Supports: uniform quantization → estimation bias (EIV view). · Primary.

## Uncertainty under temporal dependence (block bootstrap)
- **Künsch, H.R. (1989), "The Jackknife and the Bootstrap for General Stationary Observations," Annals of Statistics 17(3).**
  https://www.researchgate.net/publication/2355926 · DOI ⚠[VERIFY] · Supports: iid/analytic intervals underestimate variance for dependent data; moving-block bootstrap preserves dependence (our Phase 2C method). · Foundational.
- **Liu & Singh (1992), moving block bootstrap.** ⚠[VERIFY full citation] · Supports: same as above (independent MBB). · Foundational.

## Identifiability vs predictive accuracy (dissociation is known)
- **"Think before you fit: parameter identifiability, sensitivity and uncertainty in systems biology models," arXiv:2508.18853.**
  https://arxiv.org/abs/2508.18853 · Supports: identifiable ≠ predictive; weak identifiability undermines prediction. · Background.
- **"Parameter identifiability and model selection for PDE models of cell invasion," PMC10914513.**
  https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10914513/ · DOI ⚠[VERIFY] · Supports: good calibration fit ≠ prediction under new conditions. · Background.

## Datasets used
- **M100 ExaData, Nature Scientific Data (2023), DOI 10.1038/s41597-023-02174-3.** (context; not our primary Summit data.) · Primary dataset.
- **Summit long-term per-component power & thermal, OLCF, DOI 10.13139/OLCF/1861393.** https://doi.org/10.13139/OLCF/1861393 · Our primary dataset. · Primary dataset.

⚠ All [VERIFY] DOIs: confirm exact DOI/venue/year on the publisher page before the paper is submitted. Do not cite as final until verified.
