"""Minimal usage example for the GLASSCHIP-V1 thermal visualiser.

Run from the project root::

    python examples/visualization_example_usage.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import matplotlib.pyplot as plt

from visualization import DEFAULT_NODE, ThermalVisualizer

DATASET_PATH = "data/raw/21-03"


def main() -> None:
    viz = ThermalVisualizer(DATASET_PATH, output_dir="assets/plots/visualization")
    print(f"default node: {DEFAULT_NODE}")

    # --- individual metrics, split at segment boundaries --------------
    for name, method in (
        ("temperature", viz.plot_temperature),
        ("power", viz.plot_power),
        ("fan speed", viz.plot_fan_speed),
    ):
        fig, path = method()
        print(f"  {name:12s} -> {path.name}")
        plt.close(fig)

    # --- relationships -------------------------------------------------
    fig, path = viz.plot_temperature_vs_power()
    print(f"  power vs temp -> {path.name}")
    plt.close(fig)

    fig, path = viz.plot_temperature_vs_fan()
    print(f"  temp vs fan   -> {path.name}")
    plt.close(fig)

    # --- everything on one timeline ------------------------------------
    fig, path = viz.plot_thermal_behaviour()
    print(f"  combined      -> {path.name}")
    plt.close(fig)

    # --- where the data is, and is not ---------------------------------
    fig, path = viz.plot_segment_boundaries()
    print(f"  segments      -> {path.name}")
    plt.close(fig)

    # --- observations ---------------------------------------------------
    report = viz.generate_visualization_report()
    print(f"\nnode {report['node']}, {report['n_rows']} rows")

    print("\nsegments:")
    for segment in report["segments"]:
        print(f"  {segment['index']}: {segment['duration_h']:.3f} h, "
              f"{segment['n_samples']} samples")

    print("\nstatistics:")
    for role, stats in report["statistics"].items():
        print(f"  {role:12s} range={stats['range']:7.1f} "
              f"std={stats['std']:7.2f} unique={stats['n_unique']:3d}")

    print("\nobservations:")
    for observation in report["observations"]:
        print(f"  - {observation}")


if __name__ == "__main__":
    main()
