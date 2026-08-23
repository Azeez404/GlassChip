# GLASSCHIP Paper Package (Phase 3D)

Publication draft workspace. **Additive only** — it reads locked Phase 2A–2E
results and the Phase 3B/3C analysis; it modifies none of them.

## Positioning
An **HPC/systems empirical limits & reproducibility study** — how measurement
quality affects thermal-model identification on a supercomputer, and whether
better measurements make the residual more predictable. **Not** a PINN paper, a
new model, a monitor, or a degradation/failure study.

## Source artifacts (source of truth)
- Experiments: `v2_research/summit/{counterfactual,observability_ablation,phase2c_bootstrap,phase2d_fleet,phase2e_streaming}/*.json`
- Canonical analysis: `v2_research/paper_analysis/` (`paper_results_manifest.json`, `tables/`, `figures/`, `validate_results.py`)
- Literature/novelty: `v2_research/paper_analysis/{literature_matrix,citation_evidence,related_work_outline,claim_evidence_matrix,novelty_verdict}.md`

## Phases used
2A frozen baseline · 2B measurement-quality ablation (F0–F4) · 2C moving-block
bootstrap · 2D 116-unit fleet · 2E online rolling-τ boundary · 3B analysis
pipeline · 3C literature/novelty audit.

## Terminology
"measurement quality" (not telemetry fidelity); "temperature and power
measurements" (not telemetry); "effective thermal response time (effective τ)",
defined as an identification parameter, never a physical R·C constant.

## Locked numbers (trace to paper_results_manifest.json)
τ: F0 393.8 / F1 115.8 / F2 910.5 / F3 282.6 / F4 352.0 s;
bootstrap: 393.9 / 115.6 / 908.5 / 282.9 / 351.8 s;
ratios: 1.00 / 0.294 / 2.306 / 0.718 / 0.893.
Residual HGB OOS R²: 0.034 / 0.055 / 0.006 / 0.046 / 0.066 (max 0.066).
Fleet: 116/116; median 439; mean 552; std 365; P05 275; P95 1200; min 205; max 2596;
socket r 0.789; median rel diff 24.2%. Key: quantized 116 < fleet min 205.
Streaming: 0.041 ms/window; OOS 0.102 ≈ baseline 0.103; spread 0.62; confound 0.004.

## Reproducibility command
`python v2_research/paper_analysis/run_all.py`  → validate (44/44) → tables → figures → manifest.
Raw SHA-256 `9898170b…996e`; frozen V1 (HEAD 7cbfd1d); seeds 0.

## Citation verification status
All DOIs in `citation_evidence.md` marked **⚠[VERIFY]** — confirm on publisher
pages before finalizing References. None fabricated.

## Forbidden claims
Physical R·C; "unlearnable"; failure/degradation/RUL prediction; validated
monitor / "τ monitoring works"; PINN as contribution / "our PINN failed"; causal
socket/host explanation; universal or digital-twin framework; any causal claim
outside the within-Summit ablation; presenting known principles as novel.

## Layout
```
paper/
├── manuscript.md      section skeleton (objectives + [DRAFT PENDING])
├── abstract.md        abstract bullet plan
├── figures/           canonical Fig1-6 (PDF+PNG), copied from paper_analysis
├── tables/            canonical Table1-4, copied from paper_analysis
├── references/        (bib to be assembled after [VERIFY] pass)
├── claims/claim_audit.md   mandatory claim audit
├── drafts/            per-section drafts (STEP 3+)
└── README.md
```

## Manuscript status
STEP 2 complete: scaffold + skeleton + claim audit + canonical figs/tables.
No prose drafted. Next (on approval): STEP 3 Abstract + Introduction.
