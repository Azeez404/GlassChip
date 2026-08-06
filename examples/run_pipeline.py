"""Run the GLASSCHIP-V1 data pipeline: load -> validate -> preprocess -> visualise.

Demonstrates the first four (locked) layers on the M100 ExaData record.

Run from the repository root::

    python examples/run_pipeline.py

Requires the dataset at ``data/raw/21-03`` (see README).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from preprocessing import Exporter, TimeSeriesBuilder  # noqa: E402
from validator import DatasetValidator  # noqa: E402
from visualization import ThermalVisualizer  # noqa: E402

DATASET_PATH = "data/raw/21-03"
NODE = "15"


def main() -> None:
    # 1. VALIDATE — what can the locked mandatory inputs safely form?
    validator = DatasetValidator(DATASET_PATH)
    verdict = validator.validate_glasschip_inputs()
    print(f"[validate] mandatory-input verdict: {verdict['verdict']}")
    print(f"           (FAIL is expected: utilisation/frequency sample on a "
          f"different grid; the IPMI triple is used instead)")

    # 2. PREPROCESS — build the model-ready series for one node.
    builder = TimeSeriesBuilder(DATASET_PATH)
    frame, report = builder.construct_node_dataframe(NODE)
    print(f"\n[preprocess] node {NODE}: {frame.shape[0]} rows x "
          f"{frame.shape[1]} cols")
    print(f"             segments: "
          f"{[(s['duration_h'], s['n_samples']) for s in report['segments']]}")

    # 3. EXPORT — write the model-ready dataset (git-ignored location).
    written = Exporter("data/exports", overwrite=True).export_node(
        frame, NODE, formats=("parquet", "csv"), report=report
    )
    print(f"\n[export] {', '.join(p.name for p in written.values())}")

    # 4. VISUALISE — describe the data (never explain it).
    viz = ThermalVisualizer(builder, output_dir="data/exports/figures")
    figures = viz.plot_all(NODE)
    print(f"\n[visualise] {len(figures)} figures -> data/exports/figures/")


if __name__ == "__main__":
    main()
