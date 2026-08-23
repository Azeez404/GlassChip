"""Heterogeneous-sampling alignment for GLASSCHIP.

Additive to the frozen V1 pipeline (which exact-joins the rigid 20 s IPMI
triple). ``AsofAligner`` combines metrics recorded at different native rates
without fabricating values: a causal, backward as-of match with a per-metric
max-staleness bound and explicit missingness flags.
"""
from .aligner import AsofAligner, AlignmentError, MetricAlignment
from .heterogeneous_builder import (
    HeterogeneousTimeSeriesBuilder,
    BuilderError,
    DEFAULT_ROLE_METRICS,
    DEFAULT_STALENESS_S,
)

__all__ = [
    "AsofAligner", "AlignmentError", "MetricAlignment",
    "HeterogeneousTimeSeriesBuilder", "BuilderError",
    "DEFAULT_ROLE_METRICS", "DEFAULT_STALENESS_S",
]
