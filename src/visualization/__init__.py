"""Visualisation layer (LOCKED).

Re-exports the public API of :mod:`visualization.visualizer`.
"""

from .visualizer import (
    DEFAULT_NODE,
    LOW_CARDINALITY_THRESHOLD,
    NEAR_CONSTANT_STD,
    ROLE_COLOURS,
    ROLE_LABELS,
    ThermalVisualizer,
    VisualizationError,
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
