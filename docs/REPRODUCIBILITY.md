# Reproducibility

## Reproduce the paper (no raw data required)

Regenerates every table, figure, and manifest entry from the frozen experiment results in
`artifacts/results/`, then validates them against locked expected values.

```bash
python scripts/run_all.py
```

Expected output tail:

```
44/44 passed; data_ok=True
PASS (23 checks)
GATE: GREEN (reproduced + validated)
```

Runtime under a minute. Requires only `numpy`, `pandas`, `matplotlib` (see `requirements.txt`).

The six pipeline stages: verify source artifacts and print their SHA-256 prefixes → validate 44
locked numbers → regenerate Tables 1-4 → regenerate Figures 1-6 → rebuild the results manifest →
verify paper artifacts and scan the manuscript for drafting residue.

## Determinism anchors

| Anchor | Value |
|---|---|
| Raw Summit archive SHA-256 | `9898170bed7f…996e` (recorded in `src/glasschip/config.py`) |
| Phase 2A result | `aab18fe9307a` |
| Phase 2B result (canonical ablation) | `958b56653377` |
| Phase 2C result | `c9cada6e9bbd` |
| Phase 2D result | `00fc262c5d4f` |
| Phase 2E result | `9360a802310f` |
| Random seeds | 0 throughout |

`scripts/run_all.py` prints each source hash on every run and warns if one drifts from the value
recorded in the manifest. Phase 2F re-runs reproduce bit-identical statistics
(ρ = 0.490501, CI [0.324411, 0.628841]).

## Re-running the experiments themselves

Only necessary if you want to regenerate `artifacts/results/` from the raw archive. Requires the
~12 GB Summit dataset locally plus `polars` and `torch`.

Place the archive at `data/summit/raw/`, or point `GLASSCHIP_SUMMIT_DERIVED` at an existing
derived tree. Then:

```bash
python experiments/data_prep/summit_derive.py
```
```bash
python experiments/phase2b_ablation.py
```
```bash
python experiments/phase2f_ablation_116.py
```

Phases 2C, 2D, 2E and 2F import `phase2b_ablation` read-only for their condition definitions,
segmentation, and estimator, so 2B must exist first. All experiment scripts import
`glasschip.models.ClassicalBaselineModel` — the frozen first-order estimator — read-only.

## What must not change

- `src/glasschip/models/classical_baseline.py` — the frozen estimator.
- `artifacts/results/*.json` — locked experiment outputs; hashes are checked on every run.
- Condition definitions F0-F4, the seeds, and the τ = −Δt/ln α convention.
- The locked expected values and tolerances in `src/glasschip/config.py`.

Phase 2F is **additive**: it imports Phase 2B without modifying it and altered no previously
reported value.

## Datasets are not committed

| Dataset | Size | Expected local path |
|---|---|---|
| Summit per-component power and thermal (OSTI/OLCF DOI `10.13139/OLCF/1861393`, CC-BY-4.0) | ~12 GB | `data/summit/raw/` → derived to `data/summit/derived/cleaned/` |
| M100 ExaData (DOI `10.1038/s41597-023-02174-3`, CC-BY-4.0) — V1 only, context in V2 | ~1.2 GB | `data/raw/` |

Both are public and are referenced by local path, never redistributed. `.gitignore` excludes
them deliberately. Only the derived JSON results and provenance manifests (~4 MB) are committed —
which is what makes the paper reproducible without the archive.

The public Summit release provides **10 s and 1 min means only**; the original 1 Hz measurements
are not distributed. This bounds the fast dynamics any analysis of this archive can resolve and
is discussed in manuscript §4.1 and §9.
