# PHASE 3B — Reproducible Paper-Analysis Pipeline: Report

## 1. Implementation status
Complete. A read-only pipeline under `v2_research/paper_analysis/` loads the
locked Phase 2A–2E JSON artifacts once into a canonical data model and
regenerates all paper tables, figures (PDF+PNG), a machine-readable manifest,
and a claim audit. No experiment was rerun; no Phase 2 artifact, raw data, or
`src/` was modified. GATE: **GREEN** (44/44 validation checks pass).

## 2. Artifact inventory
See `artifact_inventory.md`. Source-of-truth = the five Phase 2 result JSONs;
exploratory PNGs/MDs in each phase dir are superseded by the canonical
`figures/` and `tables/` here.

## 3. Cross-phase consistency
`validate_results.py`: **44/44 pass**. Verifies τ points (394/116/910/283/352),
bootstrap medians (394/116/909/283/352), ratios (1.00/0.29/2.31/0.72/0.89),
analytic vs bootstrap CoV/CI (bootstrap wider), F1 precise-but-biased, residual
HGB max 0.066 with all perm-null p95 < 0 and "degraded ≥ F0", fleet stats
(116, 439/552/365, IQR 376–588, P05/P95 275/1200, min/max 205/2596, socket
0.789/24.2%), 116 < 205 (quantized below fleet min), streaming OOS≈baseline,
spread 0.62, power-confound ~0, runtime 0.041 ms.

## 4. Generated tables (tables/)
table01_conditions · table02_tau_identification · table03_residual_prediction ·
table04_fleet_streaming.

## 5. Generated figures (figures/, PDF+PNG)
fig01_setup · fig02_tau_fidelity (main) · fig03_residual_prediction ·
fig04_fleet_tau · fig05_fidelity_vs_fleet · fig06_streaming_boundary.

## 6. Claim audit
See `claim_audit.md`. All supported claims tagged [V]; mechanism claims tagged
[I]; forbidden-claim list enforced (no physical R·C, no failure/degradation
prediction, no validated monitor, "not materially learnable" not "unlearnable",
no causal socket claim).

## 7. Discrepancies discovered
None. Every paper number reproduces from the locked artifacts within tolerance.

## 8. Missing source artifact
None. All five phase JSONs (+ phase2d_units.json for the fleet histogram) present.

## 9. Reproducibility instructions
`python v2_research/paper_analysis/run_all.py` → validate → tables → figures →
manifest. Deterministic. Raw SHA-256 `9898170b…996e`; frozen V1 (HEAD 7cbfd1d).
Environment: torch 2.13 CPU, sklearn 1.9, polars 1.43 (xgboost absent → HGB used
in Phase 2B, documented).

## 10. Final gate
**GREEN** — analysis pipeline complete; all locked Phase 2 results reproduced
from artifacts. No paper prose written; stopping per instruction.
