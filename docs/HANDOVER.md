# GLASSCHIP — Project Handover

**Audience:** a programmer or AI assistant picking this repository up cold.
**Read this after the root `README.md`.** It records the full history, the current state, and
the decisions behind the repository layout.

**Last updated:** 2026-08-23, after the second (structural) repository reorganisation described in §6.
The V1/V2 branch separation from the first pass is unchanged.

---

## 1. Status in one paragraph

GLASSCHIP-V2 is an empirical study of **how the quality of a supercomputer's own temperature
and power measurements affects the thermal model you can identify from them**, on Oak Ridge's
Summit. **The manuscript is complete and submission-ready**: all prose drafted, all 27
previously-unverified citations resolved, the extended 116-unit Phase 2F ablation integrated,
and the canonical pipeline reproducing GREEN (44/44 numerical checks, 23 artifact checks).
V1 is frozen on its own branch. Later exploratory directions (a PINN prototype, a GPU/HBM
coupling study) produced honest negative results and live on an archive branch, out of the
main line. **The single next action is to submit the paper** — target FGCS or JPDC (rolling
submission).

---

## 2. Branch architecture — the key decision

```
main                          = current GLASSCHIP-V2  (the paper + its pipeline)
backup/v1                     = minimal preserved GLASSCHIP-V1
archive/exploratory-2026-08   = historical exploratory work removed from main
```

| Branch | Commit | What it holds |
|---|---|---|
| `main` | descends from V1.0 → archive → cleanup | V2 only. Clean, publication-ready. |
| `backup/v1` | `7cbfd1d` "Release GLASSCHIP-V1.0" | Exactly the 26-file V1 release: `src/` (all V1 modules), `docs/RESEARCH_SUMMARY.md`, `docs/handovers/HANDOVER.md`, `examples/`, `reports/validation/`, `README.md`, `requirements.txt`, `.gitignore`. No datasets, no debris. |
| `archive/exploratory-2026-08` | `f5447bc` | Full pre-cleanup tree — see §5. |

**No history was rewritten and nothing was force-pushed.** `backup/v1` simply points at the
existing V1.0 release commit, which was already a clean minimal V1 — duplicating it would have
been pointless. `main` moved *forward* from that commit (fast-forward; verified with
`git merge-base --is-ancestor`), so the V1 release commit remains in `main`'s ancestry and is
not deleted from history.

**The V1 handover (`docs/handovers/HANDOVER.md`) now lives only on `backup/v1`.** It was
removed from `main` because it documents V1, not the current project. Retrieve it with:

```bash
git show backup/v1:docs/handovers/HANDOVER.md
```

---

## 3. What V1 was, and what V2 still needs from it

**V1** asked whether a physics-informed neural network could learn thermal behaviour that
classical first-order physics cannot already explain, using CINECA Marconi100 (M100 ExaData,
record `21-03`). **The answer was no** — a rigorous negative result. V1 is **frozen**.

**V2's only dependency on V1 is `src/glasschip/models/`** — the frozen classical first-order estimator
(`ClassicalBaselineModel`), imported read-only by the Phase 2B/2D/2F generators. That module is
the sole V1 code retained on `main`; it imports nothing but numpy and was verified to import
standalone after the other V1 modules were removed.

`src/pinn/thermal_pinn.py` (V1's PINN) is **not** on `main`. Note for anyone tempted to revive
it: it already implements a quantization-aware dead-zone data loss plus an ODE residual physics
loss, and it underperformed. That is settled in-house, on `backup/v1`.

---

## 4. GLASSCHIP-V2 — the current project

### 4.1 Question and findings

> How does measurement quality — temperature quantization, sampling rate, spatial aggregation —
> affect identification of a first-order thermal model, and does higher measurement quality also
> make the unexplained residual more predictable?

Five conditions on fixed hardware and workload: **F0** full quality · **F1** 1 °C quantization ·
**F2** 10 s→20 s downsampling · **F3** hottest-core proxy · **F4** combined.

- τ: F0 393.8 s, F1 115.8 s (0.29×), F2 910.5 s (2.31×), F3 282.6 s, F4 352.0 s.
- **Headline (C4):** the quantized estimate (116 s) falls below the entire full-quality range
  observed across all 116 sampled host-sockets (min 205 s).
- Residual OOS R² ≤ 0.066, near a permutation null — better measurements do not buy
  predictability.
- Online rolling-τ: cheap (0.041 ms/window) but not a useful standalone monitor.
- **Phase 2F (116 units, paired):** degradation is not a constant per-unit factor; spatial
  aggregation disturbs unit rank ordering (ρ ≈ 0.49 [0.32, 0.63]) far more than quantization
  (0.80) or downsampling (0.82).

### 4.2 Two interpretive positions that must not be lost

1. **F0 is a reference measurement regime, not physical ground truth.** An ideal first-order
   process leaves τ invariant under decimation, so F2's 394→910 s shift indicates dynamics
   faster than the model represents. §7.1 of the manuscript explains this; all comparisons are
   relative to a fixed identification convention at F0.
2. **No claim of measurement-induced homogenisation.** τ = −Δt/ln α is strongly nonlinear, so
   τ-space dispersion moves for algebraic reasons. F1's apparent narrowing in τ (IQR ratio
   0.370) *reverses* in α (3.315). Only F3 narrows in both. Any future population-spread claim
   must be checked in α-space or restricted to rank statistics.

