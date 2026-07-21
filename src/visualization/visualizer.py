"""Thermal behaviour visualisation for GLASSCHIP-V1.

Answers one question: **what does the data look like?**

It never answers *why*. No physical law, equation, mechanism, or parameter
is named anywhere in this module's output. Observations are descriptive
statements about the plotted series and nothing more.

Scope is the GLASSCHIP-V1 prototype triple on a single node:
``temperature``, ``power``, ``fan_speed``.

Segment handling
----------------
Record ``21-03`` contains two temporal segments separated by a 27-day gap.
**They are never drawn as one continuous line.** Every time-axis plot
splits into one panel per segment, sized and labelled independently. Drawing
a line across the gap would imply data that does not exist.

Backend
-------
Defaults to the non-interactive ``Agg`` backend so plots render headless on
any platform. Figures are returned as well as saved, so a caller in a
notebook may display them directly.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.gridspec as gridspec  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from preprocessing.timeseries_builder import (  # noqa: E402
    TimeSeriesBuilder,
    TimeSeriesError,
)

__all__ = [
    "ThermalVisualizer",
    "VisualizationError",
    "DEFAULT_NODE",
    "ROLE_LABELS",
    "ROLE_COLOURS",
    "NEAR_CONSTANT_STD",
    "LOW_CARDINALITY_THRESHOLD",
]

#: The prototype is single-node first. This is the locked default.
DEFAULT_NODE: str = "15"

#: Axis labels with units.
ROLE_LABELS: dict[str, str] = {
    "temperature": "Temperature (degC)",
    "power": "Power (W)",
    "fan_speed": "Fan speed (RPM)",
}

#: Consistent colour per role across every figure.
ROLE_COLOURS: dict[str, str] = {
    "temperature": "#c1440e",
    "power": "#1f4e79",
    "fan_speed": "#2e7d32",
}

#: A series whose standard deviation is below this is reported as
#: near-constant. Descriptive flag only.
NEAR_CONSTANT_STD: float = 1.0

#: A series with fewer distinct values than this is reported as
#: low-cardinality. Descriptive flag only.
LOW_CARDINALITY_THRESHOLD: int = 5

#: Minimum absolute correlation before a lag statement is worth making.
#: Below this the peak lag is indistinguishable from noise and reporting
#: "changes appear later" would manufacture a temporal claim from scatter.
#: The lag is still returned numerically; only the prose is withheld.
MIN_REPORTABLE_CORRELATION: float = 0.2

#: Interval above this multiple of the median counts as a segment break.
GAP_MULTIPLIER: float = 3.0


class VisualizationError(Exception):
    """Raised when a visualisation cannot be produced."""


class ThermalVisualizer:
    """Plot thermal behaviour for one node.

    Parameters
    ----------
    source:
        A :class:`~timeseries_builder.TimeSeriesBuilder` or a dataset path.
    output_dir:
        Directory for saved figures. Created on demand.
    dpi:
        Figure resolution.

    Raises
    ------
    VisualizationError
        If the dataset cannot be opened.

    Examples
    --------
    >>> viz = ThermalVisualizer("datasets/21-03")   # doctest: +SKIP
    >>> viz.plot_thermal_behaviour()                # doctest: +SKIP
    """

    def __init__(
        self,
        source: TimeSeriesBuilder | str,
        output_dir: str | Path = "visualizations",
        dpi: int = 120,
    ) -> None:
        try:
            self.builder = (
                source
                if isinstance(source, TimeSeriesBuilder)
                else TimeSeriesBuilder(source)
            )
        except Exception as exc:
            raise VisualizationError(f"Could not open dataset: {exc}") from exc

        self.output_dir = Path(output_dir).expanduser().resolve()
        self.dpi = dpi
        self._cache: dict[str, tuple[pd.DataFrame, dict[str, Any]]] = {}

    # ------------------------------------------------------------------
    # Data access
    # ------------------------------------------------------------------

    def _frame(
        self, node: str | int = DEFAULT_NODE
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Return the cached model-ready frame and report for a node."""
        node_id = str(node)
        if node_id not in self._cache:
            try:
                self._cache[node_id] = self.builder.construct_node_dataframe(
                    node_id
                )
            except TimeSeriesError as exc:
                raise VisualizationError(
                    f"Could not build series for node {node_id!r}: {exc}"
                ) from exc
        return self._cache[node_id]

    @staticmethod
    def _split_segments(frame: pd.DataFrame) -> list[pd.DataFrame]:
        """Split a frame at gaps. Returns views, nothing is inserted.

        A gap is an interval exceeding :data:`GAP_MULTIPLIER` times the
        median. Segments are returned in chronological order.
        """
        if len(frame) < 2:
            return [frame]

        deltas = frame["timestamp"].diff().dt.total_seconds()
        median = float(deltas.dropna().median())
        breaks = list(
            frame.index[deltas > median * GAP_MULTIPLIER]
        )

        bounds = [0] + breaks + [len(frame)]
        segments = [
            frame.iloc[bounds[i]:bounds[i + 1]]
            for i in range(len(bounds) - 1)
        ]
        return [s for s in segments if len(s)]

    def _save(self, fig: plt.Figure, name: str) -> Path:
        """Write a figure and return its path."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / name
        try:
            fig.savefig(path, dpi=self.dpi, bbox_inches="tight")
        except OSError as exc:
            raise VisualizationError(
                f"Could not save figure to {path}: {exc}"
            ) from exc
        return path

    # ------------------------------------------------------------------
    # Segment-aware axes
    # ------------------------------------------------------------------

    def _segment_axes(
        self,
        fig: plt.Figure,
        segments: Sequence[pd.DataFrame],
        n_rows: int = 1,
    ) -> np.ndarray:
        """Build one axes column per segment, width-scaled by duration.

        Widths use the square root of duration so a short segment stays
        visible next to a long one. A break marker is drawn between
        columns to make the discontinuity explicit.

        Returns
        -------
        numpy.ndarray
            Axes of shape ``(n_rows, len(segments))``.
        """
        durations = [
            max(
                (s["timestamp"].iloc[-1] - s["timestamp"].iloc[0]).total_seconds(),
                1.0,
            )
            for s in segments
        ]
        widths = np.sqrt(durations)
        widths = widths / widths.sum()

        spec = gridspec.GridSpec(
            n_rows,
            len(segments),
            figure=fig,
            width_ratios=widths,
            wspace=0.08,
            hspace=0.18,
        )
        axes = np.empty((n_rows, len(segments)), dtype=object)
        for row in range(n_rows):
            for col in range(len(segments)):
                axes[row, col] = fig.add_subplot(spec[row, col])
        return axes

    @staticmethod
    def _mark_break(axis: plt.Axes, side: str) -> None:
        """Hide the spine facing a discontinuity and draw a break hatch."""
        if side == "right":
            axis.spines["right"].set_visible(False)
            axis.tick_params(labelright=False, right=False)
        else:
            axis.spines["left"].set_visible(False)
            axis.tick_params(labelleft=False, left=False)

    @staticmethod
    def _format_time_axis(
        axis: plt.Axes, segment: pd.DataFrame, narrow: bool = False
    ) -> None:
        """Label a time axis with hours elapsed within its own segment.

        Narrow panels get few ticks, otherwise labels collide and become
        unreadable on a short segment sitting beside a long one.
        """
        start = segment["timestamp"].iloc[0]
        hours = (segment["timestamp"] - start).dt.total_seconds() / 3600.0
        axis.set_xlim(hours.min(), max(hours.max(), hours.min() + 0.01))
        axis.set_xlabel("Hours from segment start", fontsize=8 if narrow else 10)
        if narrow:
            axis.xaxis.set_major_locator(plt.MaxNLocator(2))
            axis.tick_params(axis="x", labelsize=7, rotation=45)

    def _elapsed(self, segment: pd.DataFrame) -> np.ndarray:
        """Hours elapsed since the start of the segment."""
        start = segment["timestamp"].iloc[0]
        return (
            (segment["timestamp"] - start).dt.total_seconds() / 3600.0
        ).to_numpy()

    # ------------------------------------------------------------------
    # 1-3. Single-metric plots
    # ------------------------------------------------------------------

    def _plot_single(
        self,
        role: str,
        node: str | int,
        save: bool,
        filename: str | None,
    ) -> tuple[plt.Figure, Path | None]:
        """Shared implementation for the three single-metric plots."""
        frame, report = self._frame(node)
        if role not in frame.columns:
            raise VisualizationError(f"Role {role!r} not present in frame.")

        segments = self._split_segments(frame)
        fig = plt.figure(figsize=(12, 4))
        axes = self._segment_axes(fig, segments, n_rows=1)

        values = frame[role]
        pad = max((values.max() - values.min()) * 0.08, 0.5)
        limits = (values.min() - pad, values.max() + pad)

        for index, (axis, segment) in enumerate(zip(axes[0], segments)):
            hours = self._elapsed(segment)
            axis.plot(
                hours,
                segment[role].to_numpy(),
                color=ROLE_COLOURS.get(role, "#333333"),
                linewidth=0.7,
            )
            axis.set_ylim(limits)
            axis.grid(alpha=0.25, linewidth=0.5)
            self._format_time_axis(
                axis, segment, narrow=len(segments) > 1 and index > 0
            )

            duration = (
                segment["timestamp"].iloc[-1] - segment["timestamp"].iloc[0]
            ).total_seconds() / 3600.0
            axis.set_title(
                f"Segment {index + 1}: {duration:.3f} h, "
                f"{len(segment)} samples",
                fontsize=9,
            )
            if index == 0:
                axis.set_ylabel(ROLE_LABELS.get(role, role))
            if len(segments) > 1:
                self._mark_break(
                    axis, "right" if index < len(segments) - 1 else "left"
                )

        gap_note = ""
        if len(segments) > 1:
            gap = (
                segments[1]["timestamp"].iloc[0]
                - segments[0]["timestamp"].iloc[-1]
            ).total_seconds() / 3600.0
            gap_note = f"  |  segments separated by {gap:.1f} h with no data"

        fig.suptitle(
            f"Node {report['node']}  |  {role}  |  "
            f"{len(segments)} segment(s){gap_note}",
            fontsize=10,
        )

        path = None
        if save:
            path = self._save(
                fig, filename or f"node{report['node']}_{role}.png"
            )
        return fig, path

    def plot_temperature(
        self,
        node: str | int = DEFAULT_NODE,
        save: bool = True,
        filename: str | None = None,
    ) -> tuple[plt.Figure, Path | None]:
        """Plot temperature against time, split at segment boundaries.

        Parameters
        ----------
        node:
            Node identifier. Defaults to :data:`DEFAULT_NODE`.
        save:
            Write the figure to ``output_dir``.
        filename:
            Override the generated filename.

        Returns
        -------
        tuple
            ``(figure, path_or_None)``.
        """
        return self._plot_single("temperature", node, save, filename)

    def plot_power(
        self,
        node: str | int = DEFAULT_NODE,
        save: bool = True,
        filename: str | None = None,
    ) -> tuple[plt.Figure, Path | None]:
        """Plot power against time, split at segment boundaries.

        Parameters
        ----------
        node:
            Node identifier.
        save:
            Write the figure to ``output_dir``.
        filename:
            Override the generated filename.

        Returns
        -------
        tuple
            ``(figure, path_or_None)``.
        """
        return self._plot_single("power", node, save, filename)

    def plot_fan_speed(
        self,
        node: str | int = DEFAULT_NODE,
        save: bool = True,
        filename: str | None = None,
    ) -> tuple[plt.Figure, Path | None]:
        """Plot fan speed against time, split at segment boundaries.

        Parameters
        ----------
        node:
            Node identifier.
        save:
            Write the figure to ``output_dir``.
        filename:
            Override the generated filename.

        Returns
        -------
        tuple
            ``(figure, path_or_None)``.
        """
        return self._plot_single("fan_speed", node, save, filename)

    # ------------------------------------------------------------------
    # 4-5. Relationship plots
    # ------------------------------------------------------------------

    def _cross_correlation(
        self,
        segment: pd.DataFrame,
        driver: str,
        response: str,
        max_lag_samples: int = 90,
    ) -> dict[str, Any]:
        """Cross-correlate two columns over a range of sample lags.

        A positive lag means ``response`` is compared against an earlier
        ``driver`` sample. This measures temporal association only; it
        asserts nothing about mechanism.

        Returns
        -------
        dict
            ``lags_s``, ``correlations``, ``peak_lag_s``,
            ``peak_correlation``, ``zero_lag_correlation``, and
            ``interval_s``.
        """
        left = segment[driver].to_numpy(dtype="float64")
        right = segment[response].to_numpy(dtype="float64")
        interval = float(
            segment["timestamp"].diff().dt.total_seconds().dropna().median()
        )

        n = len(left)
        max_lag = int(min(max_lag_samples, max(n // 4, 1)))
        lags = range(0, max_lag + 1)

        correlations: list[float] = []
        for lag in lags:
            a = left[: n - lag] if lag else left
            b = right[lag:] if lag else right
            if len(a) < 3 or np.std(a) == 0 or np.std(b) == 0:
                correlations.append(np.nan)
            else:
                correlations.append(float(np.corrcoef(a, b)[0, 1]))

        array = np.array(correlations, dtype="float64")
        if np.all(np.isnan(array)):
            peak_index = 0
            peak_value = float("nan")
        else:
            peak_index = int(np.nanargmax(np.abs(array)))
            peak_value = float(array[peak_index])

        return {
            "driver": driver,
            "response": response,
            "interval_s": interval,
            "lags_s": [lag * interval for lag in lags],
            "correlations": correlations,
            "peak_lag_s": peak_index * interval,
            "peak_correlation": peak_value,
            "zero_lag_correlation": (
                float(array[0]) if len(array) and not np.isnan(array[0])
                else float("nan")
            ),
            "n_samples": n,
        }

    def _plot_relationship(
        self,
        driver: str,
        response: str,
        node: str | int,
        save: bool,
        filename: str | None,
    ) -> tuple[plt.Figure, Path | None]:
        """Shared implementation for the two relationship plots."""
        frame, report = self._frame(node)
        segments = self._split_segments(frame)
        longest = max(segments, key=len)

        fig, axes = plt.subplots(1, 3, figsize=(14, 4))

        # Panel 1: scatter, coloured by position within the segment.
        scatter = axes[0].scatter(
            longest[driver],
            longest[response],
            c=self._elapsed(longest),
            cmap="viridis",
            s=4,
            alpha=0.5,
        )
        axes[0].set_xlabel(ROLE_LABELS.get(driver, driver))
        axes[0].set_ylabel(ROLE_LABELS.get(response, response))
        pearson = longest[driver].corr(longest[response])
        axes[0].set_title(
            f"{driver} vs {response}\nPearson r = {pearson:.4f}", fontsize=9
        )
        axes[0].grid(alpha=0.25, linewidth=0.5)
        fig.colorbar(scatter, ax=axes[0], label="Hours into segment")

        # Panel 2: both series on a shared time axis, independently scaled.
        hours = self._elapsed(longest)
        axes[1].plot(
            hours,
            longest[driver],
            color=ROLE_COLOURS.get(driver, "#333333"),
            linewidth=0.7,
            label=driver,
        )
        axes[1].set_xlabel("Hours from segment start")
        axes[1].set_ylabel(ROLE_LABELS.get(driver, driver),
                           color=ROLE_COLOURS.get(driver, "#333333"))
        twin = axes[1].twinx()
        twin.plot(
            hours,
            longest[response],
            color=ROLE_COLOURS.get(response, "#888888"),
            linewidth=0.7,
            label=response,
        )
        twin.set_ylabel(ROLE_LABELS.get(response, response),
                        color=ROLE_COLOURS.get(response, "#888888"))
        axes[1].set_title("Shared timeline (longest segment)", fontsize=9)
        axes[1].grid(alpha=0.25, linewidth=0.5)

        # Panel 3: cross-correlation against lag.
        cross = self._cross_correlation(longest, driver, response)
        axes[2].plot(
            cross["lags_s"], cross["correlations"], color="#333333",
            linewidth=1.0,
        )
        axes[2].axvline(
            cross["peak_lag_s"], color="#c1440e", linestyle="--", linewidth=1.0
        )
        axes[2].set_xlabel(f"Lag applied to {response} (s)")
        axes[2].set_ylabel("Correlation")
        axes[2].set_title(
            f"Peak |r| = {cross['peak_correlation']:.4f} "
            f"at lag {cross['peak_lag_s']:.0f} s",
            fontsize=9,
        )
        axes[2].grid(alpha=0.25, linewidth=0.5)

        fig.suptitle(
            f"Node {report['node']}  |  {driver} vs {response}  |  "
            f"longest segment only ({len(longest)} samples)",
            fontsize=10,
        )
        fig.tight_layout()

        path = None
        if save:
            path = self._save(
                fig,
                filename
                or f"node{report['node']}_{driver}_vs_{response}.png",
            )
        return fig, path

    def plot_temperature_vs_power(
        self,
        node: str | int = DEFAULT_NODE,
        save: bool = True,
        filename: str | None = None,
    ) -> tuple[plt.Figure, Path | None]:
        """Plot the observed relationship between power and temperature.

        Three panels: scatter, shared timeline, and cross-correlation
        against lag.

        Parameters
        ----------
        node:
            Node identifier.
        save:
            Write the figure to ``output_dir``.
        filename:
            Override the generated filename.

        Returns
        -------
        tuple
            ``(figure, path_or_None)``.

        Notes
        -----
        The lag panel reports where correlation peaks. That is a temporal
        observation. It is not a claim about mechanism.
        """
        return self._plot_relationship(
            "power", "temperature", node, save, filename
        )

    def plot_temperature_vs_fan(
        self,
        node: str | int = DEFAULT_NODE,
        save: bool = True,
        filename: str | None = None,
    ) -> tuple[plt.Figure, Path | None]:
        """Plot the observed relationship between temperature and fan speed.

        Parameters
        ----------
        node:
            Node identifier.
        save:
            Write the figure to ``output_dir``.
        filename:
            Override the generated filename.

        Returns
        -------
        tuple
            ``(figure, path_or_None)``.
        """
        return self._plot_relationship(
            "temperature", "fan_speed", node, save, filename
        )

    # ------------------------------------------------------------------
    # 6. Combined timeline
    # ------------------------------------------------------------------

    def plot_thermal_behaviour(
        self,
        node: str | int = DEFAULT_NODE,
        save: bool = True,
        filename: str | None = None,
    ) -> tuple[plt.Figure, Path | None]:
        """Plot all three metrics on one timeline, stacked and aligned.

        One row per metric, one column per segment. Rows share their time
        axis so changes can be read across metrics at the same instant.

        Parameters
        ----------
        node:
            Node identifier.
        save:
            Write the figure to ``output_dir``.
        filename:
            Override the generated filename.

        Returns
        -------
        tuple
            ``(figure, path_or_None)``.
        """
        frame, report = self._frame(node)
        roles = [r for r in ("power", "temperature", "fan_speed")
                 if r in frame.columns]
        segments = self._split_segments(frame)

        fig = plt.figure(figsize=(13, 7))
        axes = self._segment_axes(fig, segments, n_rows=len(roles))

        for row, role in enumerate(roles):
            values = frame[role]
            pad = max((values.max() - values.min()) * 0.08, 0.5)
            limits = (values.min() - pad, values.max() + pad)

            for col, segment in enumerate(segments):
                axis = axes[row, col]
                axis.plot(
                    self._elapsed(segment),
                    segment[role].to_numpy(),
                    color=ROLE_COLOURS.get(role, "#333333"),
                    linewidth=0.7,
                )
                axis.set_ylim(limits)
                axis.grid(alpha=0.25, linewidth=0.5)

                if col == 0:
                    axis.set_ylabel(ROLE_LABELS.get(role, role), fontsize=9)
                if row == 0:
                    duration = (
                        segment["timestamp"].iloc[-1]
                        - segment["timestamp"].iloc[0]
                    ).total_seconds() / 3600.0
                    axis.set_title(
                        f"Segment {col + 1}: {duration:.3f} h, "
                        f"{len(segment)} samples",
                        fontsize=9,
                    )
                if row == len(roles) - 1:
                    self._format_time_axis(
                        axis, segment, narrow=len(segments) > 1 and col > 0
                    )
                else:
                    axis.tick_params(labelbottom=False)
                    axis.set_xlim(
                        0,
                        max(self._elapsed(segment).max(), 0.01),
                    )
                if len(segments) > 1:
                    self._mark_break(
                        axis, "right" if col < len(segments) - 1 else "left"
                    )

        fig.suptitle(
            f"Node {report['node']}  |  thermal behaviour  |  "
            f"{len(segments)} segment(s), axes not continuous across the gap",
            fontsize=10,
        )

        path = None
        if save:
            path = self._save(
                fig, filename or f"node{report['node']}_thermal_behaviour.png"
            )
        return fig, path

    # ------------------------------------------------------------------
    # 7. Segment boundaries
    # ------------------------------------------------------------------

    def plot_segment_boundaries(
        self,
        node: str | int = DEFAULT_NODE,
        save: bool = True,
        filename: str | None = None,
    ) -> tuple[plt.Figure, Path | None]:
        """Show where data exists and where it does not.

        Two panels: sample occupancy on the true wall-clock axis, and the
        distribution of inter-sample intervals on a log scale.

        Parameters
        ----------
        node:
            Node identifier.
        save:
            Write the figure to ``output_dir``.
        filename:
            Override the generated filename.

        Returns
        -------
        tuple
            ``(figure, path_or_None)``.

        Notes
        -----
        This is the one figure drawn on a single continuous wall-clock
        axis, precisely so the emptiness of the gap is visible.
        """
        frame, report = self._frame(node)
        segments = self._split_segments(frame)

        fig, axes = plt.subplots(
            2, 1, figsize=(12, 5), gridspec_kw={"height_ratios": [1, 1.3]}
        )

        # Panel 1: occupancy on the true wall-clock axis.
        for index, segment in enumerate(segments):
            axes[0].axvspan(
                segment["timestamp"].iloc[0],
                segment["timestamp"].iloc[-1],
                color="#1f4e79",
                alpha=0.35,
            )
            duration = (
                segment["timestamp"].iloc[-1] - segment["timestamp"].iloc[0]
            ).total_seconds() / 3600.0
            axes[0].annotate(
                f"Segment {index + 1}\n{duration:.3f} h\n{len(segment)} samples",
                xy=(segment["timestamp"].iloc[0], 0.5),
                fontsize=8,
                va="center",
            )
        axes[0].plot(
            frame["timestamp"],
            np.full(len(frame), 0.15),
            "|",
            color="#c1440e",
            markersize=4,
            alpha=0.3,
        )
        axes[0].set_ylim(0, 1)
        axes[0].set_yticks([])
        axes[0].set_xlabel("Wall clock (UTC)")
        axes[0].set_title(
            "Sample occupancy on a continuous axis "
            "(shaded = data present, blank = no data)",
            fontsize=9,
        )

        # Panel 2: inter-sample interval distribution.
        deltas = frame["timestamp"].diff().dt.total_seconds().dropna()
        positive = deltas[deltas > 0]
        # Pad the bin range outwards. Building edges with
        # np.logspace(log10(min), ...) yields a first edge fractionally
        # above min in floating point, which silently drops every sample
        # sitting exactly at the minimum -- here that is 99.99% of the
        # data. The padding guarantees the extremes are counted.
        edges = np.logspace(
            np.log10(positive.min() * 0.9),
            np.log10(positive.max() * 1.1),
            60,
        )
        counted = int(np.histogram(positive, bins=edges)[0].sum())
        if counted != len(positive):  # pragma: no cover - guard
            raise VisualizationError(
                f"Interval histogram would drop "
                f"{len(positive) - counted} of {len(positive)} samples; "
                f"refusing to plot a misleading distribution."
            )
        axes[1].hist(positive, bins=edges, color="#2e7d32", alpha=0.8)
        axes[1].set_xscale("log")
        axes[1].set_yscale("log")
        axes[1].set_xlabel("Interval between consecutive samples (s)")
        axes[1].set_ylabel("Count")
        axes[1].set_title(
            f"Interval distribution: median {positive.median():.0f} s, "
            f"maximum {positive.max() / 3600:.1f} h",
            fontsize=9,
        )
        axes[1].grid(alpha=0.25, linewidth=0.5)

        fig.suptitle(
            f"Node {report['node']}  |  segment boundaries  |  "
            f"{len(segments)} segment(s)",
            fontsize=10,
        )
        fig.tight_layout()

        path = None
        if save:
            path = self._save(
                fig, filename or f"node{report['node']}_segments.png"
            )
        return fig, path

    # ------------------------------------------------------------------
    # 8. Report
    # ------------------------------------------------------------------

    def generate_visualization_report(
        self, node: str | int = DEFAULT_NODE
    ) -> dict[str, Any]:
        """Summarise what the plotted data looks like.

        Parameters
        ----------
        node:
            Node identifier.

        Returns
        -------
        dict
            ``node``, ``statistics`` per role, ``segments``,
            ``relationships`` (Pearson and lagged cross-correlation),
            and ``observations``.

        Notes
        -----
        Every observation is a descriptive statement about the series.
        No mechanism, law, equation, or physical parameter is named. Where
        a series is near-constant or low-cardinality that is stated
        plainly, because it constrains what any later analysis can show.
        """
        frame, report = self._frame(node)
        segments = self._split_segments(frame)
        roles = [r for r in ("temperature", "power", "fan_speed")
                 if r in frame.columns]

        statistics: dict[str, Any] = {}
        for role in roles:
            series = frame[role]
            statistics[role] = {
                "count": int(series.count()),
                "min": float(series.min()),
                "max": float(series.max()),
                "range": float(series.max() - series.min()),
                "mean": float(series.mean()),
                "median": float(series.median()),
                "std": float(series.std()),
                "n_unique": int(series.nunique()),
                "near_constant": bool(series.std() < NEAR_CONSTANT_STD),
                "low_cardinality": bool(
                    series.nunique() < LOW_CARDINALITY_THRESHOLD
                ),
            }

        segment_info = []
        for index, segment in enumerate(segments):
            duration = (
                segment["timestamp"].iloc[-1] - segment["timestamp"].iloc[0]
            ).total_seconds()
            segment_info.append(
                {
                    "index": index + 1,
                    "start": str(segment["timestamp"].iloc[0]),
                    "end": str(segment["timestamp"].iloc[-1]),
                    "duration_h": round(duration / 3600.0, 4),
                    "n_samples": len(segment),
                }
            )

        longest = max(segments, key=len)
        relationships: dict[str, Any] = {}
        for driver, response in (
            ("power", "temperature"),
            ("temperature", "fan_speed"),
            ("power", "fan_speed"),
        ):
            if driver not in frame.columns or response not in frame.columns:
                continue
            cross = self._cross_correlation(longest, driver, response)
            relationships[f"{driver}->{response}"] = {
                "pearson_r": float(longest[driver].corr(longest[response])),
                "zero_lag_correlation": cross["zero_lag_correlation"],
                "peak_correlation": cross["peak_correlation"],
                "peak_lag_s": cross["peak_lag_s"],
                "interval_s": cross["interval_s"],
            }

        observations: list[str] = []

        observations.append(
            f"{len(segments)} temporal segment(s) present: "
            + "; ".join(
                f"segment {s['index']} spans {s['duration_h']:.3f} h with "
                f"{s['n_samples']} samples"
                for s in segment_info
            )
            + "."
        )
        if len(segments) > 1:
            gap = (
                segments[1]["timestamp"].iloc[0]
                - segments[0]["timestamp"].iloc[-1]
            ).total_seconds() / 3600.0
            observations.append(
                f"No samples exist for {gap:.1f} h between segment 1 and "
                f"segment 2. The segments are not plotted as one continuous "
                f"series."
            )

        for role in roles:
            stats = statistics[role]
            observations.append(
                f"{role} spans {stats['min']:.1f} to {stats['max']:.1f} "
                f"(range {stats['range']:.1f}, std {stats['std']:.2f}) across "
                f"{stats['n_unique']} distinct recorded values."
            )
            if stats["near_constant"]:
                observations.append(
                    f"{role} has a standard deviation of {stats['std']:.2f}, "
                    f"below {NEAR_CONSTANT_STD}; the series is near-constant "
                    f"on this node."
                )
            if stats["low_cardinality"]:
                observations.append(
                    f"{role} takes only {stats['n_unique']} distinct values on "
                    f"this node."
                )

        for key, info in relationships.items():
            driver, response = key.split("->")
            observations.append(
                f"{driver} and {response} show a Pearson correlation of "
                f"{info['pearson_r']:.4f} at zero lag; the largest absolute "
                f"correlation is {info['peak_correlation']:.4f} when "
                f"{response} is compared against {driver} "
                f"{info['peak_lag_s']:.0f} s earlier."
            )
            if abs(info["peak_correlation"]) < MIN_REPORTABLE_CORRELATION:
                # Below this magnitude the peak lag is noise. Stating that
                # one series "follows" another here would fabricate a
                # temporal claim the data does not support.
                observations.append(
                    f"The largest absolute correlation between {driver} and "
                    f"{response} is {abs(info['peak_correlation']):.4f}, below "
                    f"{MIN_REPORTABLE_CORRELATION}; no temporal association is "
                    f"distinguishable from scatter at any lag examined, and "
                    f"the peak lag is not reported as meaningful."
                )
            elif (
                abs(info["peak_correlation"])
                > abs(info["zero_lag_correlation"])
                and info["peak_lag_s"] > 0
            ):
                observations.append(
                    f"Correlation between {driver} and {response} is larger at "
                    f"a lag of {info['peak_lag_s']:.0f} s than at zero lag; "
                    f"changes in {response} appear later than changes in "
                    f"{driver}."
                )

        return {
            "node": report["node"],
            "n_rows": len(frame),
            "roles": roles,
            "statistics": statistics,
            "segments": segment_info,
            "relationships": relationships,
            "observations": observations,
        }

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def plot_all(
        self, node: str | int = DEFAULT_NODE, close: bool = True
    ) -> dict[str, Path]:
        """Produce every figure for one node.

        Parameters
        ----------
        node:
            Node identifier.
        close:
            Close figures after saving, to bound memory.

        Returns
        -------
        dict
            Figure name to written path.
        """
        produced: dict[str, Path] = {}
        for name, method in (
            ("temperature", self.plot_temperature),
            ("power", self.plot_power),
            ("fan_speed", self.plot_fan_speed),
            ("temperature_vs_power", self.plot_temperature_vs_power),
            ("temperature_vs_fan", self.plot_temperature_vs_fan),
            ("thermal_behaviour", self.plot_thermal_behaviour),
            ("segment_boundaries", self.plot_segment_boundaries),
        ):
            fig, path = method(node=node, save=True)
            if path is not None:
                produced[name] = path
            if close:
                plt.close(fig)
        return produced

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(output_dir={str(self.output_dir)!r}, "
            f"default_node={DEFAULT_NODE!r})"
        )
