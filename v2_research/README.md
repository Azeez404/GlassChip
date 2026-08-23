# GLASSCHIP-V2 — Research Workspace

**Separate from and read-only w.r.t. frozen GLASSCHIP-V1.** No V1 file is
modified. V1 anchor `8473342129fb19f0` remains intact.

## Question

Can richer thermal *observations* make the thermal behaviour that was
unlearnable in V1 observable, and therefore learnable? Order enforced:
**observations → observability → physics → model → validation.**

## Status

| Stage | Result |
|---|---|
| V2 audit (prior) | M100 node-level metrics do not inform the V1 residual (out-of-sample) |
| Phase V2-1 — acquisition | **Frontier dataset verified UNSUITABLE** (facility-level, not per-node); no accessible alternative qualifies |
| GATE V2-α — observability | **Unrunnable** — no suitable richer dataset exists |
| Decision | Pivot to **D2 (longitudinal M100)**; execute **GATE B** (cross-record node identity) first |

## Contents

```
v2_research/
├── README.md                              this file
├── GLASSCHIP-V2-RESEARCH-AUDIT.md         prior audit (17 sections)
├── data_audit/
│   └── dataset_inventory.md               Phase V2-1 acquisition/verification record
├── reports/
│   ├── PHASE_V2_ALPHA_REPORT.md           why GATE V2-α is unrunnable
│   ├── V2_LITERATURE_AUDIT.md             2024-2026 literature
│   └── V2_DECISION.md                     decision table + single next action
├── phase2_residual_observability.py       prior audit's decisive experiment
├── phase2_results.json                    its results
├── data/  experiments/  figures/  literature/  scripts/   (staged for D2)
```

`data/raw/` and `data/processed/` are git-ignored (external datasets are not
redistributed).

## Reproducibility

- Environment: Python 3.13; pandas, pyarrow, numpy, duckdb, scikit-learn, torch.
- The observability experiment reads V1's frozen `ClassicalBaselineModel`
  read-only and evaluates with `TimeSeriesSplit` (out-of-sample only).
- Decision criterion is **out-of-sample** test R²; mutual information and
  in-sample fit are treated as non-evidence (they were high while test R² was
  negative).

## The single next action

See `reports/V2_DECISION.md`: pivot to the longitudinal M100 target (D2) and
begin with GATE B — acquire one further M100 record and prove cross-record node
identity before any pooling or modelling.
