"""Time-series construction for GLASSCHIP-V1.

Joins cleaned single-metric frames into one model-ready table:

===========================  ===========  =======  ==========
timestamp                    temperature  power    fan_speed
===========================  ===========  =======  ==========
2021-03-01 00:00:00+00:00    44.0         34.0     4300.0
2021-03-01 00:00:20+00:00    45.0         34.0     4300.0
2021-03-01 00:00:40+00:00    44.0         34.0     4300.0
===========================  ===========  =======  ==========

The join is an **exact inner join on the timestamp instant**. No tolerance,
no ``merge_asof``, no reindexing onto a regular grid, no fill of any kind.

This is viable only because the GLASSCHIP-V1 triple all originate from
``ipmi_pub``, which samples on a rigid 20 s grid with a measured 100 %
exact timestamp match between the three metrics. It is precisely why
``cpu_user`` and ``cpu_speed`` are out of scope: at 5.7-5.8 % exact match
they would require a tolerance join, and that is value fabrication.

A row survives only if **all three** metrics recorded a value at that exact
instant. Gaps remain gaps.
"""

from __future__ import annotations

from functools import reduce
from typing import Any, Iterable

import pandas as pd

from loader import DatasetLoader
from .metric_selector import (
    GLASSCHIP_V1_METRICS,
    IncompatibleSelectionError,
    MetricSelector,
)
from .preprocessor import MODEL_COLUMNS, Preprocessor, PreprocessingError

__all__ = ["TimeSeriesBuilder", "TimeSeriesError"]


class TimeSeriesError(Exception):
    """Raised when a time series cannot be constructed."""


