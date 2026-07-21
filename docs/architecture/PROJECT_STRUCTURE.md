# GLASSCHIP-V1 — Project Structure

Reorganisation plan. Written **before** any file was moved.

Scope: file placement and import paths only. No implementation logic is
changed, no functionality is added or removed.

---

## 1. Existing structure

Everything sat in the repository root: 36 files, no separation between
source, documentation, reports, generated images, and dead material from a
superseded project.

```
GLASSCHIP/
    01_Project_Overview.md .. 08_Final_Conclusion.md   8 files, dead battery project
    HANDOVER.md
    LOADER_README.md  VALIDATOR_README.md
    PREPROCESSING_README.md  VISUALIZATION_README.md
    README.md                                          0 bytes, empty
    dataset_report.md  dataset_schema.md
    eda_report.md  schema_report.md
    glasschip_v1_compatibility.md
    loader.py  validator.py                            locked pipeline
    metric_selector.py  preprocessor.py
    timeseries_builder.py  exporter.py                 locked pipeline
    visualizer.py                                      locked pipeline
    example_usage.py  validator_example_usage.py
    preprocessing_example_usage.py
    visualization_example_usage.py
    explore_dataset.py  generate_reports.py
    verify_stats.py                                    exploration scripts
    power_distribution.png  temp_distribution.png      images in root
    __pycache__/                                       11 files of clutter
    data/processed/                                    3 files
    datasets/21-03/                                    339 files, raw data
    eda_plots/                                         9 PNGs
    visualizations/                                    7 PNGs
    exadata/  notebooks/  reports/  results/           4 empty directories
```

Problems:

1. 36 files in root, no grouping by kind or lifecycle.
2. Source, docs, reports, and generated images indistinguishable.
3. Dead battery-project material (`01_*` to `08_*`) mixed with live work.
4. Two PNGs loose in root.
5. Raw data (`datasets/`) not under `data/`.
6. Four empty directories, two of which (`exadata/`, `results/`) are unused.
7. `__pycache__/` committed as clutter.
8. Empty `README.md` — no entry point.

---

## 2. Proposed structure

```
GLASSCHIP/
    README.md                       root index

    data/
        raw/                        datasets/21-03 (untouched Zenodo record)
        processed/                  intermediate artefacts
        exports/                    Node_*.parquet / .csv / _report.json

    src/
        loader/                     loader.py            LOCKED
        validator/                  validator.py         LOCKED
        preprocessing/              metric_selector.py   LOCKED
                                    preprocessor.py      LOCKED
                                    timeseries_builder.py LOCKED
                                    exporter.py          LOCKED
        visualization/              visualizer.py        LOCKED

    reports/
        dataset/                    dataset_report, dataset_schema,
                                    eda_report, schema_report
        validation/                 glasschip_v1_compatibility
        preprocessing/              (empty, reserved)
        visualization/              (empty, reserved)

    docs/
        architecture/               PROJECT_STRUCTURE,
                                    REPOSITORY_REORGANIZATION_REPORT
        handovers/                  HANDOVER.md
        module_documentation/       LOADER/VALIDATOR/PREPROCESSING/
                                    VISUALIZATION READMEs
        specifications/             (empty, reserved)

    assets/
        images/                     power_distribution, temp_distribution
        plots/
            eda/                    9 EDA PNGs
            visualization/          7 node-15 PNGs

    examples/                       4 example_usage scripts
    configs/                        (empty, reserved)
    tests/                          (empty, reserved)
    notebooks/                      (empty, reserved)

    archive/
        battery_project_v0/         01_* .. 08_* (superseded, retained)
        exploration/                explore_dataset, generate_reports,
                                    verify_stats
```

---

## 3. Files being moved

### 3.1 Source — `src/` (7 files, all LOCKED)

| From | To | Reason |
|---|---|---|
| `loader.py` | `src/loader/loader.py` | Layer 1 of the pipeline; its own package |
| `validator.py` | `src/validator/validator.py` | Layer 2; own package |
| `metric_selector.py` | `src/preprocessing/metric_selector.py` | Preprocessing layer |
| `preprocessor.py` | `src/preprocessing/preprocessor.py` | Preprocessing layer |
| `timeseries_builder.py` | `src/preprocessing/timeseries_builder.py` | Preprocessing layer |
| `exporter.py` | `src/preprocessing/exporter.py` | Preprocessing layer |
| `visualizer.py` | `src/visualization/visualizer.py` | Visualisation layer |

Grouped by pipeline stage, matching the dependency order
`loader → validator → preprocessing → visualization`.

### 3.2 Examples — `examples/` (4 files)

| From | To |
|---|---|
| `example_usage.py` | `examples/loader_example_usage.py` |
| `validator_example_usage.py` | `examples/validator_example_usage.py` |
| `preprocessing_example_usage.py` | `examples/preprocessing_example_usage.py` |
| `visualization_example_usage.py` | `examples/visualization_example_usage.py` |

`example_usage.py` is renamed to `loader_example_usage.py`. It is the
loader example, and the bare name is ambiguous once the four sit together.
This is the **only** rename in the reorganisation.

### 3.3 Reports — `reports/` (5 files)

