"""Scientific inspector for the M100 ExaData telemetry record.

Answers exactly one question: **what can safely exist together?**

This module reports. It never repairs. It does not interpolate, resample,
align, impute, drop, or normalise anything. Where two metrics cannot be
joined, it says so and stops; constructing a joined series is preprocessing's
responsibility, not validation's.

Every threshold used to reach a verdict is a module-level constant, so any
judgement made here is auditable and adjustable.

Companion to :mod:`loader`, which it uses read-only.
"""

from __future__ import annotations

from typing import Any, Iterable, Sequence

import numpy as np
import pandas as pd

from loader import (
    NODE_SCOPED_PLUGINS,
    DatasetLoader,
    DatasetLoaderError,
    MetricNotFoundError,
    NodeNotFoundError,
)

__all__ = [
    "DatasetValidator",
    "ValidationError",
    "GLASSCHIP_MANDATORY_INPUTS",
    "EXACT_MATCH_TOLERANCE_S",
    "JITTER_TOLERANCE_S",
    "MIN_EXACT_MATCH_RATIO",
    "MIN_NODE_OVERLAP_RATIO",
    "MIN_COVERAGE_RATIO",
    "MIN_CONTIGUOUS_SEGMENT_S",
    "GAP_THRESHOLD_MULTIPLIER",
]

# --------------------------------------------------------------------------
# Verdict thresholds. Every judgement in this module traces to one of these.
# --------------------------------------------------------------------------

#: Two timestamps count as identical only at this tolerance. Zero means the
#: instants must be bit-identical; anything looser is already interpolation.
EXACT_MATCH_TOLERANCE_S: float = 0.0

#: Spread of inter-sample intervals below which a series is called a rigid
#: grid rather than a jittered stream.
JITTER_TOLERANCE_S: float = 0.5

#: Fraction of the sparser series' timestamps that must land exactly on the
#: denser series' timestamps before an exact join is declared viable.
MIN_EXACT_MATCH_RATIO: float = 0.95

#: Fraction of the smaller node set that must be shared before two metrics
#: are called node-compatible.
MIN_NODE_OVERLAP_RATIO: float = 0.95

#: Observed samples divided by samples implied by the nominal interval over
#: the full span. Below this the series is reported as sparse.
MIN_COVERAGE_RATIO: float = 0.90

#: Shortest contiguous run, in seconds, that can carry a thermal transient
#: fit. Twelve hours at 20 s is ~2160 samples, ample for R_th and C_th.
MIN_CONTIGUOUS_SEGMENT_S: float = 12 * 3600.0

#: An interval this many times the median counts as a gap, not a sample.
GAP_THRESHOLD_MULTIPLIER: float = 3.0

#: Mandatory GLASSCHIP-V1 inputs, mapped to a representative metric.
#: Values are metric names verified present in record 21-03.
GLASSCHIP_MANDATORY_INPUTS: dict[str, str] = {
    "temperature": "p0_core0_temp",
    "power": "p0_power",
    "frequency": "cpu_speed",
    "cpu_utilisation": "cpu_user",
    "fan_speed": "fan0_0",
}


class ValidationError(Exception):
    """Raised when a validation cannot be carried out at all."""


