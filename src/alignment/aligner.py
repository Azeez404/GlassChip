"""Heterogeneous-sampling alignment for GLASSCHIP.

The frozen V1 time-series builder uses an *exact* inner join on the timestamp
instant. That is correct only for metrics sharing a rigid grid (the 20 s IPMI
triple). It cannot combine metrics recorded at different native rates -- e.g.
temperature/power/fan at ~20 s, CPU frequency at ~60 s, CPU utilisation at
~90 s -- because an exact join keeps almost nothing and a naive tolerance join
fabricates values.

``AsofAligner`` provides the honest alternative for heterogeneous rates:

* pick a reference metric (by default the finest-grained one) and keep its own
  timestamps as the output grid;
* attach each slower metric by a **causal, backward** as-of match -- the most
  recent *actually measured* sample at or before each reference instant;
* discard any attached value whose age exceeds a per-metric **max-staleness**
  bound, marking it explicitly missing.

Nothing is interpolated or invented. Every attached value is a real prior
measurement; its age is recorded in ``<role>_age_s`` and, when it is dropped
for being too old (or absent), ``<role>_missing`` is ``True`` and the value is
``NaN``. Per-metric native sampling intervals and missingness statistics are
returned in a report. The match is strictly backward, so no future information
leaks into any row.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

import numpy as np
import pandas as pd

__all__ = ["AsofAligner", "AlignmentError", "MetricAlignment"]

#: Default staleness bound as a multiple of a metric's native interval. A slow
#: metric's value is carried forward for at most this many native intervals.
DEFAULT_STALENESS_FACTOR: float = 1.5


class AlignmentError(Exception):
    """Raised when metrics cannot be aligned."""


@dataclass
class MetricAlignment:
    """Per-metric alignment metadata (part of the alignment report)."""

    role: str
    native_interval_s: float
    max_staleness_s: float
    n_total: int
    n_present: int
    n_missing: int
    median_age_s: float
    is_reference: bool = False

    @property
    def missing_fraction(self) -> float:
        return 0.0 if self.n_total == 0 else self.n_missing / self.n_total

    def as_dict(self) -> dict[str, Any]:
        d = self.__dict__.copy()
        d["missing_fraction"] = round(self.missing_fraction, 6)
        return d


@dataclass
class AsofAligner:
    """Align metrics with heterogeneous sampling intervals, honestly.

    Parameters
    ----------
    staleness_factor:
        Default max-staleness as a multiple of each metric's native interval,
        used when ``max_staleness`` does not specify a role. A value of ``1.5``
        means a slow metric is carried forward for at most 1.5 native intervals
        before its reading is treated as missing.
    """

    staleness_factor: float = DEFAULT_STALENESS_FACTOR

    # ------------------------------------------------------------------
    @staticmethod
    def _value_column(role: str, frame: pd.DataFrame) -> str:
        """Return the value column for a single-metric frame.

        Prefers a column named for the role (V1 convention); otherwise the sole
        column that is not ``timestamp``/``node``.
        """
        if role in frame.columns:
            return role
        candidates = [c for c in frame.columns if c not in ("timestamp", "node")]
        if len(candidates) != 1:
            raise AlignmentError(
                f"Cannot identify the value column for role {role!r}; "
                f"columns are {list(frame.columns)}."
            )
        return candidates[0]

    @staticmethod
    def estimate_interval_s(timestamps: pd.Series) -> float:
        """Median positive spacing (seconds) of a timestamp series."""
        ts = pd.to_datetime(pd.Series(timestamps)).sort_values()
        deltas = ts.diff().dt.total_seconds().to_numpy()
        deltas = deltas[np.isfinite(deltas) & (deltas > 0)]
        if deltas.size == 0:
            raise AlignmentError("Cannot estimate interval: need >= 2 distinct timestamps.")
        return float(np.median(deltas))

    def _prep(self, role: str, frame: pd.DataFrame) -> tuple[pd.DataFrame, str, float]:
        if "timestamp" not in frame.columns:
            raise AlignmentError(f"Frame for role {role!r} has no 'timestamp' column.")
        vcol = self._value_column(role, frame)
        f = frame[["timestamp", vcol]].copy()
        f["timestamp"] = pd.to_datetime(f["timestamp"])
        f = f.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
        if f.empty:
            raise AlignmentError(f"Frame for role {role!r} has no usable timestamps.")
        interval = self.estimate_interval_s(f["timestamp"]) if len(f) > 1 else float("nan")
        return f.rename(columns={vcol: role}), role, interval

    # ------------------------------------------------------------------
    def align(
        self,
        frames: Mapping[str, pd.DataFrame],
        reference: str | None = None,
        max_staleness: Mapping[str, float] | None = None,
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Align single-metric frames onto a reference grid, causally.

        Parameters
        ----------
        frames:
            Mapping of role -> frame. Each frame has ``timestamp`` and a value
            column (named for the role, or the single remaining column).
        reference:
            Role whose timestamps form the output grid. Defaults to the metric
            with the finest (smallest) native interval.
        max_staleness:
            Optional per-role staleness bound in seconds. Roles not listed use
            ``staleness_factor * native_interval``.

        Returns
        -------
        (frame, report):
            ``frame`` has ``timestamp``, the reference value column, and for
            each other role: ``<role>`` (value or NaN), ``<role>_age_s`` (age of
            the attached sample, or NaN), ``<role>_missing`` (bool). ``report``
            carries per-role :class:`MetricAlignment` dicts and settings.
        """
        if not frames:
            raise AlignmentError("No frames supplied to align.")

        prepped = {}
        intervals = {}
        for role, frame in frames.items():
            f, r, iv = self._prep(role, frame)
            prepped[r] = f
            intervals[r] = iv

        if reference is None:
            # finest grid = smallest finite native interval
            finite = {r: iv for r, iv in intervals.items() if np.isfinite(iv)}
            reference = min(finite, key=finite.get) if finite else next(iter(prepped))
        if reference not in prepped:
            raise AlignmentError(f"Reference role {reference!r} is not among the frames.")

        ref = prepped[reference].rename(columns={reference: reference})
        out = ref[["timestamp", reference]].copy()

        bounds = dict(max_staleness or {})
        reports: dict[str, MetricAlignment] = {
            reference: MetricAlignment(
                role=reference, native_interval_s=intervals[reference],
                max_staleness_s=0.0, n_total=len(out), n_present=len(out),
                n_missing=0, median_age_s=0.0, is_reference=True)
        }

        for role, f in prepped.items():
            if role == reference:
                continue
            bound = float(bounds.get(
                role,
                self.staleness_factor * intervals[role]
                if np.isfinite(intervals[role]) else np.inf))
            # causal backward as-of: most recent measured sample <= ref instant
            merged = pd.merge_asof(
                out[["timestamp"]], f, on="timestamp", direction="backward")
            src_ts = merged["timestamp"].where(merged[role].notna())
            # age of the attached sample; requires the source timestamp, which
            # merge_asof does not expose -> recompute via a second asof on index
            src = pd.merge_asof(
                out[["timestamp"]].assign(_i=np.arange(len(out))),
                f.assign(_src_ts=f["timestamp"]), on="timestamp",
                direction="backward")
            age = (out["timestamp"].to_numpy() - src["_src_ts"].to_numpy()) \
                .astype("timedelta64[s]").astype(float)
            value = src[role].to_numpy(dtype=float)
            too_old = ~np.isfinite(age) | (age > bound)
            missing = too_old | ~np.isfinite(value)
            value = np.where(missing, np.nan, value)
            age = np.where(missing, np.nan, age)

            out[role] = value
            out[f"{role}_age_s"] = age
            out[f"{role}_missing"] = missing
            present = int((~missing).sum())
            med_age = float(np.nanmedian(age)) if present else float("nan")
            reports[role] = MetricAlignment(
                role=role, native_interval_s=intervals[role], max_staleness_s=bound,
                n_total=len(out), n_present=present, n_missing=int(missing.sum()),
                median_age_s=med_age)

        report = {
            "reference": reference,
            "staleness_factor": self.staleness_factor,
            "n_rows": len(out),
            "metrics": {r: m.as_dict() for r, m in reports.items()},
            "policy": "causal backward as-of; last measured value within "
                      "max_staleness; never interpolated; older/absent -> missing",
        }
        return out.reset_index(drop=True), report
