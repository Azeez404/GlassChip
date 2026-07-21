"""Minimal usage examples for :mod:`loader`.

Run from the project root::

    python examples/loader_example_usage.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from loader import DatasetLoader

DATASET_PATH = "data/raw/21-03"


def main() -> None:
    loader = DatasetLoader(DATASET_PATH)
    print(loader)

    # --- metadata -----------------------------------------------------
    summary = loader.dataset_summary()
    print(f"\nfiles={summary['total_files']} "
          f"metrics={summary['total_metrics']} "
          f"size={summary['total_size_mb']} MB")
    print(f"timestamps: {summary['timestamp_range']['min']} -> "
          f"{summary['timestamp_range']['max']}")

    # --- available metrics --------------------------------------------
    print(f"\nplugins: {loader.get_available_plugins()}")
    print(f"total metrics: {len(loader.get_available_metrics())}")
    print(f"ipmi_pub (first 5): {loader.get_available_metrics('ipmi_pub')[:5]}")

    # --- available nodes ----------------------------------------------
    # Node ID namespaces are plugin-specific; ask per plugin.
    nodes = loader.get_available_nodes(plugin="ipmi_pub")
    print(f"\nipmi_pub nodes: {nodes['total_nodes']} "
          f"({nodes['min_id']}..{nodes['max_id']}), "
          f"contiguous={nodes['is_contiguous']}")

    # --- load one metric for one node ---------------------------------
    power = loader.load_metric_for_node("p0_power", "15")
    print(f"\np0_power @ node 15: {power.shape}")
    print(power.head(3).to_string(index=False))

    # --- load one metric for several nodes ----------------------------
    subset = loader.load_metric("p0_power", nodes=["0", "1", "2"])
    print(f"\np0_power @ nodes 0,1,2: {subset.shape}")

    # --- load several metrics for one node (long format) --------------
    node_frame = loader.load_node(
        "15", metrics=["p0_power", "p1_power", "ambient", "fan0_0"]
    )
    print(f"\nnode 15 (4 metrics): {node_frame.shape}")
    print(node_frame.groupby("metric").size().to_string())

    # --- facility-scoped metric (no node column) ----------------------
    coolant = loader.load_metric("Potenza")
    print(f"\nPotenza (logics_pub): {coolant.shape} "
          f"columns={list(coolant.columns)}")


if __name__ == "__main__":
    main()