class DatasetValidator:
    """Read-only scientific inspector over a :class:`~loader.DatasetLoader`.

    Parameters
    ----------
    loader:
        An initialised :class:`~loader.DatasetLoader`, or a path from which
        one will be constructed.

    Examples
    --------
    >>> validator = DatasetValidator("datasets/21-03")   # doctest: +SKIP
    >>> validator.validate_glasschip_inputs()["verdict"] # doctest: +SKIP
    'FAIL'
    """

    def __init__(self, loader: DatasetLoader | str) -> None:
        if isinstance(loader, DatasetLoader):
            self.loader = loader
        else:
            try:
                self.loader = DatasetLoader(loader)
            except DatasetLoaderError as exc:
                raise ValidationError(
                    f"Could not open dataset at {loader!r}: {exc}"
                ) from exc

        self._node_sets: dict[str, list[str]] = {}
        self._timing: dict[tuple[str, str], dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _plugin_of(self, metric: str) -> str:
        """Return the owning plugin of ``metric``."""
        return self.loader._index[metric]["plugin"]  # noqa: SLF001

    def _is_node_scoped(self, metric: str) -> bool:
        """Whether ``metric`` carries a per-compute-node ``node`` column."""
        return self._plugin_of(metric) in NODE_SCOPED_PLUGINS

    def _nodes(self, metric: str) -> list[str]:
        """Cached exact node set for ``metric``."""
        if metric not in self._node_sets:
            self._node_sets[metric] = self.loader.nodes_for_metric(metric)
        return self._node_sets[metric]

    def _reference_node(self, metrics: Sequence[str]) -> str | None:
        """Pick a node present in every node-scoped metric given."""
        scoped = [m for m in metrics if self._is_node_scoped(m)]
        if not scoped:
            return None
        common: set[str] | None = None
        for metric in scoped:
            nodes = set(self._nodes(metric))
            common = nodes if common is None else common & nodes
        if not common:
            return None
        numeric = [n for n in common if n.isdigit()]
        return min(numeric, key=int) if numeric else sorted(common)[0]

    def _timing_profile(self, metric: str, node: str) -> dict[str, Any]:
        """Measure the sampling behaviour of one metric on one node.

        Returns interval statistics, grid regularity, coverage against the
        nominal interval, gap inventory, and contiguous segment inventory.
        No value is altered and nothing is filled in.
        """
        key = (metric, node)
        if key in self._timing:
            return self._timing[key]

        frame = self.loader.load_metric_for_node(
            metric, node, columns=["timestamp", "value"]
        )
        stamps = frame["timestamp"].sort_values().reset_index(drop=True)
        # .diff() yields exactly one NaN at index 0 (no predecessor). The
        # dropna() below removes that computational artifact only. No
        # observation is discarded and no value is altered anywhere in this
        # module.
        deltas = stamps.diff().dt.total_seconds().dropna()

        if deltas.empty:
            profile: dict[str, Any] = {
                "metric": metric,
                "node": node,
                "n_samples": int(len(stamps)),
                "insufficient_samples": True,
            }
            self._timing[key] = profile
            return profile

        median_dt = float(deltas.median())
        span_s = float(
            (stamps.iloc[-1] - stamps.iloc[0]).total_seconds()
        )
        gap_mask = deltas > (median_dt * GAP_THRESHOLD_MULTIPLIER)
        gaps = deltas[gap_mask]

        # Contiguous segments are delimited by gaps; boundaries only, no
        # data is modified or created.
        breaks = list(deltas.index[gap_mask])
        starts = [0] + breaks
        ends = [b - 1 for b in breaks] + [len(stamps) - 1]
        segments = []
        for lo, hi in zip(starts, ends):
            seg_s = float(
                (stamps.iloc[hi] - stamps.iloc[lo]).total_seconds()
            )
            segments.append(
                {
                    "start": str(stamps.iloc[lo]),
                    "end": str(stamps.iloc[hi]),
                    "duration_s": seg_s,
                    "duration_h": round(seg_s / 3600.0, 3),
                    "n_samples": int(hi - lo + 1),
                }
            )
        segments.sort(key=lambda s: s["duration_s"], reverse=True)

        expected = span_s / median_dt if median_dt > 0 else np.nan
        coverage = float(len(stamps) / expected) if expected else np.nan
        jitter = float(deltas[~gap_mask].std()) if (~gap_mask).any() else 0.0
        longest = segments[0]["duration_s"] if segments else 0.0

        profile = {
            "metric": metric,
            "node": node,
            "plugin": self._plugin_of(metric),
            "n_samples": int(len(stamps)),
            "first_timestamp": str(stamps.iloc[0]),
            "last_timestamp": str(stamps.iloc[-1]),
            "span_s": span_s,
            "span_days": round(span_s / 86400.0, 3),
            "median_interval_s": median_dt,
            "mean_interval_s": float(deltas.mean()),
            "min_interval_s": float(deltas.min()),
            "max_interval_s": float(deltas.max()),
            "interval_jitter_s": round(jitter, 4),
            "is_regular_grid": bool(jitter <= JITTER_TOLERANCE_S),
            "coverage_ratio": round(coverage, 5),
            "is_sparse": bool(coverage < MIN_COVERAGE_RATIO),
            "n_gaps": int(gap_mask.sum()),
            "total_gap_s": float(gaps.sum()) if not gaps.empty else 0.0,
            "largest_gap_s": float(gaps.max()) if not gaps.empty else 0.0,
            "largest_gap_h": (
                round(float(gaps.max()) / 3600.0, 3) if not gaps.empty else 0.0
            ),
            "n_segments": len(segments),
            "longest_segment_s": longest,
            "longest_segment_h": round(longest / 3600.0, 3),
            "segments": segments[:10],
            "insufficient_samples": False,
        }
        self._timing[key] = profile
        return profile

    # ------------------------------------------------------------------
    # 1. Metric validation
    # ------------------------------------------------------------------

    def validate_metric(
        self, metric: str, sample_node: str | int | None = None
    ) -> dict[str, Any]:
        """Report existence, schema, size, timestamps, and node availability.

        Parameters
        ----------
        metric:
            Metric name.
        sample_node:
            Node used for per-node timing statistics. ``None`` selects the
            lowest-numbered node present in the metric.

        Returns
        -------
        dict
            ``exists``, ``plugin``, ``node_scoped``, ``columns``,
            ``dtypes``, ``n_rows``, ``n_files``, ``size_mb``,
            ``has_timestamp``, ``has_node``, ``n_nodes``, ``timing``,
            and ``issues``.

        Notes
        -----
        Row counts come from Parquet footers. No row data is read except
        the single sampled node used for timing.
        """
        issues: list[str] = []

        try:
            entry = self.loader._index[metric]  # noqa: SLF001
        except KeyError:
            return {
                "metric": metric,
                "exists": False,
                "issues": [f"Metric {metric!r} is not present in the record."],
            }

        import pyarrow.parquet as pq

        columns: list[str] = []
        dtypes: dict[str, str] = {}
        n_rows = 0
        for path in entry["files"]:
            parquet = pq.ParquetFile(path)
            n_rows += parquet.metadata.num_rows
            if not columns:
                schema = parquet.schema_arrow
                columns = list(schema.names)
                dtypes = {f.name: str(f.type) for f in schema}

        has_timestamp = "timestamp" in columns
        has_node = "node" in columns
        node_scoped = self._is_node_scoped(metric)

        if not has_timestamp:
            issues.append("No 'timestamp' column: not a time series.")
        if not has_node and node_scoped:
            issues.append("Plugin is node-scoped but 'node' column is absent.")
        if n_rows == 0:
            issues.append("Metric contains zero rows.")

        node_ids = self._nodes(metric) if has_node else []
        timing: dict[str, Any] | None = None

        if has_timestamp and node_ids:
            node = str(sample_node) if sample_node is not None else None
            if node is not None and node not in node_ids:
                issues.append(
                    f"Requested sample_node {node!r} absent from this metric."
                )
                node = None
            if node is None:
                numeric = [n for n in node_ids if n.isdigit()]
                node = min(numeric, key=int) if numeric else node_ids[0]
            try:
                timing = self._timing_profile(metric, node)
            except (NodeNotFoundError, DatasetLoaderError) as exc:
                issues.append(f"Timing profile unavailable: {exc}")

        if timing and not timing.get("insufficient_samples"):
            if timing["is_sparse"]:
                issues.append(
                    f"Sparse: coverage {timing['coverage_ratio']:.1%} of the "
                    f"nominal {timing['median_interval_s']:.0f}s grid over "
                    f"{timing['span_days']:.2f} days."
                )
            if timing["largest_gap_s"] > MIN_CONTIGUOUS_SEGMENT_S:
                issues.append(
                    f"Contains a {timing['largest_gap_h']:.1f} h gap; "
                    f"longest contiguous run is "
                    f"{timing['longest_segment_h']:.2f} h."
                )
            if not timing["is_regular_grid"]:
                issues.append(
                    f"Irregular sampling: jitter "
                    f"{timing['interval_jitter_s']:.2f}s exceeds "
                    f"{JITTER_TOLERANCE_S}s."
                )

        return {
            "metric": metric,
            "exists": True,
            "plugin": entry["plugin"],
            "node_scoped": node_scoped,
            "columns": columns,
            "dtypes": dtypes,
            "value_dtype": dtypes.get("value"),
            "n_rows": n_rows,
            "n_files": len(entry["files"]),
            "size_mb": round(
                sum(f.stat().st_size for f in entry["files"]) / 1e6, 3
            ),
            "has_timestamp": has_timestamp,
            "has_node": has_node,
            "n_nodes": len(node_ids),
            "node_id_min": node_ids[0] if node_ids else None,
            "node_id_max": node_ids[-1] if node_ids else None,
            "timing": timing,
            "issues": issues,
            "valid": not issues,
        }

    # ------------------------------------------------------------------
    # 2. Node validation
    # ------------------------------------------------------------------

    def validate_node(
        self,
        node: str | int,
        metrics: Iterable[str] | None = None,
        plugins: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        """Report which metrics and plugins carry a given node.

        Parameters
        ----------
        node:
            Node identifier.
        metrics:
            Metric subset to check. ``None`` checks every node-scoped
            metric, which reads one ``node`` column per metric.
        plugins:
            Plugin subset. Ignored when ``metrics`` is given.

        Returns
        -------
        dict
            ``exists``, ``present_in_plugins``, ``absent_from_plugins``,
            ``available_metrics``, ``unavailable_metrics``, per-plugin
            counts, and ``issues``.
        """
        node_id = str(node)

        if metrics is None:
            allowed = (
                NODE_SCOPED_PLUGINS
                if plugins is None
                else NODE_SCOPED_PLUGINS & set(plugins)
            )
            candidates = [
                name
                for name in self.loader.get_available_metrics()
                if self._plugin_of(name) in allowed
            ]
        else:
            candidates = [m for m in metrics if self._is_node_scoped(m)]

        available: list[str] = []
        unavailable: list[str] = []
        by_plugin: dict[str, dict[str, int]] = {}

        for metric in candidates:
            plugin = self._plugin_of(metric)
            stats = by_plugin.setdefault(plugin, {"present": 0, "absent": 0})
            if node_id in set(self._nodes(metric)):
                available.append(metric)
                stats["present"] += 1
            else:
                unavailable.append(metric)
                stats["absent"] += 1

        present_plugins = sorted(
            p for p, s in by_plugin.items() if s["present"] > 0
        )
        absent_plugins = sorted(
            p for p, s in by_plugin.items() if s["present"] == 0
        )

        issues: list[str] = []
        if not available:
            issues.append(
                f"Node {node_id!r} appears in none of the "
                f"{len(candidates)} metrics checked."
            )
        if absent_plugins:
            issues.append(
                f"Node {node_id!r} is absent from plugin(s): "
                f"{absent_plugins}. Node ID namespaces are plugin-specific."
            )

        return {
            "node": node_id,
            "exists": bool(available),
            "n_metrics_checked": len(candidates),
            "n_available": len(available),
            "n_unavailable": len(unavailable),
            "present_in_plugins": present_plugins,
            "absent_from_plugins": absent_plugins,
            "available_metrics": sorted(available),
            "unavailable_metrics": sorted(unavailable),
            "by_plugin": by_plugin,
            "issues": issues,
            "valid": bool(available) and not absent_plugins,
        }

    # ------------------------------------------------------------------
    # 3. Timestamp alignment
    # ------------------------------------------------------------------

    def validate_timestamp_alignment(
        self, metrics: Sequence[str], node: str | int | None = None
    ) -> dict[str, Any]:
        """Report sampling intervals, overlap, and exact-match rates.

        Parameters
        ----------
        metrics:
            Two or more node-scoped metric names.
        node:
            Node on which to compare. ``None`` picks a node common to all.

        Returns
        -------
        dict
            Per-metric ``timing`` profiles, pairwise ``exact_match_ratio``
            and temporal ``overlap``, an ``exact_join_viable`` flag, and
            ``issues``.

        Raises
        ------
        ValidationError
            If fewer than two node-scoped metrics are given, or no shared
            node exists.

        Notes
        -----
        The exact-match ratio counts timestamps of the sparser series that
        appear bit-identically in the denser series
        (``EXACT_MATCH_TOLERANCE_S``). Any looser criterion is a tolerance
        join, which is preprocessing, and is deliberately not offered here.
        """
        metrics = list(metrics)
        scoped = [m for m in metrics if self._is_node_scoped(m)]
        if len(scoped) < 2:
            raise ValidationError(
                "Timestamp alignment needs at least two node-scoped "
                f"metrics; got {scoped}."
            )

        node_id = str(node) if node is not None else self._reference_node(scoped)
        if node_id is None:
            raise ValidationError(
                f"No node is common to all of {scoped}; cannot compare "
                f"timestamps on a shared node."
            )

        profiles: dict[str, Any] = {}
        stamps: dict[str, pd.Series] = {}
        for metric in scoped:
            if node_id not in set(self._nodes(metric)):
                raise ValidationError(
                    f"Node {node_id!r} is absent from metric {metric!r}."
                )
            profiles[metric] = self._timing_profile(metric, node_id)
            stamps[metric] = self.loader.load_metric_for_node(
                metric, node_id, columns=["timestamp"]
            )["timestamp"]

        pairs: list[dict[str, Any]] = []
        for i, left in enumerate(scoped):
            for right in scoped[i + 1:]:
                left_set = set(stamps[left])
                right_set = set(stamps[right])
                sparser, denser = (
                    (left, right)
                    if len(left_set) <= len(right_set)
                    else (right, left)
                )
                sparse_set = left_set if sparser == left else right_set
                dense_set = right_set if sparser == left else left_set
                shared = sparse_set & dense_set
                ratio = len(shared) / len(sparse_set) if sparse_set else 0.0

                lo = max(stamps[left].min(), stamps[right].min())
                hi = min(stamps[left].max(), stamps[right].max())
                overlap_s = max(0.0, (hi - lo).total_seconds())

                same_grid = (
                    profiles[left]["median_interval_s"]
                    == profiles[right]["median_interval_s"]
                )
                pairs.append(
                    {
                        "metric_a": left,
                        "metric_b": right,
                        "plugin_a": self._plugin_of(left),
                        "plugin_b": self._plugin_of(right),
                        "interval_a_s": profiles[left]["median_interval_s"],
                        "interval_b_s": profiles[right]["median_interval_s"],
                        "same_nominal_interval": same_grid,
                        "sparser_metric": sparser,
                        "n_sparser_timestamps": len(sparse_set),
                        "n_exact_matches": len(shared),
                        "exact_match_ratio": round(ratio, 5),
                        "exact_join_viable": bool(
                            ratio >= MIN_EXACT_MATCH_RATIO
                        ),
                        "overlap_start": str(lo),
                        "overlap_end": str(hi),
                        "overlap_s": overlap_s,
                        "overlap_h": round(overlap_s / 3600.0, 3),
                    }
                )

        issues: list[str] = []
        intervals = {
            m: p["median_interval_s"] for m, p in profiles.items()
        }
        if len(set(intervals.values())) > 1:
            issues.append(
                f"Metrics sample at different nominal intervals: {intervals}. "
                f"A common time base does not exist in the raw data."
            )
        for pair in pairs:
            if not pair["exact_join_viable"]:
                issues.append(
                    f"{pair['metric_a']} + {pair['metric_b']}: only "
                    f"{pair['exact_match_ratio']:.1%} of "
                    f"{pair['sparser_metric']} timestamps match exactly "
                    f"(threshold {MIN_EXACT_MATCH_RATIO:.0%}). Exact join "
                    f"not possible."
                )
            if pair["overlap_s"] <= 0:
                issues.append(
                    f"{pair['metric_a']} + {pair['metric_b']}: no temporal "
                    f"overlap."
                )

        return {
            "node": node_id,
            "metrics": scoped,
            "timing": profiles,
            "pairs": pairs,
            "all_same_interval": len(set(intervals.values())) == 1,
            "all_exact_join_viable": all(p["exact_join_viable"] for p in pairs),
            "compatible": all(p["exact_join_viable"] for p in pairs)
            and not issues,
            "issues": issues,
        }

    # ------------------------------------------------------------------
    # 4. Common nodes
    # ------------------------------------------------------------------

    def find_common_nodes(self, metrics: Sequence[str]) -> dict[str, Any]:
        """Report the node sets of several metrics and their intersection.

        Parameters
        ----------
        metrics:
            Metric names. Facility-scoped metrics are reported separately
            and excluded from the intersection.

        Returns
        -------
        dict
            ``common_nodes`` (sorted IDs), ``n_common``, ``per_metric``
            counts and ranges, ``union``, ``overlap_ratio`` against the
            smallest set, and ``issues``.

        Raises
        ------
        ValidationError
            If no node-scoped metric is supplied.
        """
        metrics = list(metrics)
        scoped = [m for m in metrics if self._is_node_scoped(m)]
        facility = [m for m in metrics if not self._is_node_scoped(m)]

        if not scoped:
            raise ValidationError(
                f"None of {metrics} are node-scoped; there are no nodes to "
                f"intersect."
            )

        per_metric: dict[str, dict[str, Any]] = {}
        sets: list[set[str]] = []
        for metric in scoped:
            nodes = self._nodes(metric)
            sets.append(set(nodes))
            per_metric[metric] = {
                "plugin": self._plugin_of(metric),
                "n_nodes": len(nodes),
                "min_id": nodes[0] if nodes else None,
                "max_id": nodes[-1] if nodes else None,
            }

        common = set.intersection(*sets) if sets else set()
        union = set().union(*sets) if sets else set()
        smallest = min(len(s) for s in sets) if sets else 0
        ratio = len(common) / smallest if smallest else 0.0

        for metric in scoped:
            missing = sets[scoped.index(metric)] - common
            per_metric[metric]["n_not_in_common"] = len(missing)

        issues: list[str] = []
        if not common:
            issues.append("No node is common to all supplied metrics.")
        if ratio < MIN_NODE_OVERLAP_RATIO:
            issues.append(
                f"Node overlap {ratio:.1%} is below the "
                f"{MIN_NODE_OVERLAP_RATIO:.0%} threshold."
            )
        plugins = {self._plugin_of(m) for m in scoped}
        if len(plugins) > 1:
            issues.append(
                f"Metrics span plugins {sorted(plugins)}. Node ID "
                f"namespaces are plugin-specific and a shared ID is not "
                f"proof of a shared physical machine."
            )
        if facility:
            issues.append(
                f"Facility-scoped metrics excluded from the intersection: "
                f"{facility}."
            )

        return {
            "metrics": scoped,
            "facility_metrics": facility,
            "common_nodes": self.loader._sort_node_ids(common),  # noqa: SLF001
            "n_common": len(common),
            "n_union": len(union),
            "smallest_set_size": smallest,
            "overlap_ratio": round(ratio, 5),
            "per_metric": per_metric,
            "plugins_involved": sorted(plugins),
            "issues": issues,
            "compatible": bool(common) and ratio >= MIN_NODE_OVERLAP_RATIO,
        }

    # ------------------------------------------------------------------
    # 5. Metric compatibility
    # ------------------------------------------------------------------

    def validate_metric_compatibility(
        self, metrics: Sequence[str], node: str | int | None = None
    ) -> dict[str, Any]:
        """Decide whether a set of metrics can safely coexist.

        Three independent axes are checked and reported separately:

        ``schema``
            All metrics carry ``timestamp`` and ``value``, and all are
            node-scoped (or all facility-scoped).
        ``identifier``
            The node ID namespaces intersect sufficiently.
        ``timestamp``
            The series share a time base at
            ``EXACT_MATCH_TOLERANCE_S``.

        Parameters
        ----------
        metrics:
            Two or more metric names.
        node:
            Node on which to compare timestamps.

        Returns
        -------
        dict
            ``compatible`` (bool), the three axis reports, ``blocking``
            issues, ``limitations``, and ``verdict``.

        Raises
        ------
        ValidationError
            If fewer than two metrics are supplied.
        """
        metrics = list(metrics)
        if len(metrics) < 2:
            raise ValidationError(
                "Compatibility requires at least two metrics."
            )

        blocking: list[str] = []
        limitations: list[str] = []

        # --- schema axis ------------------------------------------------
        per_metric = {m: self.validate_metric(m) for m in metrics}
        missing = [m for m, r in per_metric.items() if not r["exists"]]
        if missing:
            return {
                "metrics": metrics,
                "compatible": False,
                "verdict": "FAIL",
                "blocking": [f"Metrics not present in record: {missing}."],
                "limitations": [],
                "schema": {"compatible": False},
                "identifier": None,
                "timestamp": None,
            }

        scoped = [m for m in metrics if self._is_node_scoped(m)]
        facility = [m for m in metrics if not self._is_node_scoped(m)]
        schema_ok = True

        if scoped and facility:
            schema_ok = False
            blocking.append(
                f"Mixed scope: {scoped} are node-scoped while {facility} are "
                f"facility-scoped (no 'node' column). They share no join key."
            )
        for metric, report in per_metric.items():
            if not report["has_timestamp"]:
                schema_ok = False
                blocking.append(f"{metric} has no 'timestamp' column.")
            if "value" not in report["columns"]:
                schema_ok = False
                blocking.append(f"{metric} has no 'value' column.")

        dtypes = {m: r["value_dtype"] for m, r in per_metric.items()}
        if len(set(dtypes.values())) > 1:
            limitations.append(
                f"Mixed 'value' dtypes {dtypes}; stacking widens the column. "
                f"Container change only, no value is altered."
            )

        schema_report = {
            "compatible": schema_ok,
            "node_scoped": scoped,
            "facility_scoped": facility,
            "value_dtypes": dtypes,
            "columns": {m: r["columns"] for m, r in per_metric.items()},
        }

        # --- identifier axis -------------------------------------------
        identifier_report: dict[str, Any] | None = None
        if len(scoped) >= 2:
            identifier_report = self.find_common_nodes(scoped)
            if not identifier_report["compatible"]:
                blocking.extend(identifier_report["issues"])
            else:
                limitations.extend(identifier_report["issues"])

        # --- timestamp axis --------------------------------------------
        timestamp_report: dict[str, Any] | None = None
        if len(scoped) >= 2 and schema_ok:
            try:
                timestamp_report = self.validate_timestamp_alignment(
                    scoped, node=node
                )
                if not timestamp_report["compatible"]:
                    blocking.extend(timestamp_report["issues"])
            except ValidationError as exc:
                blocking.append(f"Timestamp comparison impossible: {exc}")

        compatible = not blocking
        return {
            "metrics": metrics,
            "compatible": compatible,
            "verdict": "PASS" if compatible else "FAIL",
            "schema": schema_report,
            "identifier": identifier_report,
            "timestamp": timestamp_report,
            "blocking": blocking,
            "limitations": limitations,
        }

    # ------------------------------------------------------------------
    # 6. GLASSCHIP mandatory input feasibility
    # ------------------------------------------------------------------

    def validate_glasschip_inputs(
        self,
        inputs: dict[str, str] | None = None,
        node: str | int | None = None,
    ) -> dict[str, Any]:
        """Decide whether the locked mandatory inputs can form one series.

        Parameters
        ----------
        inputs:
            Mapping of role to metric name. Defaults to
            :data:`GLASSCHIP_MANDATORY_INPUTS`.
        node:
            Node on which to test alignment.

        Returns
        -------
        dict
            ``verdict`` (``"PASS"`` or ``"FAIL"``), ``justification``,
            per-role reports, ``common_nodes``, ``sampling``,
            ``blocking_issues``, and ``scientific_limitations``.

        Notes
        -----
        A ``FAIL`` verdict means the mandatory inputs cannot be assembled
        into a model-ready series **from the raw record alone**. It does
        not mean the project is infeasible; it means an explicit,
        documented preprocessing decision is required first. Making that
        decision is outside this module's remit.
        """
        inputs = dict(inputs or GLASSCHIP_MANDATORY_INPUTS)
        metrics = list(inputs.values())

        blocking: list[str] = []
        limitations: list[str] = []

        # 1. Do the metrics exist at all?
        per_role: dict[str, Any] = {}
        for role, metric in inputs.items():
            report = self.validate_metric(metric)
            per_role[role] = report
            if not report["exists"]:
                blocking.append(
                    f"Mandatory input {role!r} -> metric {metric!r} is not "
                    f"present in the record."
                )

        if blocking:
            return {
                "verdict": "FAIL",
                "inputs": inputs,
                "per_role": per_role,
                "blocking_issues": blocking,
                "scientific_limitations": limitations,
                "justification": "One or more mandatory inputs are absent.",
            }

        # 2. Plugin spread
        plugins = {m: self._plugin_of(m) for m in metrics}
        multi_plugin = len(set(plugins.values())) > 1

        # 3. Node intersection
        node_report = self.find_common_nodes(metrics)
        if node_report["n_common"] == 0:
            blocking.append("No node carries all mandatory inputs.")

        # 4. Timestamp / sampling compatibility
        timestamp_report: dict[str, Any] | None = None
        try:
            timestamp_report = self.validate_timestamp_alignment(
                metrics, node=node
            )
        except ValidationError as exc:
            blocking.append(f"Alignment could not be assessed: {exc}")

        sampling: dict[str, float] = {}
        if timestamp_report:
            sampling = {
                m: p["median_interval_s"]
                for m, p in timestamp_report["timing"].items()
            }
            if not timestamp_report["all_same_interval"]:
                blocking.append(
                    f"Mandatory inputs sample at different intervals "
                    f"{sampling}. No common raw time base exists."
                )
            if not timestamp_report["all_exact_join_viable"]:
                blocking.append(
                    "Exact timestamp joins are not viable between all "
                    "mandatory inputs at "
                    f"{MIN_EXACT_MATCH_RATIO:.0%} match threshold."
                )

            # 5. Continuity of the shared window
            for metric, profile in timestamp_report["timing"].items():
                if profile.get("insufficient_samples"):
                    blocking.append(f"{metric} has too few samples to profile.")
                    continue
                if profile["longest_segment_s"] < MIN_CONTIGUOUS_SEGMENT_S:
                    blocking.append(
                        f"{metric}: longest contiguous run is "
                        f"{profile['longest_segment_h']:.2f} h, below the "
                        f"{MIN_CONTIGUOUS_SEGMENT_S / 3600:.0f} h needed for "
                        f"a transient fit."
                    )
                elif profile["is_sparse"]:
                    limitations.append(
                        f"{metric}: coverage {profile['coverage_ratio']:.1%} "
                        f"over {profile['span_days']:.2f} days; usable "
                        f"contiguous run "
                        f"{profile['longest_segment_h']:.2f} h."
                    )

        # 6. Standing scientific limitations of the source itself
        if multi_plugin:
            limitations.append(
                f"Inputs span plugins {sorted(set(plugins.values()))}. Node "
                f"IDs are plugin-local; cross-plugin identity is unproven."
            )
        if node_report["n_common"] < node_report["smallest_set_size"]:
            limitations.append(
                f"Only {node_report['n_common']} of "
                f"{node_report['smallest_set_size']} nodes carry every "
                f"mandatory input."
            )
        limitations.append(
            "Observational production telemetry: power is closed-loop under "
            "DVFS and governor control, so inputs are not independent and no "
            "causal claim is supported."
        )
        limitations.append(
            "No instrument characterisation is possible: sensor accuracy, "
            "calibration, and drift are unknown and unknowable from this "
            "record."
        )

        verdict = "FAIL" if blocking else "PASS"
        if verdict == "PASS":
            justification = (
                f"All {len(inputs)} mandatory inputs exist, share "
                f"{node_report['n_common']} nodes, and align on a common "
                f"time base."
            )
        else:
            justification = (
                f"{len(blocking)} blocking issue(s) prevent assembling the "
                f"mandatory inputs into a model-ready series from the raw "
                f"record. Resolution requires explicit preprocessing "
                f"decisions, which are out of scope for validation."
            )

        return {
            "verdict": verdict,
            "justification": justification,
            "inputs": inputs,
            "plugins": plugins,
            "per_role": per_role,
            "common_nodes": {
                "n_common": node_report["n_common"],
                "overlap_ratio": node_report["overlap_ratio"],
                "per_metric": node_report["per_metric"],
            },
            "sampling": sampling,
            "timestamp": timestamp_report,
            "blocking_issues": blocking,
            "scientific_limitations": limitations,
        }

    # ------------------------------------------------------------------
    # 7. Full report
    # ------------------------------------------------------------------

    def generate_validation_report(
        self,
        metrics: Sequence[str] | None = None,
        node: str | int | None = None,
    ) -> dict[str, Any]:
        """Assemble the complete validation report.

        Parameters
        ----------
        metrics:
            Metrics to assess. Defaults to the mandatory GLASSCHIP inputs.
        node:
            Node used for timing comparisons.

        Returns
        -------
        dict
            ``dataset``, ``metric_validation``, ``node_compatibility``,
            ``timestamp_compatibility``, ``metric_compatibility``,
            ``glasschip_inputs``, ``joinability``,
            ``scientific_limitations``, and ``observations``.

        Notes
        -----
        ``observations`` states what was measured. It contains no repair
        instructions; deciding what to do about a finding belongs to
        preprocessing.
        """
        metric_list = (
            list(metrics)
            if metrics is not None
            else list(GLASSCHIP_MANDATORY_INPUTS.values())
        )

        summary = self.loader.dataset_summary()
        per_metric = {m: self.validate_metric(m) for m in metric_list}

        try:
            node_report: dict[str, Any] | None = self.find_common_nodes(
                metric_list
            )
        except ValidationError as exc:
            node_report = {"error": str(exc)}

        try:
            timestamp_report: dict[str, Any] | None = (
                self.validate_timestamp_alignment(metric_list, node=node)
            )
        except ValidationError as exc:
            timestamp_report = {"error": str(exc)}

        try:
            compat_report: dict[str, Any] | None = (
                self.validate_metric_compatibility(metric_list, node=node)
            )
        except ValidationError as exc:
            compat_report = {"error": str(exc)}

        glasschip = self.validate_glasschip_inputs(node=node)

        # Joinability matrix: pairwise exact-join viability.
        joinability: dict[str, Any] = {}
        if timestamp_report and "pairs" in timestamp_report:
            for pair in timestamp_report["pairs"]:
                key = f"{pair['metric_a']}+{pair['metric_b']}"
                joinability[key] = {
                    "exact_join_viable": pair["exact_join_viable"],
                    "exact_match_ratio": pair["exact_match_ratio"],
                    "same_nominal_interval": pair["same_nominal_interval"],
                    "overlap_h": pair["overlap_h"],
                }

        observations: list[str] = []
        for metric, report in per_metric.items():
            observations.extend(f"{metric}: {issue}" for issue in report["issues"])
        if node_report and node_report.get("issues"):
            observations.extend(node_report["issues"])
        if timestamp_report and timestamp_report.get("issues"):
            observations.extend(timestamp_report["issues"])

        return {
            "dataset": {
                "root": summary["root"],
                "total_metrics": summary["total_metrics"],
                "total_files": summary["total_files"],
                "total_size_mb": summary["total_size_mb"],
                "timestamp_range": summary["timestamp_range"],
                "nodes_by_plugin": summary["nodes_by_plugin"],
                "node_namespaces_agree": summary["node_namespaces_agree"],
            },
            "metrics_assessed": metric_list,
            "metric_validation": per_metric,
            "node_compatibility": node_report,
            "timestamp_compatibility": timestamp_report,
            "metric_compatibility": compat_report,
            "glasschip_inputs": glasschip,
            "joinability": joinability,
            "scientific_limitations": glasschip["scientific_limitations"],
            "observations": observations,
            "verdict": glasschip["verdict"],
        }

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"{type(self).__name__}(loader={self.loader!r})"
