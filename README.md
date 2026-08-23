# GLASSCHIP-V2

**An empirical HPC measurement-quality study on the Summit supercomputer.**
Manuscript complete and submission-ready.

---

## Research question

> On real supercomputer temperature and power measurements, how does measurement quality —
> temperature quantization, sampling rate, and spatial aggregation — affect identification of
> a first-order thermal model, and does higher measurement quality that sharpens parameter
> identification also make the unexplained residual dynamics more predictable out-of-sample?

Holding hardware and workload fixed, only the *measurements* are degraded (five conditions,
F0–F4), and the model is re-identified in each.

## Main findings

- **Measurement quality substantially changes the identified effective thermal response time
  τ**: about 394 s at full quality, 116 s under 1 °C quantization (0.29×), 910 s under 10 s→20 s
  downsampling (2.31×) — roughly a factor of eight across conditions on the same units.
- **The strongest result:** the quantization-induced estimate falls **below the entire
  full-quality range observed across all 116 sampled host-sockets** (minimum ≈ 205 s). A
  measurement choice can bias an identified parameter further than real unit-to-unit variation.
- **Better measurements do not buy predictability**: out-of-sample residual R² ≤ 0.066, near a
  permutation null, and no better at full quality than under degradation.
- **Extended 116-unit ablation (Phase 2F):** the degradation is *not* a constant per-unit
  factor, and spatial aggregation disturbs the rank ordering of units (Spearman ρ ≈ 0.49) far
  more than quantization or downsampling do (ρ ≈ 0.80).
- **F0 is a reference measurement regime, not physical ground truth.** An ideal first-order
  process would leave τ invariant under decimation; the observed shift indicates dynamics
  faster than the model represents.

This is a measurement-quality study. It is **not** a new model, a monitor, a digital twin, or
a physics-informed-ML paper.

## Repository layout

```
README.md                     this file
requirements.txt
docs/handovers/
  PROJECT_HANDOVER.md         full project history and state — read this second
src/baseline/                 frozen classical first-order estimator (V1 module,
                              imported read-only by the Phase 2 generators)
v2_research/
  README.md                   V2 pipeline guide
  paper/                      manuscript, figures, tables, references, claim audits
    manuscript.md             ** the paper **
  paper_analysis/             canonical analysis pipeline, validator, result manifest
  summit/                     Phase 2A–2F experiment code + locked JSON results
  data_audit/                 dataset provenance
```

## Reproduce the analysis

Regenerates every table, figure, and manifest entry from the locked Phase 2 result artifacts,
then validates them. **Requires no raw data.**

```bash
python v2_research/paper_analysis/run_all.py
```

Expected: `44/44 passed`, `PASS (23 checks)`, `GATE: GREEN (reproduced + validated)`.

Validation alone:

```bash
python v2_research/paper_analysis/validate_results.py
```

## Datasets are intentionally not committed

Both datasets are public and are referenced by local path, never redistributed here. `.gitignore`
excludes them deliberately.

| Dataset | Size | Where it must go locally |
|---|---|---|
| Summit per-component power and thermal (OSTI/OLCF DOI `10.13139/OLCF/1861393`, CC-BY-4.0) | ~12 GB | `v2_research/summit/raw/` → derived to `v2_research/summit/derived/cleaned/` |
| M100 ExaData (DOI `10.1038/s41597-023-02174-3`, CC-BY-4.0) — V1 only, context in V2 | ~1.2 GB | `data/raw/` |

Only the **derived JSON result artifacts** and provenance manifests are committed (~4 MB total).
Regenerating the Phase 2 results from raw data additionally requires the Summit archive and
`polars`.

Note: the public Summit release provides 10 s and 1 min means only — the original 1 Hz
measurements are **not** distributed. This bounds the fast dynamics any analysis of this archive
can resolve, and is discussed in the manuscript.

## Branches

| Branch | Contents |
|---|---|
| `main` | **GLASSCHIP-V2** — the current project (this README) |
| `backup/v1` | **GLASSCHIP-V1**, frozen at the `Release GLASSCHIP-V1.0` commit: 26 files, full V1 source, docs, handover, research summary, usage examples |
| `archive/exploratory-2026-08` | Historical exploratory work removed from `main` — PINN opportunity hunts and prototype, GPU/HBM coupling study, strategy/novelty audits, early V2 decision records |

**V1** asked whether a physics-informed neural network could learn thermal behaviour classical
first-order physics cannot already explain, on CINECA Marconi100 data. The answer was **no** — a
rigorous negative result. V1 is frozen; nothing in V2 depends on it except the classical
estimator in `src/baseline/`.

The `archive/` branch preserves later exploratory directions (a PINN prototype and a GPU/HBM
thermal-coupling study, both of which produced honest negative results). They are historical and
form no part of the V2 contribution.

## Licence and citation

Datasets are used under CC-BY-4.0 and cited in the manuscript. See
`v2_research/paper/references/references_block.md` for the verified reference list.
