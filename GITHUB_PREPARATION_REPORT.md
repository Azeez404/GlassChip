# GLASSCHIP-V1 — GitHub Preparation Report

**Status: GITHUB READY**, with one action required by you before the first
push. See §1.

No commit was created, no remote configured, nothing pushed.

---

## 1. ⚠️ ACTION REQUIRED — 1.1 GiB of orphaned dataset blobs in `.git`

`.git/objects` holds **359 loose objects totalling 1.10 GiB**, while the
repository has **zero commits, zero refs, and an empty index**.

```
git count-objects -vH
  count: 359
  size: 1.10 GiB
  in-pack: 0
```

Largest orphans: **575 MB**, 18 MB, 14 MB, 14 MB, 13 MB … — these are the
dataset `.tar` and Parquet files. Someone ran `git add` against `data/` at
some point and unstaged it. The blobs were written and never collected.

**Impact assessment — measured, not assumed:**

| Question | Answer |
|---|---|
| Will these be pushed to GitHub? | **No.** Push transmits only objects reachable from the refs being pushed. These are reachable from nothing. |
| Will a cloner receive them? | **No.** |
| Does it bloat the local repository? | **Yes — 1.1 GiB.** |
| Is it a latent hazard? | **Yes.** It proves `git add` has already swallowed the dataset once. |

**Safe to remove.** With no commits and no refs, every one of these objects
is unreachable by definition, and the source files still exist on disk under
`data/`.

```bash
git prune --expire=now
git gc --prune=now --aggressive
```

Expected result: `.git` drops from ~1.2 GiB to well under 1 MiB.

**I did not run this.** It is destructive git plumbing and was not in the
task's scope. Run it yourself before the first commit.

---

## 2. Files to commit — 58 files, 2.3 MB

| Area | Files | Size | Rationale |
|---|---|---|---|
| `src/` | 11 | 378 K | The locked pipeline. 4 packages + 7 modules. |
| `examples/` | 4 | 20 K | One runnable example per layer. |
| `docs/` | 7 | 84 K | Handover, architecture, module documentation. |
| `reports/` | 5 | 64 K | Dataset and validation findings. |
| `assets/` | 18 | 1.9 M | 9 EDA figures, 7 node-15 figures, 2 distribution images. |
| `archive/` | 11 | 129 K | Provenance — see §2.1. |
| Root | 2 | 6 K | `README.md`, `.gitignore`. |

Largest single file: `assets/plots/eda/05_missing_values.png` at 231 KB.
All assets are scientifically useful figures already referenced by the
reports, and are small enough to version.

### 2.1 On committing `archive/`

`archive/` was in neither the MUST-COMMIT nor MUST-NOT-COMMIT list, so this
was a judgement call.

**Committed**, because:

- `archive/exploration/` (3 scripts) produced `reports/dataset/*.md`.
  Committing them makes those reports reproducible rather than assertions.
- `archive/battery_project_v0/` (8 files) is the provenance of the project's
  pivot. `README.md` states plainly it is not a specification.
- Combined cost is 129 KB.

If you disagree, one line in `.gitignore` (`archive/`) reverses it.

---

## 3. Files ignored

| Category | Pattern | Measured |
|---|---|---|
| **Dataset** | `data/` | 1.15 GB, 342 files |
| Dataset formats anywhere | `*.parquet` `*.csv` `*.h5` `*.hdf5` `*.feather` | defence in depth |
| Archives | `*.tar` `*.tar.*` `*.zip` `*.7z` `*.gz` `*.bz2` `*.xz` `*.rar` | 575 MB `21-03.tar` |
| Default pipeline output | `/visualizations/` `/eda_plots/` `/results/` | landmine paths |
| Python | `__pycache__/` `*.py[cod]` `build/` `dist/` `*.egg-info/` | regenerable |
| Virtualenvs | `.venv/` `venv/` `env/` `ENV/` `.conda/` | — |
| Test artefacts | `.pytest_cache/` `.mypy_cache/` `.ruff_cache/` `.coverage` `htmlcov/` | — |
| Notebooks | `.ipynb_checkpoints/` `*-checkpoint.ipynb` | — |
| Logs / temp | `*.log` `*.tmp` `*.bak` `*.swp` `*~` `tmp/` | — |
| OS | `.DS_Store` `Thumbs.db` `desktop.ini` `$RECYCLE.BIN/` | — |
| IDE | `.vscode/` `.idea/` | — |
| Secrets | `.env` `*.pem` `*.key` `credentials.json` | precautionary |

