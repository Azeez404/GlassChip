# GLASSCHIP — Paper Analysis Layer (Phase 3B)

Read-only, reproducible pipeline that turns the locked Phase 2A–2E results into
publication tables, figures, and a traceable manifest. It **does not** run
experiments, modify raw data, `src/`, or any Phase 2 artifact.

## Requirements
Minimal — this layer reads the frozen Phase 2 JSONs, so only **numpy** and
**matplotlib** are needed (see `requirements.txt`; stdlib otherwise). The raw
dataset and the heavier Phase-2 stack (polars/scikit-learn/torch/pyarrow) are
**not** required here.
```
python -m pip install -r v2_research/paper_analysis/requirements.txt
```

## Run
```
python v2_research/paper_analysis/run_all.py     # full reproduction + gate
python v2_research/paper_analysis/validate_results.py   # numbers only (44/44)
python v2_research/paper_analysis/verify_artifacts.py   # deliverables + residue scan
```
`run_all.py` steps: (1) verify frozen Phase 2 source JSONs exist → (2) validate
locked numbers (44/44) → (3) regenerate tables → (4) figures (PDF+PNG) →
(5) regenerate manifest → (6) verify paper artifacts. Exit 0 = GATE GREEN.
The raw dataset is **not** needed; it is only required to regenerate Phase 2
itself, which this runner never does. If a Phase 2 JSON is missing the runner
fails clearly and says so (it never downloads or fabricates data).

## Layout
```
paper_analysis/
├── config.py                  paths + LOCKED expected values + terminology
├── load_results.py            canonical data model (single source of numbers) + manifest
├── validate_results.py        44 cross-phase consistency checks (fails loudly)
├── make_tables.py             Tables 1–4 (markdown)
├── make_figures.py            Figures 1–6 (PDF + PNG)
├── verify_artifacts.py        deliverable existence + manuscript residue scan
├── run_all.py                 orchestrator (source-check → validate → regen → verify)
├── requirements.txt           minimal env (numpy, matplotlib)
├── artifact_inventory.md      Phase 2 source-of-truth inventory
├── claim_audit.md             [V]/[I]/[L] + forbidden-claim list
├── paper_results_manifest.json  metric → value → phase → figure/table → claim → class
├── figures/  tables/  reports/
```

The manuscript and its embedded copies of the figures/tables live under
`v2_research/paper/`; `run_all.py` regenerates into `paper_analysis/` and does
not modify the manuscript or `paper/figures/`.

## Traceability
Every table/figure derives from `load_all()`; no number is hand-typed. The
manifest records `metric → value → phase → destination → claim → classification`,
giving: Phase-2 experiment → locked JSON → loader → table/figure → paper claim.

## Terminology (mentor-facing)
"measurement quality" (not "telemetry fidelity"); "temperature and power
measurements" (not "telemetry"); τ = "how quickly temperature responds to power".

## Integrity
Raw SHA-256 `9898170b…996e`; frozen V1 baseline (HEAD 7cbfd1d); deterministic
seeds. Validation must print `data_ok=True` (GATE GREEN) or the paper numbers do
not match the locked results.
