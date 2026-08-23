# Literature Matrix — closest prior art

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

## Overlap / Difference (decision-critical)
- **P1–P3 (closest prior art).** *Overlap:* HPC node thermal RC/ARX identification from real measurements **with 1°C temperature quantization present.** *Difference:* they **overcome** quantization to obtain an *accurate* model; they do **not** run a controlled same-hardware ablation, do **not** quantify τ **bias** across measurement-quality conditions, do **not** show precise-but-biased uncertainty, do **not** compare artifact bias to fleet heterogeneity, and do **not** test residual OOS predictability or online monitoring. → threatens C1/C2 framing, not C3–C6.
- **P6–P8 (quantized system ID).** *Overlap:* quantization biases parameter estimates (errors-in-variables). *Difference:* generic/theoretical, not thermal, not HPC, no fleet, no fidelity-vs-heterogeneity, no dissociation. Establishes the **mechanism** [L]; makes our *phenomenon* expected, our *demonstration on real HPC fleet* the increment.
- **P9 (block bootstrap).** *Overlap:* iid/analytic intervals underestimate variance for dependent data; MBB is the fix. *Difference:* our Phase 2C **uses** this; it makes "analytic CI narrower than bootstrap" **expected/textbook**, so C3's novelty is the *bias* (precision≠accuracy) on HPC thermal, not the CI-width gap.
- **P10–P11 (identifiability vs prediction).** *Overlap:* good-fit parameters ≠ good prediction under new conditions is known. *Difference:* systems-biology/ODE/PDE, not measurement-quality-controlled, not HPC, not OOS residual on real fleet. Makes our C5 a *domain demonstration*, not a new principle.
- **P4/P5/P12/P13.** Context: supercomputer temperature modeling and the datasets we use; none run the measurement-quality ablation.
