"""Validation layer (LOCKED).

Re-exports the public API of :mod:`validator.validator` so that
``from validator import DatasetValidator`` keeps working unchanged.
"""

from .validator import (
    EXACT_MATCH_TOLERANCE_S,
    GAP_THRESHOLD_MULTIPLIER,
    GLASSCHIP_MANDATORY_INPUTS,
    JITTER_TOLERANCE_S,
    MIN_CONTIGUOUS_SEGMENT_S,
    MIN_COVERAGE_RATIO,
    MIN_EXACT_MATCH_RATIO,
    MIN_NODE_OVERLAP_RATIO,
    DatasetValidator,
    ValidationError,
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
