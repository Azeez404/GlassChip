"""Preprocessing layer (LOCKED).

Re-exports the public API of the four preprocessing modules so that
``from preprocessing import MetricSelector`` works, while submodules remain
importable individually as ``preprocessing.metric_selector`` etc.
"""

from .exporter import SUPPORTED_FORMATS, ExportError, Exporter
from .metric_selector import (
    GLASSCHIP_V1_METRICS,
    SUPPORTED_ROLES,
    IncompatibleSelectionError,
    MetricSelector,
    SelectionError,
)
from .preprocessor import (
    MODEL_COLUMNS,
    PHYSICAL_BOUNDS,
    PreprocessingError,
    Preprocessor,
)
from .timeseries_builder import TimeSeriesBuilder, TimeSeriesError

__all__ = [
    "MetricSelector",
    "SelectionError",
    "IncompatibleSelectionError",
    "GLASSCHIP_V1_METRICS",
    "SUPPORTED_ROLES",
    "Preprocessor",
    "PreprocessingError",
    "PHYSICAL_BOUNDS",
    "MODEL_COLUMNS",
    "TimeSeriesBuilder",
    "TimeSeriesError",
    "Exporter",
    "ExportError",
    "SUPPORTED_FORMATS",
]
