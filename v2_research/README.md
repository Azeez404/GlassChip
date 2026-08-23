# GLASSCHIP-V2 — Summit measurement-quality study

The complete V2 research artifact: experiment code, locked results, analysis pipeline, and the
manuscript. See the repository root `README.md` for the findings summary.

## Layout

```
paper/                  the manuscript and everything it ships with
  manuscript.md         ** the paper **
  abstract.md           standalone abstract
  figures/              canonical Fig 1-6 (PDF + PNG)
  tables/               canonical Table 1-5
  references/           verified reference list (references_block.md)
  claims/               claim-to-evidence audits (auditability)

paper_analysis/         canonical analysis pipeline - the reproduction entry point
  run_all.py            validate -> tables -> figures -> manifest
  validate_results.py   44 locked numerical checks
  verify_artifacts.py   23 artifact-presence/consistency checks
  load_results.py       reads Phase 2 JSON, single source of truth
  make_tables.py        regenerates Table 1-4
  make_figures.py       regenerates Fig 1-6
  config.py             artifact paths and condition keys
  paper_results_manifest.json   provenance: every reported number -> source artifact + hash
  citation_evidence.md, claim_evidence_matrix.md, literature_matrix.md,
  novelty_verdict.md, related_work_outline.md, artifact_inventory.md

summit/                 Phase 2 experiments (generators + locked JSON results)
  scripts/              dataset inventory, derivation, Phase 1 audit, Phase 2A counterfactual
  counterfactual/       Phase 2A - frozen baseline, per-unit alpha/beta/gamma
  observability_ablation/  Phase 2B - F0-F4 ablation, 20 units  [FROZEN CANONICAL]
  phase2c_bootstrap/    Phase 2C - moving-block bootstrap
  phase2d_fleet/        Phase 2D - 116 sampled host-sockets at F0
  phase2e_streaming/    Phase 2E - causal online rolling-tau boundary
  phase2f_fleet_ablation/  Phase 2F - F0-F4 across all 116 units, paired per unit
  derived/manifests/    per-host cleaning provenance (JSON)
  metadata/, inventory/, feasibility/, logs/

data_audit/             human-readable dataset provenance
```

## Reproduce

From the repository root, with no raw data required:

```bash
python v2_research/paper_analysis/run_all.py
```

Expected tail: `44/44 passed`, `PASS (23 checks)`, `GATE: GREEN (reproduced + validated)`.

## Regenerating Phase 2 from raw data

Only needed if the raw Summit archive is present locally (~12 GB, see root README). Order:

```bash
python v2_research/summit/scripts/summit_derive.py
```
```bash
python v2_research/summit/observability_ablation/observability_ablation.py
```
```bash
python v2_research/summit/phase2f_fleet_ablation/phase2f_fleet_ablation.py
```

Phase 2C/2D/2E/2F all import Phase 2B read-only for their condition definitions, segmentation,
and estimator, so 2B must exist first. These scripts also import `src/baseline` (the frozen V1
classical estimator) read-only.

## Locked and frozen

Do not modify without a deliberate scientific decision:

- `src/baseline/` — the frozen first-order estimator, imported read-only.
- `summit/observability_ablation/` — Phase 2B canonical ablation; its result hash
  (`958b56653377`) is recorded in `paper_results_manifest.json` and checked on every run.
- All Phase 2 `*_results.json` — locked artifacts; the pipeline verifies their hashes.
- Random seeds (0 throughout), condition definitions F0–F4, the train/test split convention.

Phase 2F is **additive**: it imports Phase 2B without modifying it, writes only into its own
directory, and does not alter any previously reported value.

## Data policy

Raw and derived-parquet data are never committed; see the root `README.md`. What *is* committed
is the derived JSON result artifacts and provenance manifests (~4 MB), which is what makes the
paper reproducible without the 12 GB archive.
