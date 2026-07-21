# GLASSCHIP-V1

Physics-constrained thermal modelling of fleet-scale processor telemetry.

Dataset: **M100 ExaData** (CINECA Marconi100), record `21-03`, CC-BY-4.0.

---

## Status

| Module | State |
|---|---|
| Dataset exploration, schema, EDA | complete |
| `loader` | **LOCKED** |
| `validator` | **LOCKED** |
| `preprocessing` | **LOCKED** |
| `visualization` | **LOCKED** |
| Modelling | not started |

---

## Layout

```
data/       raw/ (Zenodo record) - processed/ - exports/
src/        loader/ - validator/ - preprocessing/ - visualization/
reports/    dataset/ - validation/ - preprocessing/ - visualization/
docs/       architecture/ - handovers/ - module_documentation/ - specifications/
assets/     images/ - plots/eda/ - plots/visualization/
examples/   one runnable example per layer
configs/    tests/    notebooks/    archive/
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

pip install pandas pyarrow numpy matplotlib
```

Python 3.10 or newer. No packaging metadata is required; `src/` is placed on
the path by the examples.

---

## Running

From the repository root, after the dataset is in place:

```bash
python examples/loader_example_usage.py
python examples/validator_example_usage.py
python examples/preprocessing_example_usage.py
python examples/visualization_example_usage.py
```

The examples insert `src/` on `sys.path` themselves. For ad-hoc imports set
`PYTHONPATH=src`:

```python
from loader import DatasetLoader
from validator import DatasetValidator
from preprocessing import MetricSelector, TimeSeriesBuilder, Exporter
from visualization import ThermalVisualizer
```

### Generated output

Running the examples writes to git-ignored locations:

| Path | Content |
|---|---|
| `data/exports/` | `Node_15.parquet`, `Node_15.csv`, `Node_15_report.json` |
| `assets/plots/visualization/` | 7 node-15 figures (overwrites the committed copies) |

### Reproducibility check

The preprocessing pipeline is deterministic. For node 15 of record `21-03`:

| | |
|---|---|
| Frame shape | `(11166, 5)` |
| SHA-256 of frame (first 16) | `8473342129fb19f0` |
| Segments | `61.978 h / 11157 samples`, `0.044 h / 9 samples` |
| 5-input validator verdict | `FAIL` (expected — see Known constraints) |

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
```

Each layer refuses to proceed when the previous one reports a problem.
`preprocessing` raises `IncompatibleSelectionError` whenever `validator`
returns `FAIL`; there is no override.

---

## Documentation

| Topic | Path |
|---|---|
| Session handover - **read first** | `docs/handovers/HANDOVER.md` |
| Repository structure | `docs/architecture/PROJECT_STRUCTURE.md` |
| Reorganisation record | `docs/architecture/REPOSITORY_REORGANIZATION_REPORT.md` |
| Module documentation | `docs/module_documentation/` |
| Dataset reports | `reports/dataset/` |
| Validation reports | `reports/validation/` |

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

---

## `archive/`

`archive/battery_project_v0/` holds a superseded battery-SOH project.
**It is not a specification for this work.** `archive/exploration/` holds
the exploration scripts that produced the dataset reports; they remain
runnable but are not part of the locked pipeline.
