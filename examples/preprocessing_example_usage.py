"""Minimal usage example for the GLASSCHIP-V1 preprocessing pipeline.

Run from the project root::

    python examples/preprocessing_example_usage.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from preprocessing import (
    PHYSICAL_BOUNDS,
    Exporter,
    IncompatibleSelectionError,
    MetricSelector,
    TimeSeriesBuilder,
)

DATASET_PATH = "data/raw/21-03"
OUTPUT_DIR = "data/exports"


def main() -> None:
    # --- 1. selection is gated by validator.py ------------------------
    selector = MetricSelector(DATASET_PATH)
    selection = selector.select_metrics()
    print(f"selection verdict: {selection['verdict']}")
    print(f"  metrics: {selection['metrics']}")
    print(f"  common nodes: {selection['n_common_nodes']}")

    # A selection the validator rejects must not proceed.
    try:
        selector.select_metrics({
            "temperature": "cpu_user",   # 90 s, ganglia
            "power": "p0_power",         # 20 s, ipmi
        })
        print("  ERROR: gate failed to refuse")
    except IncompatibleSelectionError:
        print("  gate correctly refused an incompatible selection")

    # --- 2. node selection --------------------------------------------
    nodes = selector.select_common_nodes()
    node = selector.select_node("15")
    print(f"\n{len(nodes)} nodes carry all three metrics; using node {node}")

    # --- 3. build the time series -------------------------------------
    print(f"\nphysical bounds: {PHYSICAL_BOUNDS}")
    builder = TimeSeriesBuilder(DATASET_PATH)
    frame, report = builder.construct_node_dataframe(node)

    print(f"\nmodel-ready frame: {frame.shape}")
    print(frame.head(4).to_string(index=False))

    print(f"\nrows per role after cleaning: "
          f"{report['n_rows_per_role_after_cleaning']}")
    print(f"joined rows: {report['n_rows_joined']} "
          f"(retention {report['join_retention_ratio']:.4f})")
    for segment in report["segments"]:
        print(f"  segment {segment['duration_h']:.3f} h, "
              f"{segment['n_samples']} samples")

    # --- 4. export -----------------------------------------------------
    exporter = Exporter(OUTPUT_DIR, overwrite=True)
    written = exporter.export_node(
        frame, node, formats=("parquet", "csv"), report=report
    )
    print("\nwritten:")
    for fmt, path in written.items():
        print(f"  {fmt:8s} {path.name} ({path.stat().st_size / 1024:.1f} KB)")

    # --- 5. several nodes ----------------------------------------------
    many = builder.build_many(nodes[:3])
    print(f"\nbuilt {len(many)} nodes: "
          f"{ {k: v.shape for k, v in many.items()} }")


if __name__ == "__main__":
    main()