### 4.3 Validation status — GREEN

```bash
python scripts/run_all.py
```
Last run after cleanup: source hashes matched, **44/44 numerical checks passed**,
tables and figures regenerated, manifest rebuilt (33 rows), **23 artifact checks PASS**,
`GATE: GREEN (reproduced + validated)`.

Canonical hashes (unchanged by the cleanup): manifest `c999514568e1ab20`, Phase 2B
`958b56653377bd39`, Phase 2D `00fc262c5d4f826d`.

### 4.4 Locked / sacred

`src/glasschip/models/`; Phase 2A–2F `*_results.json`; condition definitions F0–F4; seeds (0);
the τ = −Δt/ln α convention; `paper_analysis/` logic. Phase 2F is **additive** — it imports
Phase 2B read-only and altered no previously reported value.

---

## 5. What was removed from `main`, and where it went

All of the following is preserved on `archive/exploratory-2026-08` (commit `f5447bc`) and in
git history. None of it is required by the manuscript or the reproduction pipeline; each was
verified by tracing references before deletion.

| Removed from `main` | Why |
|---|---|
| `research_pinn_chip/` | PINN opportunity hunts + prototype. **KILLED**: PINN 27.81 °C RMSE vs XGBoost 4.44 °C, physics-induced runaway. All 30 sanity checks passed, so a real negative result. |
| `research_hbm_thermal/` | GPU/HBM two-node coupling study. **KILLED**: two-node beat one-node on 0/8 traces; physically admissible 1/8; coupling lag unresolvable at 10 s in 8/8. |
| `src/alignment/` + `tests/` | Additive M100 causal as-of alignment layer. Good engineering, tested, but unused by the V2 manuscript. |
| `v2_research/paper/{SUBMISSION_STRATEGY,NOVELTY_IMPACT_UPGRADE,PINN_SCIENTIFIC_ML_REDESIGN}_AUDIT.md`, `RESEARCH_OPPORTUNITY_HUNT.md` | Strategy/novelty audits. Referenced by nothing in the manuscript or pipeline. |
| `v2_research/paper/drafts/` | Superseded per-section drafts; `manuscript.md` is complete. |
| `v2_research/reports/`, `GLASSCHIP-V2-RESEARCH-AUDIT.md` | Early V2 decision records. |
| `v2_research/d2_longitudinal/`, `phase2_residual_observability.py`, `phase2_results.json` | Early V2 exploration, superseded by the `summit/` phases. Unreferenced by the manuscript. |
| V1 modules: `src/{loader,preprocessing,screening,validator,visualization,pinn}/`, `examples/`, `reports/validation/`, `docs/RESEARCH_SUMMARY.md`, `docs/handovers/HANDOVER.md` | V1 only. Preserved on `backup/v1`. |
| `__pycache__/`, empty directories | Generated clutter / empty directories. |

**Kept deliberately despite looking auxiliary:** `paper/claims/` and
`paper_analysis/{citation_evidence,claim_evidence_matrix,literature_matrix,novelty_verdict,related_work_outline,artifact_inventory}.md`
— these are the claim-to-evidence trail that lets a reviewer or successor check *why* the paper
makes each claim; they now live in `docs/EVIDENCE.md` and `docs/RELATED_WORK.md`. Dataset
provenance is consolidated in `docs/DATA_PROVENANCE.md`.

---

## 6. Final repository structure (`main`)

Reorganised by **purpose**, not by file type, in a second cleanup pass after the V1/V2 split.
The former `v2_research/` tree is gone; its contents were redistributed as follows.

