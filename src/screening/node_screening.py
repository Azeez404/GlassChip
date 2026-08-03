"""Physics-based node screening for GLASSCHIP-V1.

ONE responsibility: decide which nodes deserve to teach the future PINN.

Output per node is exactly PASS or FAIL, with the scientific reason. This
module estimates nothing, models nothing, learns nothing. It reads the
model-ready per-node series (via the locked pipeline) and applies four
physics-motivated gates.

A node PASSes only if it can *identify* a first-order thermal system:

    C dT/dt = P - (T - T_ref)/R

That requires, at minimum:

1. Temperature that moves clearly above the 1 degC quantization floor
   (otherwise "dynamics" are quantization noise).
2. Power that actually varies (no forcing -> nothing to identify).
3. Temperature that responds coherently to power (the node-95 guard:
   power varies, temperature does not -> physically meaningless for a
   thermal fit).
4. A usable contiguous segment long enough for stable statistics.

Thresholds are module-level constants, each justified below and each
traceable, so any verdict can be audited.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from preprocessing import TimeSeriesBuilder, TimeSeriesError
from metric_selector import MetricSelector  # type: ignore  # noqa: F401

__all__ = [
    "NodeScreener",
    "ScreeningVerdict",
    "MIN_TEMP_STD_C",
    "MIN_TEMP_UNIQUE",
    "MIN_POWER_STD_W",
    "MIN_ABS_CORR",
    "MIN_SEGMENT_SAMPLES",
    "TEMPERATURE_QUANTIZATION_C",
]

# --------------------------------------------------------------------------
# Screening thresholds. Each is justified; none is arbitrary.
# --------------------------------------------------------------------------

#: Temperature sensor quantization step, measured in the dataset (1 degC).
TEMPERATURE_QUANTIZATION_C: float = 1.0

#: A node's temperature std must exceed TWICE the quantization step. Below
#: this the signal is dominated by 1 degC rounding and no dynamic
#: information survives. Idle nodes measured at 0.5-0.9; active nodes at
#: 2.2+. The gap makes 2.0 a natural, defensible cut.
MIN_TEMP_STD_C: float = 2.0 * TEMPERATURE_QUANTIZATION_C

#: The temperature trajectory must exercise enough distinct levels to have
#: shape, not just toggle between two or three values.
MIN_TEMP_UNIQUE: int = 8

#: Power (the forcing term) must vary meaningfully. Idle nodes measured at
#: ~1.5 W std; active nodes at 10-56 W. 5 W sits in the empty gap between
#: them and marks "genuinely driven".
MIN_POWER_STD_W: float = 5.0

#: Absolute Pearson correlation between power and temperature. This is the
#: coherence gate: even with excitation, temperature must track power. The
#: data separates cleanly - incoherent nodes at 0.01-0.30, coherent nodes
#: at 0.54+. 0.5 is the natural boundary and the node-95 guard.
MIN_ABS_CORR: float = 0.5

#: Minimum contiguous-segment length for stable statistics (~5.5 h at 20 s).
MIN_SEGMENT_SAMPLES: int = 1000


@dataclass
class ScreeningVerdict:
    """The PASS/FAIL result for one node, with its evidence."""

    node: str
    verdict: str  # "PASS" or "FAIL"
    reasons: list[str] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        head = f"Node-{self.node}  {self.verdict}"
        body = "\n".join(f"    - {r}" for r in self.reasons)
        return f"{head}\n{body}"


class NodeScreener:
    """Apply the physics-based screen to nodes of one dataset record.

    Parameters
    ----------
    source:
        A :class:`~preprocessing.TimeSeriesBuilder` or a dataset path.

    Notes
    -----
    Statistics are computed on the **longest contiguous segment** of each
    node, never across the 648.9 h gap.
    """

    def __init__(self, source: TimeSeriesBuilder | str) -> None:
        self.builder = (
            source
            if isinstance(source, TimeSeriesBuilder)
            else TimeSeriesBuilder(source)
        )

    # ------------------------------------------------------------------
    # Segment handling (boundaries only; nothing inserted)
    # ------------------------------------------------------------------

    @staticmethod
    def _longest_segment(frame: pd.DataFrame) -> pd.DataFrame:
        """Return the longest gap-free run of the series."""
        if len(frame) < 2:
            return frame
        dt = frame["timestamp"].diff().dt.total_seconds()
        median = float(dt.dropna().median())
        breaks = list(frame.index[dt > median * 3.0])
        bounds = [0] + breaks + [len(frame)]
        segments = [
            frame.iloc[bounds[i]:bounds[i + 1]]
            for i in range(len(bounds) - 1)
        ]
        return max(segments, key=len)

    # ------------------------------------------------------------------
    # Screening
    # ------------------------------------------------------------------

    def screen_node(self, node: str | int) -> ScreeningVerdict:
        """Return PASS or FAIL for one node, with scientific reasons."""
        node_id = str(node)

        try:
            frame = self.builder.build_timeseries(node_id)
        except TimeSeriesError as exc:
            return ScreeningVerdict(
                node_id, "FAIL",
                [f"could not build a usable series: {exc}"],
            )

        segment = self._longest_segment(frame)
        n = len(segment)

        temp = segment["temperature"]
        power = segment["power"]
        t_std = float(temp.std())
        t_unique = int(temp.nunique())
        p_std = float(power.std())
        # abs correlation; guard the degenerate zero-variance case
        if temp.std() == 0 or power.std() == 0:
            abs_corr = 0.0
        else:
            abs_corr = float(abs(power.corr(temp)))

        stats = {
            "segment_samples": n,
            "temp_std_c": round(t_std, 3),
            "temp_unique": t_unique,
            "power_std_w": round(p_std, 3),
            "abs_corr_power_temp": round(abs_corr, 4),
        }

        reasons: list[str] = []

        # Gate 0: enough data to judge.
        if n < MIN_SEGMENT_SAMPLES:
            reasons.append(
                f"longest contiguous segment has {n} samples, below the "
                f"{MIN_SEGMENT_SAMPLES} needed for stable statistics"
            )
            return ScreeningVerdict(node_id, "FAIL", reasons, stats)

        # Gate 1: thermal excitation above the quantization floor.
        temp_ok = t_std >= MIN_TEMP_STD_C and t_unique >= MIN_TEMP_UNIQUE
        # Gate 2: power excitation.
        power_ok = p_std >= MIN_POWER_STD_W
        # Gate 3: coherent thermal response.
        corr_ok = abs_corr >= MIN_ABS_CORR

        if not temp_ok:
            reasons.append(
                f"temperature is quantization-dominated "
                f"(std {t_std:.2f} degC, {t_unique} distinct values; need "
                f">= {MIN_TEMP_STD_C:.1f} degC and >= {MIN_TEMP_UNIQUE} "
                f"values above the {TEMPERATURE_QUANTIZATION_C:.0f} degC step)"
            )
        if not power_ok:
            reasons.append(
                f"insufficient power excitation "
                f"(std {p_std:.2f} W; need >= {MIN_POWER_STD_W:.1f} W)"
            )
        # The coherence gate is only meaningful when power is actually
        # exercised. Power varying with no thermal response is the
        # physically-meaningless (node-95) case and is called out plainly.
        if power_ok and not corr_ok:
            reasons.append(
                f"observable power variation ({p_std:.1f} W) with no coherent "
                f"thermal response (|corr| {abs_corr:.3f}; need "
                f">= {MIN_ABS_CORR:.2f}) - physically meaningless for a "
                f"thermal fit"
            )
        elif not power_ok and not corr_ok:
            reasons.append(
                f"weak power-temperature coupling (|corr| {abs_corr:.3f})"
            )

        if temp_ok and power_ok and corr_ok:
            return ScreeningVerdict(
                node_id, "PASS",
                [
                    f"meaningful thermal excitation (std {t_std:.2f} degC, "
                    f"{t_unique} levels)",
                    f"meaningful power excitation (std {p_std:.2f} W)",
                    f"coherent thermal response (|corr| {abs_corr:.3f})",
                ],
                stats,
            )
        return ScreeningVerdict(node_id, "FAIL", reasons, stats)

    def screen_all(
        self, nodes: list[str] | None = None
    ) -> dict[str, Any]:
        """Screen every common node; return verdicts and the training set.

        Parameters
        ----------
        nodes:
            Explicit node list. ``None`` screens every node carrying all
            three metrics.

        Returns
        -------
        dict
            ``total``, ``n_pass``, ``n_fail``, ``verdicts`` (list of
            :class:`ScreeningVerdict`), ``training_nodes`` (PASS only),
            and ``fail_reason_summary``.
        """
        if nodes is None:
            nodes = self.builder.selector.select_common_nodes()

        verdicts = [self.screen_node(n) for n in nodes]
        passed = [v for v in verdicts if v.verdict == "PASS"]
        failed = [v for v in verdicts if v.verdict == "FAIL"]

        reason_summary: dict[str, int] = {}
        for v in failed:
            for r in v.reasons:
                key = r.split("(")[0].strip()
                reason_summary[key] = reason_summary.get(key, 0) + 1

        return {
            "total": len(verdicts),
            "n_pass": len(passed),
            "n_fail": len(failed),
            "verdicts": verdicts,
            "training_nodes": sorted(
                (v.node for v in passed),
                key=lambda x: int(x) if x.isdigit() else x,
            ),
            "fail_reason_summary": reason_summary,
        }
