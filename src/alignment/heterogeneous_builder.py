"""Heterogeneous-sampling time-series builder for the M100 record.

Combines M100 metrics recorded at different native rates into one per-node,
model-ready table WITHOUT the frozen V1 assumption of a rigid common grid and
WITHOUT fabricating values. It:

* maps physical M100 metric names to canonical roles;
* cleans each metric independently (a new metric-agnostic layer; the frozen V1
  ``Preprocessor`` is not used or modified);
* estimates native sampling interval and jitter per metric;
* aligns everything onto a configurable reference grid (default: temperature)
  with :class:`~alignment.aligner.AsofAligner` -- causal, backward, bounded
  by a per-metric max-staleness; older/absent readings are marked missing;
* emits ``<role>``, ``<role>_age_s``, ``<role>_missing`` and a machine-readable
  report.

The M100 raw files are not required to exercise the builder: raw per-metric
frames can be injected directly (``build_node(node, raw_frames=...)``), and the
dataset root is configurable. Nothing is interpolated, forward-filled beyond the
staleness bound, or invented.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from .aligner import AsofAligner, AlignmentError

__all__ = ["HeterogeneousTimeSeriesBuilder", "BuilderError",
           "DEFAULT_ROLE_METRICS", "DEFAULT_STALENESS_S"]

#: Canonical role -> M100 physical metric name (IPMI ~20 s; Ganglia 60/90 s).
DEFAULT_ROLE_METRICS: dict[str, str] = {
    "temperature": "p0_core0_temp",   # ipmi_pub, ~20 s
    "power": "p0_power",              # ipmi_pub, ~20 s
    "fan": "fan0_0",                  # ipmi_pub, ~20 s
    "frequency": "cpu_speed",         # ganglia_pub, ~60 s
    "utilization": "cpu_user",        # ganglia_pub, ~90 s
}

#: Per-role max-staleness (s) ~ 1.5x native interval. Configurable, not baked
#: into scientific logic; the effective values are echoed in the report.
DEFAULT_STALENESS_S: dict[str, float] = {
    "temperature": 30.0, "power": 30.0, "fan": 30.0,
    "frequency": 90.0, "utilization": 135.0,
}


class BuilderError(Exception):
    """Raised when a heterogeneous series cannot be built."""


def _interval_and_jitter(ts: pd.Series) -> dict[str, float]:
    """Native interval (median dt) and jitter statistics, in seconds."""
    dt = pd.to_datetime(ts).sort_values().diff().dt.total_seconds().to_numpy()
    dt = dt[np.isfinite(dt) & (dt > 0)]
    if dt.size == 0:
        return {"native_interval_s": float("nan"), "dt_std_s": float("nan"),
                "dt_p05_s": float("nan"), "dt_p95_s": float("nan"),
                "frac_off_grid": float("nan")}
    med = float(np.median(dt))
    off = float(np.mean(np.abs(dt - med) > 0.1 * med)) if med > 0 else float("nan")
    return {"native_interval_s": med, "dt_std_s": float(np.std(dt)),
            "dt_p05_s": float(np.percentile(dt, 5)),
            "dt_p95_s": float(np.percentile(dt, 95)), "frac_off_grid": off}


@dataclass
class HeterogeneousTimeSeriesBuilder:
    """Build per-node heterogeneous-rate series for the M100 record.

    Parameters
    ----------
    source:
        A ``DatasetLoader``, a dataset path, or ``None``. If ``None``, raw
        frames must be injected into :meth:`build_node`.
    role_metrics:
        Role -> physical metric name (default: :data:`DEFAULT_ROLE_METRICS`).
    staleness_s:
        Role -> max-staleness seconds (default: :data:`DEFAULT_STALENESS_S`).
    reference_role:
        Role whose timestamps form the output grid (default ``"temperature"``).
    """

    source: Any = None
    role_metrics: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_ROLE_METRICS))
    staleness_s: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_STALENESS_S))
    reference_role: str = "temperature"

    def __post_init__(self) -> None:
        self._loader = self._resolve_loader(self.source)
        if self.reference_role not in self.role_metrics:
            raise BuilderError(
                f"reference_role {self.reference_role!r} is not in role_metrics "
                f"{list(self.role_metrics)}.")

    # ------------------------------------------------------------------
    @staticmethod
    def _resolve_loader(source: Any):
        if source is None:
            return None
        try:  # lazy import so tests without the dataset need no loader deps
            from loader import DatasetLoader  # type: ignore
        except Exception as exc:  # noqa: BLE001
            raise BuilderError(f"Could not import DatasetLoader: {exc}") from exc
        if isinstance(source, DatasetLoader):
            return source
        return DatasetLoader(source)

    # ------------------------------------------------------------------
    @staticmethod
    def clean_metric(role: str, frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Metric-agnostic cleaning. Preserves real values and missingness.

        Normalises the timestamp to UTC datetime, rejects malformed rows (null
        timestamp or non-finite value), sorts chronologically, and drops
        duplicate timestamps deterministically (keep first after a stable sort).
        Never interpolates or forward-fills; gaps are preserved.
        """
        if "timestamp" not in frame.columns or "value" not in frame.columns:
            raise BuilderError(
                f"Frame for role {role!r} must have 'timestamp' and 'value'; "
                f"got {list(frame.columns)}.")
        n_in = len(frame)
        node = None
        if "node" in frame.columns and len(frame):
            uniq = pd.unique(frame["node"].dropna())
            if len(uniq) > 1:
                raise BuilderError(
                    f"Frame for role {role!r} spans multiple nodes {list(uniq)}; "
                    "the builder is per-node.")
            node = uniq[0] if len(uniq) else None

        df = frame.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        bad = df["timestamp"].isna() | ~np.isfinite(df["value"].to_numpy())
        n_rejected = int(bad.sum())
        df = df.loc[~bad]
        # stable sort then keep first occurrence per timestamp (deterministic)
        df = df.sort_values("timestamp", kind="mergesort")
        n_dupes = int(df["timestamp"].duplicated().sum())
        df = df.drop_duplicates(subset="timestamp", keep="first")
        clean = df[["timestamp", "value"]].rename(columns={"value": role}).reset_index(drop=True)
        report = {"role": role, "n_in": n_in, "n_rejected": n_rejected,
                  "n_duplicate_timestamps_dropped": n_dupes, "n_out": len(clean),
                  "node": (str(node) if node is not None else None),
                  **(_interval_and_jitter(clean["timestamp"]) if len(clean) > 1 else {})}
        return clean, report

    # ------------------------------------------------------------------
    def _load_raw(self, node: str | int) -> dict[str, pd.DataFrame]:
        if self._loader is None:
            raise BuilderError(
                "No dataset loader configured. Provide `source=<path or "
                "DatasetLoader>` or inject `raw_frames=` into build_node().")
        out: dict[str, pd.DataFrame] = {}
        for role, metric in self.role_metrics.items():
            try:
                out[role] = self._loader.load_metric_for_node(metric, str(node))
            except Exception as exc:  # noqa: BLE001 - record, continue with others
                out[role] = pd.DataFrame(columns=["timestamp", "value", "node"])
                out[role].attrs["load_error"] = f"{type(exc).__name__}: {exc}"
        return out

    def build_node(
        self,
        node: str | int,
        raw_frames: Mapping[str, pd.DataFrame] | None = None,
        return_report: bool = True,
    ):
        """Build one node's aligned heterogeneous series.

        Parameters
        ----------
        node:
            Node identifier.
        raw_frames:
            Optional role -> raw single-metric frame. If omitted, frames are
            loaded from the configured dataset.
        """
        raw = dict(raw_frames) if raw_frames is not None else self._load_raw(node)

        clean: dict[str, pd.DataFrame] = {}
        cleaning: dict[str, Any] = {}
        for role in self.role_metrics:
            if role not in raw:
                continue
            c, rep = self.clean_metric(role, raw[role])
            cleaning[role] = rep
            if len(c) >= 1:
                clean[role] = c

        if self.reference_role not in clean or len(clean[self.reference_role]) < 2:
            raise BuilderError(
                f"Reference role {self.reference_role!r} has insufficient clean "
                "data to form the alignment grid.")

        staleness = {r: float(self.staleness_s[r]) for r in clean
                     if r in self.staleness_s}
        aligned, align_report = AsofAligner().align(
            clean, reference=self.reference_role, max_staleness=staleness)
        aligned.insert(1, "node", str(node))

        if not return_report:
            return aligned

        report = {
            "node": str(node),
            "reference": {
                "role": self.reference_role,
                "metric": self.role_metrics[self.reference_role],
                "interval_s": cleaning.get(self.reference_role, {}).get("native_interval_s"),
            },
            "alignment_direction": "backward (causal)",
            "role_to_metric": dict(self.role_metrics),
            "effective_staleness_s": staleness,
            "dataset_root": (str(getattr(self._loader, "root", None))
                             if self._loader is not None else None),
            "cleaning": cleaning,
            "n_rows_aligned": len(aligned),
            "metrics": align_report["metrics"],
            "missingness": {r: round(m["missing_fraction"], 6)
                            for r, m in align_report["metrics"].items()},
            "columns": list(aligned.columns),
        }
        return aligned, report