```
README.md  requirements.txt  .gitignore
docs/          HANDOVER  METHODOLOGY  REPRODUCIBILITY  DATA_PROVENANCE  EVIDENCE  RELATED_WORK
src/glasschip/ config.py + models/ analysis/ validation/     (library code)
experiments/   phase2a..2f entry points + data_prep/          (experiment code)
paper/         manuscript/ figures/ tables/ references/       (paper deliverables)
artifacts/     results/ manifests/ validation/                (generated outputs)
scripts/       run_all.py                                     (reproduction entry point)
data/          gitignored - Summit ~12 GB, M100 ~1.2 GB
```

**Key moves.** `v2_research/paper_analysis/*.py` → `src/glasschip/{analysis,validation}/` and
`config.py` → `src/glasschip/`; `src/glasschip/models/` → `src/glasschip/models/`;
`artifacts/results/*/[phase].py` and `summit/scripts/*.py` → `experiments/`;
`v2_research/paper/` → `paper/`; all `*_results.json` → `artifacts/results/` under phase-named
files; manifests/metadata/inventory JSON → `artifacts/manifests/`; the 12 GB dataset →
`data/summit/`.

**Path handling changed.** `src/glasschip/config.py` now resolves every path relative to the
repository root via `Path(__file__).parents[2]`, so the pipeline runs from any working
directory. The dataset location is overridable with `GLASSCHIP_SUMMIT_DERIVED`. Experiment
scripts import `glasschip.models.ClassicalBaselineModel` and each other as flat siblings
(`import phase2b_ablation as p2b`).

**Deduplicated.** `paper/figures` and `paper_analysis/figures` previously held byte-identical
copies of the same 12 files; verified identical by SHA-256, then reduced to the single canonical
copy under `paper/`. Same for tables. The pipeline now writes directly into `paper/`.

**Documentation merged.** Fifteen scattered Markdown files became four: six claim/consistency
audits → `docs/EVIDENCE.md`; four literature/novelty documents → `docs/RELATED_WORK.md`; five
inventory/integrity reports → `docs/DATA_PROVENANCE.md`; plus new `METHODOLOGY.md` and
`REPRODUCIBILITY.md`. Per-directory READMEs were retired into these.

**Also removed** (all recoverable from the archive branch): 15 per-phase diagnostic PNGs and 5
per-phase tables, none used by the manuscript and all regenerable from the committed JSON.

## 7. Datasets — intentionally not committed

| Dataset | Size | Local path | Committed? |
|---|---|---|---|
| Summit power/thermal (DOI `10.13139/OLCF/1861393`, CC-BY-4.0) | ~12 GB | `artifacts/results/raw/`, derived to `derived/cleaned/` | **No** |
| M100 ExaData (DOI `10.1038/s41597-023-02174-3`, CC-BY-4.0) | ~1.2 GB | `data/raw/` | **No** |

Only derived JSON results and provenance manifests are committed — which is precisely what makes
the paper reproducible without the 12 GB archive. `.gitignore` also excludes all `*.parquet` and
`*.csv` as defence in depth; the ignored CSVs are regenerable summaries of committed JSON.

**The public Summit release provides 10 s and 1 min means only — the original 1 Hz measurements
are not distributed.** This is stated in manuscript §4.1 and bounds what any analysis of this
archive can resolve. Do not claim otherwise.

---

## 8. Next actions

1. **Submit the manuscript.** `paper/manuscript/manuscript.md`. Target **FGCS** or **JPDC**
   (rolling). This is the only near-certain outcome in the portfolio.
2. Optional strengthening if a conference is preferred: CCGrid 2027 (abstract ~24 Nov 2026) or
   IPDPS 2027 Measurements track (abstract ~1 Oct 2026) — **verify those dates before relying on
   them**; they were current as of August 2026.
3. **Do not** revive PINNs, build a benchmark, or claim the alignment module as a contribution.
   Four structurally distinct neural directions were evaluated and all failed; the reasoning is
   preserved on the archive branch.

---

## 9. Working principles that produced this repository

- **Verify data before designing around it.** Several ideas died in minutes because a channel
  was all zeros, a signal was confounded, or a dataset had one device.
- **Pre-register kill conditions and honour them.** No rescue tuning.
- **Validate tooling on synthetic ground truth** so a negative result is a statement about the
  data, not the code.
- **Delete on evidence, not on filename.** Every removal in §5 was preceded by a reference trace.
- **A negative result, honestly established, is a real outcome.** Three of the project's four
  scientific conclusions are negative, which is why the surviving positive one is credible.
