"""Per-metric cleaning for GLASSCHIP-V1.

Does exactly four things:

1. Sorts by timestamp.
2. Converts dtypes (IPMI stores ``value`` as ``int32``; models want float).
3. Drops records whose values are **physically impossible**.
4. Drops exact duplicate ``(timestamp)`` records.

Everything else is forbidden. In particular this module never normalises,
interpolates, resamples, reindexes, forward-fills, engineers features, or
invents a timestamp or a value. A record that is missing stays missing; a
gap stays a gap.

Physical bounds are permissive by design: they reject the impossible
(negative power, 500 °C), not the merely unusual. Narrowing them would be a
scientific filtering decision, not preprocessing.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from loader import DatasetLoader, DatasetLoaderError, NodeNotFoundError
from .metric_selector import GLASSCHIP_V1_METRICS

__all__ = [
    "Preprocessor",
    "PreprocessingError",
    "PHYSICAL_BOUNDS",
    "MODEL_COLUMNS",
]

#: Inclusive ``(minimum, maximum)`` bounds per role, in the units below.
#: A record outside its bound is physically impossible and is removed.
#:
#: ``temperature``  degrees Celsius. IPMI sensor plausible span. POWER9
#:                  Tjmax is around 100 C; observed in record 21-03 is
#:                  31-54 C.
#: ``power``        watts, per socket. POWER9 AC922 socket TDP is roughly
#:                  250 W; observed maximum in record 21-03 is 268 W.
#: ``fan_speed``    RPM. Observed maximum in record 21-03 is 10,100 RPM.
#:                  Zero is retained: a stopped fan is possible, and 2.5 %
#:                  of raw ``fan0_0`` rows read exactly zero.
PHYSICAL_BOUNDS: dict[str, tuple[float, float]] = {
    "temperature": (0.0, 125.0),
    "power": (0.0, 500.0),
    "fan_speed": (0.0, 30000.0),
}

#: Column order of a model-ready frame.
MODEL_COLUMNS: tuple[str, ...] = (
    "timestamp",
    "node",
    "temperature",
    "power",
    "fan_speed",
)


class PreprocessingError(Exception):
    """Raised when preprocessing cannot be carried out."""


class Preprocessor:
    """Clean single-metric series without altering any surviving value.

    Parameters
    ----------
    loader:
        A :class:`~loader.DatasetLoader` or a dataset path.
    bounds:
        Override for :data:`PHYSICAL_BOUNDS`. Supplying a narrower bound is
        a scientific decision and must be justified by the caller.

    Examples
    --------
    >>> pre = Preprocessor("datasets/21-03")                 # doctest: +SKIP
    >>> frame = pre.preprocess_metric("p0_power", "15", "power")  # doctest: +SKIP
    """

    def __init__(
        self,
        loader: DatasetLoader | str,
        bounds: dict[str, tuple[float, float]] | None = None,
    ) -> None:
        try:
            self.loader = (
                loader
                if isinstance(loader, DatasetLoader)
                else DatasetLoader(loader)
            )
        except DatasetLoaderError as exc:
            raise PreprocessingError(f"Could not open dataset: {exc}") from exc
        self.bounds = dict(bounds or PHYSICAL_BOUNDS)

    # ------------------------------------------------------------------
    # Single metric
    # ------------------------------------------------------------------

    def preprocess_metric(
        self,
        metric: str,
        node: str | int,
        role: str,
        return_report: bool = False,
    ) -> pd.DataFrame | tuple[pd.DataFrame, dict[str, Any]]:
        """Load one metric for one node and clean it.

        Parameters
        ----------
        metric:
            Metric name, e.g. ``"p0_power"``.
        node:
            Node identifier.
        role:
            Role name used for the value column, e.g. ``"power"``. Must
            have an entry in ``self.bounds``.
        return_report:
            Also return a removal report.

        Returns
        -------
        pandas.DataFrame
            Columns ``timestamp``, ``node``, ``<role>``. Sorted ascending
            by timestamp, ``float64`` values, timezone-aware UTC stamps.
        dict, optional
            ``n_input``, ``n_output``, ``n_removed_null``,
            ``n_removed_out_of_bounds``, ``n_removed_duplicate``,
            ``bounds``, and ``removal_ratio``.

        Raises
        ------
        PreprocessingError
            If the role has no bound, or the node/metric cannot be read.

        Notes
        -----
        Removal is the only operation applied. No surviving value is
        modified beyond an ``int32`` to ``float64`` widening, which is
        exact for the integer ranges present.
        """
        if role not in self.bounds:
            raise PreprocessingError(
                f"No physical bound defined for role {role!r}. "
                f"Known roles: {sorted(self.bounds)}."
            )

        try:
            frame = self.loader.load_metric_for_node(
                metric, node, columns=["timestamp", "value", "node"]
            )
        except (NodeNotFoundError, DatasetLoaderError) as exc:
            raise PreprocessingError(
                f"Could not load {metric!r} for node {node!r}: {exc}"
            ) from exc

        n_input = len(frame)

        # 1. dtype handling. int32 -> float64 is exact here.
        frame = frame.rename(columns={"value": role})
        frame[role] = frame[role].astype("float64")
        frame["node"] = frame["node"].astype("string")

        # 2. timestamp handling: ensure UTC-aware, then sort ascending.
        stamps = pd.to_datetime(frame["timestamp"], utc=True)
        frame["timestamp"] = stamps
        frame = frame.sort_values("timestamp", kind="mergesort")

        # 3. drop nulls. These are absent readings, not fabricable ones.
        before = len(frame)
        frame = frame[frame[role].notna() & frame["timestamp"].notna()]
        n_null = before - len(frame)

        # 4. drop physically impossible records.
        low, high = self.bounds[role]
        before = len(frame)
        frame = frame[(frame[role] >= low) & (frame[role] <= high)]
        n_bounds = before - len(frame)

        # 5. drop exact duplicate timestamps. Keeping both would make the
        #    series ill-defined; no value is merged or averaged.
        before = len(frame)
        frame = frame.drop_duplicates(subset=["timestamp"], keep="first")
        n_dup = before - len(frame)

        frame = frame[["timestamp", "node", role]].reset_index(drop=True)

        if not return_report:
            return frame

        report = {
            "metric": metric,
            "role": role,
            "node": str(node),
            "n_input": n_input,
            "n_output": len(frame),
            "n_removed_null": n_null,
            "n_removed_out_of_bounds": n_bounds,
            "n_removed_duplicate": n_dup,
            "n_removed_total": n_input - len(frame),
            "removal_ratio": round(
                (n_input - len(frame)) / n_input, 6
            ) if n_input else 0.0,
            "bounds": {"min": low, "max": high},
        }
        return frame, report

    # ------------------------------------------------------------------
    # All roles for one node
    # ------------------------------------------------------------------

    def preprocess_node(
        self,
        node: str | int,
        roles: dict[str, str] | None = None,
        return_report: bool = False,
    ) -> dict[str, pd.DataFrame] | tuple[dict[str, pd.DataFrame], dict[str, Any]]:
        """Clean every selected metric for one node.

        Parameters
        ----------
        node:
            Node identifier.
        roles:
            Role-to-metric mapping. Defaults to
            :data:`~metric_selector.GLASSCHIP_V1_METRICS`.
        return_report:
            Also return per-role removal reports.

        Returns
        -------
        dict of str to pandas.DataFrame
            One cleaned frame per role.
        dict, optional
            Per-role removal reports.

        Raises
        ------
        PreprocessingError
            If any role fails to preprocess.
        """
        roles = dict(roles or GLASSCHIP_V1_METRICS)
        frames: dict[str, pd.DataFrame] = {}
        reports: dict[str, Any] = {}

        for role, metric in roles.items():
            frame, report = self.preprocess_metric(
                metric, node, role, return_report=True
            )
            frames[role] = frame
            reports[role] = report

        if not return_report:
            return frames
        return frames, reports

    # ------------------------------------------------------------------
    # Final shaping
    # ------------------------------------------------------------------

    def prepare_model_input(
        self, frame: pd.DataFrame, columns: tuple[str, ...] = MODEL_COLUMNS
    ) -> pd.DataFrame:
        """Apply final column order, dtypes, and ordering.

        Parameters
        ----------
        frame:
            A joined frame, typically from
            :class:`~timeseries_builder.TimeSeriesBuilder`.
        columns:
            Desired column order. Columns absent from ``frame`` are
            skipped.

        Returns
        -------
        pandas.DataFrame
            Sorted ascending by timestamp, contiguous integer index,
            ``float64`` value columns, UTC-aware timestamps.

        Raises
        ------
        PreprocessingError
            If ``frame`` has no ``timestamp`` column.

        Notes
        -----
        Shaping only. No row is added or removed and no value is altered.
        """
        if "timestamp" not in frame.columns:
            raise PreprocessingError(
                "Frame has no 'timestamp' column; cannot prepare model input."
            )

        result = frame.copy()
        result["timestamp"] = pd.to_datetime(result["timestamp"], utc=True)

        for column in result.columns:
            if column in ("timestamp", "node"):
                continue
            if pd.api.types.is_numeric_dtype(result[column]):
                result[column] = result[column].astype("float64")

        ordered = [c for c in columns if c in result.columns]
        remaining = [c for c in result.columns if c not in ordered]
        result = result[ordered + remaining]

        return result.sort_values(
            "timestamp", kind="mergesort"
        ).reset_index(drop=True)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(loader={self.loader!r}, "
            f"roles={sorted(self.bounds)})"
        )