| From | To | Reason |
|---|---|---|
| `dataset_report.md` | `reports/dataset/` | Dataset finding |
| `dataset_schema.md` | `reports/dataset/` | Dataset finding |
| `eda_report.md` | `reports/dataset/` | Dataset finding |
| `schema_report.md` | `reports/dataset/` | Dataset finding |
| `glasschip_v1_compatibility.md` | `reports/validation/` | Compatibility result |

Names unchanged — these are scientific records.

### 3.4 Documentation — `docs/` (5 files)

| From | To | Reason |
|---|---|---|
| `LOADER_README.md` | `docs/module_documentation/` | Module doc |
| `VALIDATOR_README.md` | `docs/module_documentation/` | Module doc |
| `PREPROCESSING_README.md` | `docs/module_documentation/` | Module doc |
| `VISUALIZATION_README.md` | `docs/module_documentation/` | Module doc |
| `HANDOVER.md` | `docs/handovers/` | Session handover |

### 3.5 Assets — `assets/` (18 files)

| From | To | Reason |
|---|---|---|
| `power_distribution.png` | `assets/images/` | No image may remain in root |
| `temp_distribution.png` | `assets/images/` | No image may remain in root |
| `eda_plots/*.png` (9) | `assets/plots/eda/` | Generated EDA plots |
| `visualizations/*.png` (7) | `assets/plots/visualization/` | Generated node-15 plots |

### 3.6 Data — `data/` (342 files)

| From | To | Reason |
|---|---|---|
| `datasets/21-03/` | `data/raw/21-03/` | Raw Zenodo record belongs under `data/raw` |
| `datasets/21-03.tar` | `data/raw/` | Source archive |
| `data/processed/Node_15.*` | `data/exports/` | These are exporter output |

### 3.7 Archive — `archive/` (11 files)

| From | To | Reason |
|---|---|---|
| `01_Project_Overview.md` … `08_Final_Conclusion.md` | `archive/battery_project_v0/` | Superseded battery-SOH project. Retained, not deleted. Must not be read as a specification. |
| `explore_dataset.py` | `archive/exploration/` | Exploration script, superseded by the locked pipeline |
| `generate_reports.py` | `archive/exploration/` | Generated the dataset reports |
| `verify_stats.py` | `archive/exploration/` | One-off verification |

The three exploration scripts remain runnable. They are archived because
they are not part of the locked pipeline, not because they are broken.

### 3.8 Removed clutter (no data loss)

| Item | Action | Reason |
|---|---|---|
| `__pycache__/` | Delete | Regenerable bytecode |
| `exadata/` | Delete | Empty, unused |
| `results/` | Delete | Empty, superseded by `reports/` |

No file containing information is deleted anywhere in this reorganisation.

---

## 4. Import changes required

This is the only part of the task that touches source files. Moving Python
modules into packages breaks flat imports. **16 cross-module import
statements** exist today.

### 4.1 Mechanism

Each `src/` subdirectory becomes a package with an `__init__.py` that
re-exports its public names. With `src/` on `sys.path`:

- `from loader import DatasetLoader` — **unchanged**, resolves to the
  `loader` package
- `from validator import DatasetValidator` — **unchanged**

Only imports that cross into or within the multi-module `preprocessing`
package need adjusting.

### 4.2 Statements changed (4 of 16)

| File | Before | After |
|---|---|---|
| `src/preprocessing/preprocessor.py` | `from metric_selector import ...` | `from .metric_selector import ...` |
| `src/preprocessing/timeseries_builder.py` | `from metric_selector import ...` | `from .metric_selector import ...` |
| `src/preprocessing/timeseries_builder.py` | `from preprocessor import ...` | `from .preprocessor import ...` |
| `src/visualization/visualizer.py` | `from timeseries_builder import ...` | `from preprocessing.timeseries_builder import ...` |

Intra-package imports use relative form (`.module`) to avoid a circular
initialisation between `preprocessing/__init__.py` and its submodules.

The remaining **12 import statements are unchanged**, including all 4 in
`validator.py` and every `from loader import ...`.

**Only the module path changes. No imported name, signature, constant, or
behaviour is altered.**

### 4.3 Examples

Each example gains a four-line `sys.path` bootstrap so it runs from the
repository root without installation:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
```

`preprocessing_example_usage.py` also has its output directory changed from
`data/processed` to `data/exports`, matching where exported node datasets
now live.

---

## 5. What is explicitly NOT changed

- No function, class, method, constant, or threshold is modified.
- No algorithm, filter, join, or plot behaviour is modified.
- No scientific report is renamed or edited.
- No file containing information is deleted.
- No new module, feature, test, or capability is added.

---

## 6. Verification plan

After moving:

1. Import every module from the new layout.
2. Run all four examples end to end.
3. Compare pipeline output against the pre-move baseline
   (node 15: 11,166 rows, 5 columns, 2 segments of 61.978 h and 0.044 h).
4. Byte-compile every moved source file.
5. Confirm no image remains in root.
6. Confirm module file contents are unchanged apart from the 4 import lines.

Results are recorded in
`docs/architecture/REPOSITORY_REORGANIZATION_REPORT.md`.
