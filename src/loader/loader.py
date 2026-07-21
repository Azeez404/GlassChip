"""Dataset loader for the M100 ExaData telemetry record.

Single responsibility: RAW DATASET -> ACCESSIBLE DATA.

This module reads Parquet files and returns DataFrames. It does not clean,
normalise, resample, decode, impute, or otherwise transform values. Anything
that changes a number belongs in the preprocessing stage, not here.

On-disk layout expected::

    <dataset_path>/
        year_month=21-03/
            plugin=ipmi_pub/
                metric=p0_power/
                    a_0.parquet
            plugin=ganglia_pub/
                metric=cpu_user/
                    a_0.parquet
            ...

Schemas differ per plugin. Three shapes exist in the 21-03 record:

===============  ===========================================================
Plugin           Columns
===============  ===========================================================
``ipmi_pub``     timestamp, value (int32), node
``ganglia_pub``  timestamp, value (float32), node
``nagios_pub``   timestamp, value, description, host_group, nagiosdrained,
                 node, state_type
``schneider_pub``timestamp, value (int32), panel          -- NO node column
``logics_pub``   timestamp, value (float32), panel, device -- NO node column
===============  ===========================================================

``schneider_pub`` and ``logics_pub`` are facility-scoped (cooling plant,
electrical panels), not node-scoped. Node-based accessors skip them.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any, Iterable, Sequence

import pandas as pd
import pyarrow.compute as pc
import pyarrow.parquet as pq

__all__ = [
    "DatasetLoader",
    "DatasetLoaderError",
    "MetricNotFoundError",
    "NodeNotFoundError",
]

#: Plugins whose Parquet files carry a per-compute-node ``node`` column.
NODE_SCOPED_PLUGINS: frozenset[str] = frozenset(
    {"ipmi_pub", "ganglia_pub", "nagios_pub"}
)

#: Columns shared by every node-scoped plugin, used for long-format stacking.
_COMMON_NODE_COLUMNS: tuple[str, ...] = ("timestamp", "value", "node")


class DatasetLoaderError(Exception):
    """Base exception for all loader failures."""


class MetricNotFoundError(DatasetLoaderError, KeyError):
    """Raised when a requested metric does not exist in the dataset."""


class NodeNotFoundError(DatasetLoaderError, KeyError):
    """Raised when a requested node ID does not exist in the dataset."""


class DatasetLoader:
    """Read-only accessor for one M100 ExaData record.

    The loader indexes the directory tree on construction (a cheap path scan,
    no file reads) and thereafter resolves metric names to Parquet paths.

    Parameters
    ----------
    dataset_path:
        Path to a record directory. Either the record root (which contains a
        single ``year_month=*`` directory) or the ``year_month=*`` directory
        itself is accepted.

    Raises
    ------
    DatasetLoaderError
        If the path does not exist, is not a directory, or contains no
        ``plugin=*`` directories.

    Examples
    --------
    >>> loader = DatasetLoader("datasets/21-03")  # doctest: +SKIP
    >>> loader.load_metric_for_node("p0_power", "15")  # doctest: +SKIP
    """

    def __init__(self, dataset_path: str | Path) -> None:
        self.dataset_path: Path = Path(dataset_path).expanduser().resolve()
        self.root: Path = self._resolve_root(self.dataset_path)

        # metric name -> {"plugin": str, "path": Path, "files": list[Path]}
        self._index: dict[str, dict[str, Any]] = self._build_index(self.root)
        if not self._index:
            raise DatasetLoaderError(
                f"No 'metric=*' directories found under {self.root}"
            )

        # plugin -> {"node_ids": list[str], "source_metric": str}
        self._node_cache: dict[str, dict[str, Any]] | None = None

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_root(path: Path) -> Path:
        """Locate the directory that directly contains ``plugin=*`` folders.

        Accepts either the record root or the ``year_month=*`` level.
        """
        if not path.exists():
            raise DatasetLoaderError(f"Dataset path does not exist: {path}")
        if not path.is_dir():
            raise DatasetLoaderError(f"Dataset path is not a directory: {path}")

        if any(path.glob("plugin=*")):
            return path

        candidates = sorted(path.glob("year_month=*"))
        for candidate in candidates:
            if candidate.is_dir() and any(candidate.glob("plugin=*")):
                return candidate

        raise DatasetLoaderError(
            f"No 'plugin=*' directories found in {path} or its "
            f"'year_month=*' subdirectories"
        )

    @staticmethod
    def _build_index(root: Path) -> dict[str, dict[str, Any]]:
        """Map every metric name to its plugin, directory, and Parquet files.

        Metric names are unique across plugins in the M100 records, so the
        bare metric name is a sufficient lookup key. If a duplicate is ever
        encountered, a warning is emitted and the first occurrence wins.
        """
        index: dict[str, dict[str, Any]] = {}
        for plugin_dir in sorted(root.glob("plugin=*")):
            if not plugin_dir.is_dir():
                continue
            plugin = plugin_dir.name.split("=", 1)[1]
            for metric_dir in sorted(plugin_dir.glob("metric=*")):
                if not metric_dir.is_dir():
                    continue
                metric = metric_dir.name.split("=", 1)[1]
                if metric in index:
                    warnings.warn(
                        f"Duplicate metric name {metric!r} in plugin "
                        f"{plugin!r}; keeping "
                        f"{index[metric]['plugin']!r}.",
                        stacklevel=2,
                    )
                    continue
                index[metric] = {
                    "plugin": plugin,
                    "path": metric_dir,
                    "files": sorted(metric_dir.glob("*.parquet")),
                }
        return index

    # ------------------------------------------------------------------
    # Internal lookups
    # ------------------------------------------------------------------

    def _entry(self, metric: str) -> dict[str, Any]:
        """Return the index entry for ``metric`` or raise."""
        try:
            return self._index[metric]
        except KeyError:
            raise MetricNotFoundError(
                f"Unknown metric {metric!r}. "
                f"{len(self._index)} metrics available; "
                f"call get_available_metrics() to list them."
            ) from None

    @staticmethod
    def _normalise_nodes(nodes: str | int | Iterable[str | int]) -> list[str]:
        """Coerce node identifiers to the string form used on disk."""
        if isinstance(nodes, (str, int)):
            nodes = [nodes]
        return [str(node) for node in nodes]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_parquet(
        self,
        path: str | Path,
        columns: Sequence[str] | None = None,
        filters: list[Any] | None = None,
    ) -> pd.DataFrame:
        """Read a Parquet file or directory into a DataFrame.

        Parameters
        ----------
        path:
            Parquet file, or a directory of Parquet files.
        columns:
            Column subset to read. ``None`` reads all columns.
        filters:
            PyArrow predicate pushdown filters, e.g.
            ``[("node", "in", ["15"])]``. Applied during the read so that
            non-matching row groups are never materialised.

        Returns
        -------
        pandas.DataFrame
            Rows exactly as stored. No values are altered.

        Raises
        ------
        DatasetLoaderError
            If the path is missing or the file cannot be read.
        """
        target = Path(path)
        if not target.exists():
            raise DatasetLoaderError(f"Parquet path does not exist: {target}")
        try:
            table = pq.read_table(
                target,
                columns=list(columns) if columns is not None else None,
                filters=filters,
            )
        except Exception as exc:  # pragma: no cover - surfaced to caller
            raise DatasetLoaderError(
                f"Failed to read Parquet at {target}: {exc}"
            ) from exc
        return table.to_pandas()

    def load_metric(
        self,
        metric: str,
        nodes: str | int | Iterable[str | int] | None = None,
        columns: Sequence[str] | None = None,
    ) -> pd.DataFrame:
        """Load one telemetry metric across the record.

        Parameters
        ----------
        metric:
            Metric name, e.g. ``"p0_power"``, ``"ambient"``, ``"cpu_user"``,
            ``"fan0_0"``, ``"total_power"``.
        nodes:
            Optional node ID or iterable of node IDs. When given, the filter
            is pushed into the Parquet reader rather than applied afterwards,
            so memory stays proportional to the result, not the file. Only
            valid for node-scoped plugins.
        columns:
            Optional column subset.

        Returns
        -------
        pandas.DataFrame
            Schema depends on the owning plugin; see the module docstring.

        Raises
        ------
        MetricNotFoundError
            If the metric does not exist.
        DatasetLoaderError
            If ``nodes`` is given for a metric that has no ``node`` column,
            or if no Parquet files are present for the metric.

        Notes
        -----
        Some metrics are large. ``p0_power`` holds roughly 10.7 million rows
        for a single month. Prefer ``nodes=`` or ``columns=`` over loading in
        full and slicing afterwards.
        """
        entry = self._entry(metric)
        if not entry["files"]:
            raise DatasetLoaderError(
                f"No Parquet files found for metric {metric!r} at "
                f"{entry['path']}"
            )

        filters: list[Any] | None = None
        if nodes is not None:
            if entry["plugin"] not in NODE_SCOPED_PLUGINS:
                raise DatasetLoaderError(
                    f"Metric {metric!r} belongs to plugin "
                    f"{entry['plugin']!r}, which is facility-scoped and has "
                    f"no 'node' column. Node filtering is not applicable."
                )
            filters = [("node", "in", self._normalise_nodes(nodes))]

        return self.load_parquet(
            entry["path"], columns=columns, filters=filters
        )

    def load_metric_for_node(
        self,
        metric: str,
        node: str | int,
        columns: Sequence[str] | None = None,
    ) -> pd.DataFrame:
        """Load a single metric for a single node.

        Parameters
        ----------
        metric:
            Metric name, e.g. ``"p0_power"``.
        node:
            Node identifier. Accepts ``"15"`` or ``15``.
        columns:
            Optional column subset. Defaults to the full plugin schema,
            which for ipmi/ganglia is ``timestamp``, ``value``, ``node``.

        Returns
        -------
        pandas.DataFrame
            Rows for that node only, in file order.

        Raises
        ------
        MetricNotFoundError
            If the metric does not exist.
        NodeNotFoundError
            If the metric contains no rows for that node.
        """
        node_id = str(node)
        frame = self.load_metric(metric, nodes=node_id, columns=columns)
        if frame.empty:
            raise NodeNotFoundError(
                f"No rows for node {node_id!r} in metric {metric!r}."
            )
        return frame

    def load_node(
        self,
        node: str | int,
        metrics: Iterable[str] | None = None,
        plugins: Iterable[str] | None = None,
    ) -> pd.DataFrame:
        """Load every record belonging to one node, in long format.

        Parameters
        ----------
        node:
            Node identifier.
        metrics:
            Optional metric subset. ``None`` loads every node-scoped metric,
            which reads on the order of 500 MB for a single month; a warning
            is emitted in that case.
        plugins:
            Optional plugin subset, e.g. ``["ipmi_pub"]``. Ignored for
            metrics given explicitly.

        Returns
        -------
        pandas.DataFrame
            Long format with columns ``timestamp``, ``value``, ``node``,
            ``metric``, ``plugin``, sorted by metric then timestamp.

        Raises
        ------
        NodeNotFoundError
            If no rows exist for the node in any selected metric.
        DatasetLoaderError
            If an explicitly requested metric is facility-scoped.

        Notes
        -----
        Long format keeps only the columns common to all node-scoped
        plugins. ``nagios_pub`` carries extra columns (``description``,
        ``host_group``, ``state_type``, ``nagiosdrained``) that are not
        present here; use :meth:`load_metric` to read them.

        Because ``ipmi_pub`` stores ``value`` as ``int32`` and
        ``ganglia_pub`` as ``float32``, stacking them widens the column to
        ``float64``. This is a container change only; no value is altered.
        """
        node_id = str(node)

        if metrics is None:
            allowed = (
                NODE_SCOPED_PLUGINS
                if plugins is None
                else NODE_SCOPED_PLUGINS & set(plugins)
            )
            selected = [
                name
                for name, entry in self._index.items()
                if entry["plugin"] in allowed
            ]
            warnings.warn(
                f"load_node({node_id!r}) with metrics=None will read "
                f"{len(selected)} metrics. Pass metrics= or plugins= to "
                f"limit the read.",
                stacklevel=2,
            )
        else:
            selected = list(metrics)
            for name in selected:
                entry = self._entry(name)
                if entry["plugin"] not in NODE_SCOPED_PLUGINS:
                    raise DatasetLoaderError(
                        f"Metric {name!r} belongs to facility-scoped plugin "
                        f"{entry['plugin']!r} and has no 'node' column."
                    )

        frames: list[pd.DataFrame] = []
        for name in sorted(selected):
            entry = self._index[name]
            frame = self.load_metric(
                name, nodes=node_id, columns=_COMMON_NODE_COLUMNS
            )
            if frame.empty:
                continue
            frame["metric"] = name
            frame["plugin"] = entry["plugin"]
            frames.append(frame)

        if not frames:
            raise NodeNotFoundError(
                f"No rows for node {node_id!r} across "
                f"{len(selected)} metric(s)."
            )

        return pd.concat(frames, ignore_index=True).sort_values(
            ["metric", "timestamp"], ignore_index=True
        )

    def get_available_metrics(
        self, plugin: str | None = None
    ) -> list[str]:
        """List every telemetry metric present in the record.

        Parameters
        ----------
        plugin:
            Optional plugin filter, e.g. ``"ipmi_pub"``.

        Returns
        -------
        list of str
            Sorted metric names.

        Raises
        ------
        DatasetLoaderError
            If ``plugin`` is not present in the record.
        """
        if plugin is None:
            return sorted(self._index)

        known = self.get_available_plugins()
        if plugin not in known:
            raise DatasetLoaderError(
                f"Unknown plugin {plugin!r}. Available: {known}"
            )
        return sorted(
            name
            for name, entry in self._index.items()
            if entry["plugin"] == plugin
        )

    def get_available_plugins(self) -> list[str]:
        """List every plugin present in the record.

        Returns
        -------
        list of str
            Sorted plugin names.
        """
        return sorted({entry["plugin"] for entry in self._index.values()})

    def nodes_for_metric(self, metric: str) -> list[str]:
        """Return the exact set of node IDs present in one metric.

        Parameters
        ----------
        metric:
            Metric name.

        Returns
        -------
        list of str
            Sorted node IDs, numerically where the IDs are digits.

        Raises
        ------
        MetricNotFoundError
            If the metric does not exist.
        DatasetLoaderError
            If the metric is facility-scoped and has no ``node`` column.

        Notes
        -----
        Node coverage is not uniform. Within ``ipmi_pub``, ``p0_power``
        reports 980 nodes while ``ambient`` reports 979. Use this method
        when an exact per-metric answer matters.
        """
        entry = self._entry(metric)
        if entry["plugin"] not in NODE_SCOPED_PLUGINS:
            raise DatasetLoaderError(
                f"Metric {metric!r} belongs to facility-scoped plugin "
                f"{entry['plugin']!r} and has no 'node' column."
            )
        table = pq.read_table(entry["path"], columns=["node"])
        values = [v for v in pc.unique(table["node"]).to_pylist() if v is not None]
        return self._sort_node_ids(values)

    def get_available_nodes(
        self, plugin: str | None = None, refresh: bool = False
    ) -> dict[str, Any]:
        """Return the node inventory for the record.

        Parameters
        ----------
        plugin:
            Restrict the report to one node-scoped plugin. ``None``
            reports every node-scoped plugin plus their union and
            intersection.
        refresh:
            Re-scan even if a cached result exists.

        Returns
        -------
        dict
            ``total_nodes`` (size of the union), ``node_ids`` (the union),
            ``common_node_ids`` (intersection across node-scoped plugins),
            ``total_common_nodes``, ``namespaces_agree``, ``min_id``,
            ``max_id``, ``is_contiguous``, ``dtype``, and ``by_plugin``
            with per-plugin counts, ranges, and the metric each set was
            sampled from.

        Raises
        ------
        DatasetLoaderError
            If no node-scoped metric can be read, or ``plugin`` is not a
            node-scoped plugin present in the record.

        Warns
        -----
        UserWarning
            If the plugins disagree on the node ID namespace.

        Notes
        -----
        Node ID namespaces are **plugin-specific and not interchangeable**.
        In the ``21-03`` record ``ipmi_pub`` spans 0-979, ``ganglia_pub``
        spans 3-987, and ``nagios_pub`` spans 0-1162. Their intersection is
        smaller than any individual set. Treat ``node`` as a plugin-local
        label unless a cross-plugin mapping has been established
        independently.

        Each plugin's set is sampled from its largest metric file, which
        gives the widest coverage for that plugin. For an exact per-metric
        answer use :meth:`nodes_for_metric`.
        """
        if self._node_cache is None or refresh:
            self._node_cache = self._discover_nodes()

        cache = self._node_cache

        if plugin is not None:
            if plugin not in cache:
                raise DatasetLoaderError(
                    f"{plugin!r} is not a node-scoped plugin in this record. "
                    f"Available: {sorted(cache)}"
                )
            selected = {plugin: cache[plugin]}
        else:
            selected = cache

        sets = [set(info["node_ids"]) for info in selected.values()]
        union = self._sort_node_ids(set().union(*sets)) if sets else []
        common = self._sort_node_ids(set.intersection(*sets)) if sets else []
        agree = len(sets) <= 1 or all(s == sets[0] for s in sets)

        if plugin is None and not agree:
            warnings.warn(
                "Node ID namespaces differ across plugins "
                f"({ {p: len(i['node_ids']) for p, i in selected.items()} }). "
                "A 'node' value is only meaningful within its own plugin "
                "unless a cross-plugin mapping has been verified.",
                stacklevel=2,
            )

        as_int = [int(n) for n in union if n.isdigit()]
        contiguous = (
            len(as_int) == len(union)
            and bool(as_int)
            and as_int == list(range(as_int[0], as_int[-1] + 1))
        )

        return {
            "total_nodes": len(union),
            "node_ids": union,
            "total_common_nodes": len(common),
            "common_node_ids": common,
            "namespaces_agree": agree,
            "min_id": union[0] if union else None,
            "max_id": union[-1] if union else None,
            "is_contiguous": contiguous,
            "dtype": "string",
            "by_plugin": {
                name: {
                    "total_nodes": len(info["node_ids"]),
                    "min_id": info["node_ids"][0] if info["node_ids"] else None,
                    "max_id": info["node_ids"][-1] if info["node_ids"] else None,
                    "source_metric": info["source_metric"],
                }
                for name, info in selected.items()
            },
        }

    def _discover_nodes(self) -> dict[str, dict[str, Any]]:
        """Sample node IDs from the largest metric of each node-scoped plugin.

        The largest file is used because it gives the widest node coverage
        for that plugin, and because node coverage is not uniform across
        metrics within a plugin.
        """
        by_plugin: dict[str, list[tuple[int, str]]] = {}
        for name, entry in self._index.items():
            if entry["plugin"] not in NODE_SCOPED_PLUGINS or not entry["files"]:
                continue
            size = sum(f.stat().st_size for f in entry["files"])
            by_plugin.setdefault(entry["plugin"], []).append((size, name))

        if not by_plugin:
            raise DatasetLoaderError(
                "No node-scoped metrics found; cannot enumerate nodes."
            )

        discovered: dict[str, dict[str, Any]] = {}
        errors: dict[str, str] = {}

        for plugin, candidates in by_plugin.items():
            # Largest first: widest coverage, and a fallback chain if a
            # file is unreadable.
            for _, name in sorted(candidates, reverse=True):
                try:
                    table = pq.read_table(
                        self._index[name]["path"], columns=["node"]
                    )
                except Exception as exc:  # pragma: no cover - try next
                    errors[plugin] = str(exc)
                    continue
                values = [
                    v
                    for v in pc.unique(table["node"]).to_pylist()
                    if v is not None
                ]
                if not values:
                    continue
                discovered[plugin] = {
                    "node_ids": self._sort_node_ids(values),
                    "source_metric": name,
                }
                break

        if not discovered:
            raise DatasetLoaderError(
                f"Could not enumerate nodes from any node-scoped metric. "
                f"Errors: {errors}"
            )
        return discovered

    @staticmethod
    def _sort_node_ids(values: Iterable[str]) -> list[str]:
        """Sort node IDs numerically when they are digits, else lexically."""
        return sorted(
            set(values),
            key=lambda v: (not v.isdigit(), int(v) if v.isdigit() else v),
        )

    def dataset_summary(self, sample_timestamps: bool = True) -> dict[str, Any]:
        """Summarise the record without loading any values.

        Parameters
        ----------
        sample_timestamps:
            Read Parquet footer statistics to report the observed timestamp
            range. Metadata only; no row data is materialised.

        Returns
        -------
        dict
            ``dataset_path``, ``root``, ``total_files``, ``total_bytes``,
            ``total_size_mb``, ``total_metrics``, ``total_nodes``,
            ``plugins`` (per-plugin file/metric/byte counts and schema),
            ``metrics_by_plugin``, and ``timestamp_range``.
        """
        plugins: dict[str, dict[str, Any]] = {}
        total_files = 0
        total_bytes = 0

        for name, entry in self._index.items():
            plugin = entry["plugin"]
            info = plugins.setdefault(
                plugin,
                {
                    "metrics": 0,
                    "files": 0,
                    "bytes": 0,
                    "node_scoped": plugin in NODE_SCOPED_PLUGINS,
                    "columns": None,
                    "dtypes": None,
                },
            )
            info["metrics"] += 1
            for file in entry["files"]:
                size = file.stat().st_size
                info["files"] += 1
                info["bytes"] += size
                total_files += 1
                total_bytes += size

            if info["columns"] is None and entry["files"]:
                try:
                    schema = pq.ParquetFile(entry["files"][0]).schema_arrow
                    info["columns"] = list(schema.names)
                    info["dtypes"] = {
                        field.name: str(field.type) for field in schema
                    }
                except Exception:  # pragma: no cover - schema is advisory
                    pass

        for info in plugins.values():
            info["size_mb"] = round(info["bytes"] / 1e6, 2)

        # The namespace warning belongs to get_available_nodes(); the
        # summary already reports the per-plugin breakdown explicitly.
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                nodes = self.get_available_nodes()
            total_nodes = nodes["total_nodes"]
            nodes_by_plugin = {
                name: info["total_nodes"]
                for name, info in nodes["by_plugin"].items()
            }
            common_nodes = nodes["total_common_nodes"]
            namespaces_agree = nodes["namespaces_agree"]
        except DatasetLoaderError:
            total_nodes = None
            nodes_by_plugin = {}
            common_nodes = None
            namespaces_agree = None

        summary: dict[str, Any] = {
            "dataset_path": str(self.dataset_path),
            "root": str(self.root),
            "total_files": total_files,
            "total_bytes": total_bytes,
            "total_size_mb": round(total_bytes / 1e6, 2),
            "total_metrics": len(self._index),
            "total_nodes": total_nodes,
            "nodes_by_plugin": nodes_by_plugin,
            "total_common_nodes": common_nodes,
            "node_namespaces_agree": namespaces_agree,
            "plugins": plugins,
            "metrics_by_plugin": {
                plugin: self.get_available_metrics(plugin)
                for plugin in self.get_available_plugins()
            },
            "timestamp_range": None,
        }

        if sample_timestamps:
            summary["timestamp_range"] = self._timestamp_range()

        return summary

    def _timestamp_range(self) -> dict[str, Any] | None:
        """Read min/max timestamp from Parquet column statistics.

        Uses the largest node-scoped metric, which has the densest time
        coverage. The metric used is reported so the figure is traceable.
        """
        ordered = sorted(
            (
                (sum(f.stat().st_size for f in entry["files"]), name, entry)
                for name, entry in self._index.items()
                if entry["plugin"] in NODE_SCOPED_PLUGINS and entry["files"]
            ),
            reverse=True,
        )
        for _, name, entry in ordered:
            try:
                parquet_file = pq.ParquetFile(entry["files"][0])
                schema = parquet_file.schema_arrow
                if "timestamp" not in schema.names:
                    continue
                column = schema.names.index("timestamp")
                lows, highs = [], []
                for group in range(parquet_file.metadata.num_row_groups):
                    stats = parquet_file.metadata.row_group(group).column(
                        column
                    ).statistics
                    if stats is not None and stats.has_min_max:
                        lows.append(stats.min)
                        highs.append(stats.max)
                if lows and highs:
                    return {
                        "min": str(min(lows)),
                        "max": str(max(highs)),
                        "source_metric": name,
                        "dtype": str(schema.field("timestamp").type),
                    }
            except Exception:  # pragma: no cover - advisory only
                continue
        return None

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(root={str(self.root)!r}, "
            f"metrics={len(self._index)}, "
            f"plugins={len(self.get_available_plugins())})"
        )

    def __contains__(self, metric: object) -> bool:
        return metric in self._index

    def __len__(self) -> int:
        return len(self._index)
