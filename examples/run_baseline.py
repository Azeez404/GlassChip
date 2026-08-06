"""Fit the classical first-order thermal baseline on screened PASS nodes.

Pipeline: screening -> classical baseline. Answers Phase 9's question:
how much of the observed thermal behaviour does simple first-order physics
explain?

Run from the repository root::

    python examples/run_baseline.py [n_nodes]

``n_nodes`` (optional) limits how many PASS nodes to fit (default: 10, for a
quick demo; omit the cap in a full run). Requires the dataset at
``data/raw/21-03``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from baseline import ClassicalBaselineModel  # noqa: E402
from preprocessing import TimeSeriesBuilder  # noqa: E402
from screening import NodeScreener  # noqa: E402

DATASET_PATH = "data/raw/21-03"
GAP_MULTIPLIER = 3.0


def segments(frame):
    dt = frame["timestamp"].diff().dt.total_seconds().to_numpy()
    median = np.nanmedian(dt)
    breaks = list(np.where(dt > median * GAP_MULTIPLIER)[0])
    bounds = [0] + breaks + [len(frame)]
    out = []
    for i in range(len(bounds) - 1):
        lo, hi = bounds[i], bounds[i + 1]
        if hi - lo >= 2:
            out.append((frame["temperature"].to_numpy()[lo:hi],
                        frame["power"].to_numpy()[lo:hi]))
    return out


def main() -> None:
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10

    builder = TimeSeriesBuilder(DATASET_PATH)
    pass_nodes = NodeScreener(builder).screen_all()["training_nodes"][:limit]
    print(f"fitting classical baseline on {len(pass_nodes)} PASS nodes\n")

    taus, rmses, inc_r2s = [], [], []
    for node in pass_nodes:
        segs = segments(builder.build_timeseries(node))
        if not segs:
            continue
        model = ClassicalBaselineModel()
        fit = model.fit(segs)
        metrics = model.evaluate(segs)
        if fit.is_stable:
            taus.append(fit.tau_eff_s)
        rmses.append(metrics.rmse)
        inc_r2s.append(metrics.increment_r2)

    print(f"median tau_eff    : {np.nanmedian(taus):.0f} s")
    print(f"median one-step RMSE: {np.median(rmses):.3f} degC")
    print(f"median increment R2 : {np.median(inc_r2s):.3f}  "
          f"(physics explains little of the step-to-step dynamics)")


if __name__ == "__main__":
    main()