### 3.1 Note on `/visualizations/`

`ThermalVisualizer` defaults to `output_dir="visualizations"`. Called
without an explicit path from the repository root, it creates
`./visualizations/`. That path is ignored so stray generated figures cannot
be committed by accident. The curated copies live in
`assets/plots/visualization/` and **are** committed.

### 3.2 Note on the blanket `*.csv`

`*.csv` is ignored repository-wide because the exporter emits CSV node
datasets. If a small reference or config CSV is ever needed, add a negation
**before** the general rule:

```gitignore
!configs/some_reference.csv
```

---

## 4. Verification

### 4.1 Dataset leak — PASS

```
dataset-format files staged: 0
files under data/:           0
```

Explicit `git check-ignore` confirmation:

| Path | Result |
|---|---|
| `data/raw/21-03.tar` | IGNORED |
| `data/exports/Node_15.parquet` | IGNORED |
| `data/exports/Node_15.csv` | IGNORED |
| `data/raw/21-03/…/metric=p0_power/a_0.parquet` | IGNORED |

And the inverse — nothing that must ship is ignored:

| Path | Result |
|---|---|
| `src/loader/loader.py` | tracked |
| `examples/loader_example_usage.py` | tracked |
| `README.md`, `.gitignore` | tracked |
| `assets/plots/eda/01_temperature_distributions.png` | tracked |
| `reports/dataset/dataset_report.md` | tracked |
| `docs/handovers/HANDOVER.md` | tracked |

### 4.2 Portability — PASS

A clone was simulated by copying **only** the files git would track into a
clean directory outside the project.

| Check | Result |
|---|---|
| Files copied | 58 |
| Size | 2.4 MB |
| `data/` present in clone | **No** (correct) |
| `from loader import DatasetLoader` | OK |
| `from validator import DatasetValidator` | OK |
| `from preprocessing import …` | OK |
| `from visualization import …` | OK |

All four packages import in a data-free clone.

### 4.3 Graceful failure without the dataset — PASS

Running an example in the clone before downloading data:

```
loader.loader.DatasetLoaderError: Dataset path does not exist: ...\data\raw\21-03
```

A named exception with the exact expected path — actionable, not a
traceback into library internals.

### 4.4 Reproducibility — PASS

The clone was pointed at a separately-downloaded dataset and the full
pipeline run:

| | Original repo | Simulated clone |
|---|---|---|
| Frame shape | `(11166, 5)` | `(11166, 5)` |
| **SHA-256 (first 16)** | `8473342129fb19f0` | **`8473342129fb19f0`** |
| Segments | `61.978 h / 11157`, `0.044 h / 9` | identical |
| Validator verdict | `FAIL` | `FAIL` |

**A clone of committed files plus an independently downloaded dataset
reproduces the pipeline byte-for-byte.** This is the task's stated success
condition and it is met.

### 4.5 Locked implementations — PASS

SHA-256 compared against the post-reorganisation baseline:

| Module | Result |
|---|---|
| `loader.py` | UNCHANGED |
| `validator.py` | UNCHANGED |
| `metric_selector.py` | UNCHANGED |
| `preprocessor.py` | UNCHANGED |
| `timeseries_builder.py` | UNCHANGED |
| `exporter.py` | UNCHANGED |
| `visualizer.py` | UNCHANGED |

**All 7 locked modules byte-identical. No scientific behaviour touched.**

