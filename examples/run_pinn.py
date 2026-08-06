"""Fit the GLASSCHIP-V1 PINN on one PASS node and compare it to the baseline.

Answers Phase 10's question: can the PINN explain what the classical
first-order baseline cannot? The comparison is FAIR — the PINN's learned
continuous-time physics parameters are discretised into the SAME one-step
predictor the baseline uses, so both are scored as first-order predictors on
identical data.

Run from the repository root::

    python examples/run_pinn.py [node]

``node`` (optional) is a PASS node ID (default: 99, strong excitation).
Requires the dataset at ``data/raw/21-03`` and ``torch``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from baseline import ClassicalBaselineModel  # noqa: E402
from pinn import PINNConfig, ThermalPINN  # noqa: E402
from preprocessing import TimeSeriesBuilder  # noqa: E402

DATASET_PATH = "data/raw/21-03"
DT_S = 20.0
GAP_MULTIPLIER = 3.0


def longest_segment(frame):
    dt = frame["timestamp"].diff().dt.total_seconds().to_numpy()
    median = np.nanmedian(dt)
    breaks = list(np.where(dt > median * GAP_MULTIPLIER)[0])
    bounds = [0] + breaks + [len(frame)]
    spans = [(bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)]
    lo, hi = max(spans, key=lambda x: x[1] - x[0])
    return frame["temperature"].to_numpy()[lo:hi], frame["power"].to_numpy()[lo:hi]


def onestep(alpha, beta, gamma, temp, power):
    pred = alpha * temp[:-1] + beta * power[:-1] + gamma
    actual = temp[1:]
    rmse = float(np.sqrt(np.mean((actual - pred) ** 2)))
    ia, ip = actual - temp[:-1], pred - temp[:-1]
    inc_r2 = float(1 - np.sum((ia - ip) ** 2) / np.sum((ia - ia.mean()) ** 2))
    return rmse, inc_r2


def main() -> None:
    node = sys.argv[1] if len(sys.argv) > 1 else "99"

    temp, power = longest_segment(
        TimeSeriesBuilder(DATASET_PATH).build_timeseries(node)
    )
    t = np.arange(len(temp)) * DT_S
    print(f"node {node}: {len(temp)} samples, T std {temp.std():.2f} degC\n")

    # classical baseline
    bf = ClassicalBaselineModel(dt_s=DT_S).fit([(temp, power)])
    b_rmse, b_inc = onestep(bf.alpha, bf.beta, bf.gamma, temp, power)
    print(f"baseline: tau={bf.tau_eff_s:.0f}s | RMSE={b_rmse:.3f} incR2={b_inc:.3f}")

    # PINN -> discretise its physics into the same one-step predictor
    pf = ThermalPINN(PINNConfig(epochs=3000)).fit(t, temp, power)
    alpha = np.exp(-pf.b * DT_S)
    beta = (pf.a / pf.b) * (1 - alpha)
    gamma = (pf.c / pf.b) * (1 - alpha)
    p_rmse, p_inc = onestep(alpha, beta, gamma, temp, power)
    print(f"PINN    : tau={pf.tau_eff_s:.0f}s | RMSE={p_rmse:.3f} incR2={p_inc:.3f}")

    print(f"\nPINN beats baseline on RMSE?  {p_rmse < b_rmse}  "
          f"(Phase 10 result across 12 nodes: 0/12)")


if __name__ == "__main__":
    main()
