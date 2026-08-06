# GLASSCHIP-V1

Physics-constrained thermal modelling of fleet-scale processor telemetry.

Dataset: **M100 ExaData** (CINECA Marconi100), record `21-03`, CC-BY-4.0.

---

## Status — FROZEN (all phases complete)

| Layer | State |
|---|---|
| Dataset exploration, schema, EDA | complete |
| `loader` | **LOCKED** |
| `validator` | **LOCKED** |
| `preprocessing` | **LOCKED** |
| `visualization` | **LOCKED** |
| `screening` (physics-based node screening) | **LOCKED** |
| `baseline` (classical first-order thermal model) | **LOCKED** |
| `pinn` (the single physics-informed neural network) | **LOCKED** |
| Adversarial audit | complete |

**Headline result:** the PINN provides **no scientifically meaningful
improvement** over the classical first-order baseline. The residual the
baseline leaves is real but **orthogonal to the available inputs** (explained
variance R² ≤ 0.04 from power, power-change, fan, and temperature), so it is
not learnable within scope. See `docs/RESEARCH_SUMMARY.md`.

---

## Layout

```
data/       raw/ (Zenodo record, gitignored) - exports/ (generated, gitignored)
src/        loader/ - validator/ - preprocessing/ - visualization/
            screening/ - baseline/ - pinn/     (7 locked layers)
docs/       RESEARCH_SUMMARY.md - handovers/HANDOVER.md
reports/    validation/
examples/   run_pipeline.py - run_baseline.py - run_pinn.py
README.md - requirements.txt - .gitignore
```

---

## Dataset

**The dataset is not included in this repository and never will be.** It is
public, permanently archived, and must be downloaded separately.

| | |
|---|---|
| Source | M100 ExaData, CINECA Marconi100 |
| Paper | Borghesi et al., *Nature Scientific Data* (2023), DOI `10.1038/s41597-023-02174-3` |
| Archive | Zenodo, DOI series `10.5281/zenodo.7588815` … `7590583` |
| Licence | CC-BY-4.0 |
| Record used | `21-03` (March 2021), inside the `21-01` – `21-06` record (`10.5281/zenodo.7589131`) |
| Size on disk | ~575 MB extracted, 338 Parquet files |

### Download

1. Open the Zenodo record and download the archive containing `21-03`.
2. Extract it so the tree looks exactly like this:

```
data/raw/21-03/
    year_month=21-03/
        plugin=ipmi_pub/
            metric=p0_power/
                a_0.parquet
        plugin=ganglia_pub/
        plugin=logics_pub/
        plugin=nagios_pub/
        plugin=schneider_pub/
```

3. Confirm the loader sees it:

```bash
PYTHONPATH=src python -c "from loader import DatasetLoader; print(DatasetLoader('data/raw/21-03'))"
```

Expected: `DatasetLoader(root='...21-03/year_month=21-03', metrics=338, plugins=5)`

`data/` is git-ignored in full. Nothing you place there will be committed.

---

## Setup

```bash
git clone <repository-url>
cd GLASSCHIP

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

Python 3.10 or newer (verified on 3.13). No packaging metadata is required;
`src/` is placed on the path by the examples. `torch` (CPU build) is needed
only for the PINN layer.

---

## Running

From the repository root, after the dataset is in place:

```bash
python examples/run_pipeline.py     # load -> validate -> preprocess -> visualise
python examples/run_baseline.py     # screening + classical first-order fit
python examples/run_pinn.py         # PINN vs baseline on one node
```

The examples insert `src/` on `sys.path` themselves. For ad-hoc imports set
`PYTHONPATH=src`:

```python
from loader import DatasetLoader
from validator import DatasetValidator
from preprocessing import TimeSeriesBuilder, Exporter
from visualization import ThermalVisualizer
from screening import NodeScreener
from baseline import ClassicalBaselineModel
from pinn import ThermalPINN
```

Examples write to the git-ignored `data/exports/`. The pipeline is
deterministic: node 15's model-ready frame has SHA-256 (first 16)
`8473342129fb19f0` — the reproducibility anchor.

---

## Pipeline

```
data/raw/21-03
      |
   loader          raw parquet -> dataframes
      |
   validator       what can safely coexist?  PASS / FAIL
      |
  preprocessing    gate -> clean -> exact join -> export
      |
  visualization    what does the data look like?
      |
  screening        which nodes deserve to teach a model?  PASS / FAIL (372/22)
      |
  baseline         how much does simple first-order physics explain?
      |
  pinn             can a PINN explain what the baseline cannot?  (answer: no)
```

Each layer refuses to proceed when the previous one reports a problem.
`preprocessing` raises `IncompatibleSelectionError` whenever `validator`
returns `FAIL`; there is no override.

---

## Documentation

| Topic | Path |
|---|---|
| **Complete scientific summary** | `docs/RESEARCH_SUMMARY.md` |
| **Project state + how to continue** | `docs/handovers/HANDOVER.md` |
| Validation report | `reports/validation/glasschip_v1_compatibility.md` |
| API reference | in-code docstrings in `src/` |

---

## Scope

**In scope (prototype):** temperature (`p0_core0_temp`), power
(`p0_power`), fan speed (`fan0_0`) - the IPMI-only triple that validates.

**Out of scope:** CPU utilisation, frequency, GPU metrics, and the
remaining ~330 metrics.

---

## Known constraints

1. Record `21-03` contains **61.978 h** of contiguous data plus a 9-sample
   fragment, separated by a 648.9 h gap - not a month.
2. **394 nodes** carry all three metrics, not 980.
3. Node ID namespaces are **plugin-specific** and do not match across
   plugins.
4. The data is **observational and closed-loop**; no causal claim is
   supported.
5. No instrument characterisation is possible from this record.

Full detail in `docs/handovers/HANDOVER.md`.