### 4.6 Secret scan — PASS

Repository-wide grep for `api_key`, `secret`, `password`, `token =`, and
PEM private-key headers across all tracked files returned one hit:
`.gitignore` itself, which contains those words as *patterns*. No credential
material exists.

---

## 5. README changes

The README was missing content the task requires. Three sections added; no
existing section altered.

| Required item | Before | After |
|---|---|---|
| What is GLASSCHIP-V1 | present | unchanged |
| Repository structure | present | unchanged |
| **Dataset requirements** | **missing** | **added** — source, DOIs, licence, record, size |
| **How to set up** | partial | **added** — clone, venv, `pip install` |
| **How to download the dataset** | **missing** | **added** — Zenodo, target tree, verification command |
| How to run examples | present | extended with generated-output paths |

Also added a reproducibility check block so a cloner can confirm their setup
against `8473342129fb19f0`. **That checksum was verified true at the time of
writing**, not asserted.

README is 202 lines. No scientific narrative, no future versions, no
abstract.

---

## 6. Repository observations

1. **Committable content is 2.3 MB against 1.15 GB of data** — a 500:1
   ratio. The separation is clean.
2. **`git` currently has no commits.** Branch `main` exists but is unborn.
3. **Empty directories will not survive a clone.** Git cannot track them.
   These vanish: `configs/`, `tests/`, `notebooks/`,
   `docs/specifications/`, `reports/preprocessing/`,
   `reports/visualization/`, `data/processed/`.
   Not a functional problem — `Exporter` and `ThermalVisualizer` both
   `mkdir(parents=True, exist_ok=True)` on their output paths. If you want
   them preserved, add a `.gitkeep` to each. I did not, because the task
   restricted new files to three.
4. **No packaging metadata.** Imports rely on `src/` being on `sys.path`,
   handled by the example bootstraps or `PYTHONPATH=src`. Adding
   `pyproject.toml` would be new functionality and was out of scope.
5. **No `.gitattributes`.** On a mixed Windows/Unix team, line-ending
   normalisation (`* text=auto`) would be worth adding. Out of scope here.
6. **No dependency pin.** `pandas`, `pyarrow`, `numpy`, `matplotlib` are
   named in the README but unversioned. A `requirements.txt` would improve
   reproducibility; it is a new file and was not created.

---

## 7. Remaining issues

| # | Issue | Severity | Action |
|---|---|---|---|
| 1 | **1.1 GiB orphaned dataset blobs in `.git/objects`** | **High (local only)** | Run `git prune --expire=now && git gc --prune=now`. **Yours to run.** |
| 2 | Empty directories lost on clone | Low | Add `.gitkeep` files if wanted |
| 3 | No `requirements.txt` / `pyproject.toml` | Low | Out of scope |
| 4 | No `.gitattributes` | Low | Out of scope |
| 5 | Blanket `*.csv` ignore | Informational | Negate per-file if a config CSV is ever needed |

**Nothing blocks the first commit except item 1, and item 1 does not affect
what reaches GitHub — only local disk.**

---

## 8. Suggested first commit

```bash
# 1. reclaim the orphaned blobs
git prune --expire=now && git gc --prune=now

# 2. confirm what will be staged (expect 58 files, no data/)
git add -A --dry-run | grep -c '^add'
git add -A --dry-run | grep 'data/' || echo "no dataset files - good"

# 3. stage and commit
git add -A
git status --short
git commit -m "GLASSCHIP-V1: locked pipeline, documentation and reports"
```

Do not run `git add data/` under any circumstances.

---

## 9. Scope compliance

| Constraint | Held |
|---|---|
| No new modules | yes |
| No scientific implementation modified | yes — 7/7 locked modules byte-identical |
| No models, no PINNs | yes |
| No optimisation or refactoring | yes |
| No commit, remote, or push created | yes |
| Files created | 2 (`.gitignore` rewritten, this report) + README edit |