class TimeSeriesBuilder:
    """Build model-ready per-node time series from validated metrics.

    Parameters
    ----------
    source:
        A :class:`~loader.DatasetLoader` or a dataset path.
    roles:
        Role-to-metric mapping. Defaults to
        :data:`~metric_selector.GLASSCHIP_V1_METRICS`.
    validate:
        Run the validation gate on construction. Leaving this ``True`` is
        strongly recommended; it is the mechanism that stops preprocessing
        when the validator says ``FAIL``.

    Raises
    ------
    TimeSeriesError
        If the dataset cannot be opened.
    IncompatibleSelectionError
        If ``validate`` is set and the validator returns ``FAIL``.

    Examples
    --------
    >>> builder = TimeSeriesBuilder("datasets/21-03")   # doctest: +SKIP
    >>> frame = builder.build_timeseries("15")          # doctest: +SKIP
    """

    def __init__(
        self,
        source: DatasetLoader | str,
        roles: dict[str, str] | None = None,
        validate: bool = True,
    ) -> None:
        try:
            self.loader = (
                source
                if isinstance(source, DatasetLoader)
                else DatasetLoader(source)
            )
        except Exception as exc:
            raise TimeSeriesError(f"Could not open dataset: {exc}") from exc

        self.roles = dict(roles or GLASSCHIP_V1_METRICS)
        self.selector = MetricSelector(self.loader)
        self.preprocessor = Preprocessor(self.loader)
        self.validation: dict[str, Any] | None = None

        if validate:
            # Raises IncompatibleSelectionError on FAIL. This is the gate.
            self.validation = self.selector.select_metrics(self.roles)

    # ------------------------------------------------------------------
    # Alignment
    # ------------------------------------------------------------------

    def align_metrics(
        self, frames: dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """Exact-inner-join cleaned single-metric frames on timestamp.

        Parameters
        ----------
        frames:
            Mapping of role to cleaned frame, each with ``timestamp``,
            ``node``, and a value column named for its role.

        Returns
        -------
        pandas.DataFrame
            One row per instant at which every input recorded a value.

        Raises
        ------
        TimeSeriesError
            If fewer than one frame is given, a frame lacks ``timestamp``,
            or the join yields no rows.

        Notes
        -----
        Uses ``how="inner"`` on the exact timestamp. Rows present in some
        metrics but not others are dropped, never filled. The result is a
        strict subset of every input.
        """
        if not frames:
            raise TimeSeriesError("No frames supplied to align.")

        for role, frame in frames.items():
            if "timestamp" not in frame.columns:
                raise TimeSeriesError(
                    f"Frame for role {role!r} has no 'timestamp' column."
                )

        ordered = [
            frames[role].drop(columns=["node"], errors="ignore")
            if index else frames[role]
            for index, role in enumerate(frames)
        ]

        joined = reduce(
            lambda left, right: left.merge(
                right, on="timestamp", how="inner", validate="one_to_one"
            ),
            ordered,
        )

        if joined.empty:
            raise TimeSeriesError(
                "Exact timestamp join produced zero rows. The metrics share "
                "no common instants; a tolerance join is not permitted."
            )
        return joined

    # ------------------------------------------------------------------
    # Per-node construction
    # ------------------------------------------------------------------

    def build_timeseries(
        self,
        node: str | int,
        return_report: bool = False,
    ) -> pd.DataFrame | tuple[pd.DataFrame, dict[str, Any]]:
        """Build the model-ready time series for one node.

        Parameters
        ----------
        node:
            Node identifier. Must carry every selected metric.
        return_report:
            Also return a construction report.

        Returns
        -------
        pandas.DataFrame
            Columns ``timestamp``, ``node``, ``temperature``, ``power``,
            ``fan_speed``. Sorted ascending, contiguous index.
        dict, optional
            Per-role cleaning reports plus join retention statistics and a
            contiguous-segment inventory.

        Raises
        ------
        TimeSeriesError
            If the node is unusable or the join yields nothing.

        Notes
        -----
        The reported segments describe where the data actually is. They are
        boundaries only; nothing is inserted between them.
        """
        try:
            node_id = self.selector.select_node(node, self.roles)
        except IncompatibleSelectionError:
            raise
        except Exception as exc:
            raise TimeSeriesError(
                f"Node {node!r} cannot be used: {exc}"
            ) from exc

        try:
            frames, reports = self.preprocessor.preprocess_node(
                node_id, self.roles, return_report=True
            )
        except PreprocessingError as exc:
            raise TimeSeriesError(
                f"Preprocessing failed for node {node_id!r}: {exc}"
            ) from exc

        joined = self.align_metrics(frames)
        result = self.preprocessor.prepare_model_input(joined, MODEL_COLUMNS)

        if "node" not in result.columns:
            result.insert(1, "node", node_id)

        if not return_report:
            return result

        inputs = {role: report["n_output"] for role, report in reports.items()}
        smallest = min(inputs.values()) if inputs else 0
        report = {
            "node": node_id,
            "roles": dict(self.roles),
            "cleaning": reports,
            "n_rows_per_role_after_cleaning": inputs,
            "n_rows_joined": len(result),
            "join_retention_ratio": round(
                len(result) / smallest, 6
            ) if smallest else 0.0,
            "first_timestamp": str(result["timestamp"].iloc[0]),
            "last_timestamp": str(result["timestamp"].iloc[-1]),
            "segments": self._segments(result["timestamp"]),
            "columns": list(result.columns),
        }
        return result, report

    def construct_node_dataframe(
        self, node: str | int
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Build one node's series and its report together.

        Convenience wrapper over :meth:`build_timeseries`.

        Parameters
        ----------
        node:
            Node identifier.

        Returns
        -------
        tuple
            ``(frame, report)``.
        """
        return self.build_timeseries(node, return_report=True)

    def build_many(
        self, nodes: Iterable[str | int], skip_failures: bool = True
    ) -> dict[str, pd.DataFrame]:
        """Build series for several nodes.

        Parameters
        ----------
        nodes:
            Node identifiers.
        skip_failures:
            Skip nodes that cannot be built instead of raising. Skipped
            nodes are omitted from the result; nothing is substituted.

        Returns
        -------
        dict of str to pandas.DataFrame
            One frame per successfully built node.

        Raises
        ------
        TimeSeriesError
            If ``skip_failures`` is ``False`` and any node fails.
        """
        built: dict[str, pd.DataFrame] = {}
        for node in nodes:
            try:
                built[str(node)] = self.build_timeseries(node)
            except TimeSeriesError:
                if not skip_failures:
                    raise
        return built

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _segments(
        stamps: pd.Series, gap_multiplier: float = 3.0
    ) -> list[dict[str, Any]]:
        """Describe contiguous runs, longest first. Boundaries only."""
        if len(stamps) < 2:
            return []

        deltas = stamps.diff().dt.total_seconds().dropna()
        median = float(deltas.median())
        gaps = deltas > (median * gap_multiplier)
        breaks = list(deltas.index[gaps])

        starts = [0] + breaks
        ends = [b - 1 for b in breaks] + [len(stamps) - 1]

        segments = []
        for lo, hi in zip(starts, ends):
            duration = float(
                (stamps.iloc[hi] - stamps.iloc[lo]).total_seconds()
            )
            segments.append(
                {
                    "start": str(stamps.iloc[lo]),
                    "end": str(stamps.iloc[hi]),
                    "duration_h": round(duration / 3600.0, 3),
                    "n_samples": int(hi - lo + 1),
                }
            )
        segments.sort(key=lambda s: s["duration_h"], reverse=True)
        return segments

    def __repr__(self) -> str:
        return f"{type(self).__name__}(roles={list(self.roles)})"
