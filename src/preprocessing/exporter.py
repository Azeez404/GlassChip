"""Export model-ready GLASSCHIP-V1 time series to disk.

Writes what it is given, unchanged. No filtering, rounding, resampling, or
column derivation happens here.

Two formats:

``parquet``
    Preferred. Preserves dtypes and timezone-aware timestamps exactly.
``csv``
    Portable. Timestamps are written in ISO-8601 with UTC offset so they
    survive a round trip; numeric precision is left to pandas defaults.

Files are named ``Node_<id>.<ext>``, e.g. ``Node_15.parquet``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

__all__ = ["Exporter", "ExportError", "SUPPORTED_FORMATS"]

#: Formats this module can write.
SUPPORTED_FORMATS: frozenset[str] = frozenset({"parquet", "csv"})


class ExportError(Exception):
    """Raised when an export cannot be completed."""


class Exporter:
    """Write per-node time series to a directory.

    Parameters
    ----------
    output_dir:
        Destination directory. Created if absent.
    overwrite:
        Permit replacing existing files. When ``False`` an existing target
        raises rather than being silently clobbered.

    Raises
    ------
    ExportError
        If the directory cannot be created.

    Examples
    --------
    >>> exporter = Exporter("data/processed")          # doctest: +SKIP
    >>> exporter.export_node(frame, "15")              # doctest: +SKIP
    """

    def __init__(
        self, output_dir: str | Path, overwrite: bool = False
    ) -> None:
        self.output_dir = Path(output_dir).expanduser().resolve()
        self.overwrite = overwrite
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ExportError(
                f"Could not create output directory {self.output_dir}: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _target(self, node: str | int, fmt: str) -> Path:
        """Resolve and guard the destination path."""
        if fmt not in SUPPORTED_FORMATS:
            raise ExportError(
                f"Unsupported format {fmt!r}. "
                f"Supported: {sorted(SUPPORTED_FORMATS)}."
            )
        path = self.output_dir / f"Node_{node}.{fmt}"
        if path.exists() and not self.overwrite:
            raise ExportError(
                f"{path} already exists. Pass overwrite=True to replace it."
            )
        return path

    @staticmethod
    def _check(frame: pd.DataFrame) -> None:
        """Reject an empty or malformed frame before writing."""
        if not isinstance(frame, pd.DataFrame):
            raise ExportError(f"Expected a DataFrame, got {type(frame)!r}.")
        if frame.empty:
            raise ExportError("Refusing to export an empty frame.")

    # ------------------------------------------------------------------
    # Single format
    # ------------------------------------------------------------------

    def export_parquet(
        self,
        frame: pd.DataFrame,
        node: str | int,
        compression: str = "snappy",
    ) -> Path:
        """Write one node's series to Parquet.

        Parameters
        ----------
        frame:
            Model-ready frame.
        node:
            Node identifier, used for the filename.
        compression:
            Parquet codec.

        Returns
        -------
        pathlib.Path
            The written file.

        Raises
        ------
        ExportError
            If the frame is empty or the write fails.
        """
        self._check(frame)
        path = self._target(node, "parquet")
        try:
            frame.to_parquet(path, index=False, compression=compression)
        except Exception as exc:
            raise ExportError(f"Parquet write failed for {path}: {exc}") from exc
        return path

    def export_csv(
        self, frame: pd.DataFrame, node: str | int
    ) -> Path:
        """Write one node's series to CSV.

        Parameters
        ----------
        frame:
            Model-ready frame.
        node:
            Node identifier, used for the filename.

        Returns
        -------
        pathlib.Path
            The written file.

        Raises
        ------
        ExportError
            If the frame is empty or the write fails.

        Notes
        -----
        Timestamps are written ISO-8601 with UTC offset. CSV carries no
        dtype information, so Parquet is preferred where round-tripping
        matters.
        """
        self._check(frame)
        path = self._target(node, "csv")
        try:
            frame.to_csv(path, index=False, date_format="%Y-%m-%dT%H:%M:%S%z")
        except Exception as exc:
            raise ExportError(f"CSV write failed for {path}: {exc}") from exc
        return path

    # ------------------------------------------------------------------
    # Combined
    # ------------------------------------------------------------------

    def export_node(
        self,
        frame: pd.DataFrame,
        node: str | int,
        formats: tuple[str, ...] = ("parquet",),
        report: Mapping[str, Any] | None = None,
    ) -> dict[str, Path]:
        """Write one node in one or more formats, optionally with a report.

        Parameters
        ----------
        frame:
            Model-ready frame.
        node:
            Node identifier.
        formats:
            Any of ``"parquet"``, ``"csv"``.
        report:
            Construction report to write alongside as
            ``Node_<id>_report.json``. Provenance, not data.

        Returns
        -------
        dict
            Format name to written path, plus ``"report"`` if written.

        Raises
        ------
        ExportError
            On an unsupported format or a failed write.
        """
        written: dict[str, Path] = {}
        for fmt in formats:
            if fmt == "parquet":
                written["parquet"] = self.export_parquet(frame, node)
            elif fmt == "csv":
                written["csv"] = self.export_csv(frame, node)
            else:
                raise ExportError(
                    f"Unsupported format {fmt!r}. "
                    f"Supported: {sorted(SUPPORTED_FORMATS)}."
                )

        if report is not None:
            path = self.output_dir / f"Node_{node}_report.json"
            if path.exists() and not self.overwrite:
                raise ExportError(
                    f"{path} already exists. Pass overwrite=True to replace it."
                )
            try:
                path.write_text(
                    json.dumps(report, indent=2, default=str), encoding="utf-8"
                )
            except OSError as exc:
                raise ExportError(
                    f"Report write failed for {path}: {exc}"
                ) from exc
            written["report"] = path

        return written

    def export_many(
        self,
        frames: Mapping[str, pd.DataFrame],
        formats: tuple[str, ...] = ("parquet",),
    ) -> dict[str, dict[str, Path]]:
        """Write several nodes.

        Parameters
        ----------
        frames:
            Node ID to model-ready frame.
        formats:
            Formats to write for each node.

        Returns
        -------
        dict
            Node ID to the mapping returned by :meth:`export_node`.

        Raises
        ------
        ExportError
            On the first failure. Files already written are kept.
        """
        return {
            node: self.export_node(frame, node, formats)
            for node, frame in frames.items()
        }

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(output_dir={str(self.output_dir)!r}, "
            f"overwrite={self.overwrite})"
        )
