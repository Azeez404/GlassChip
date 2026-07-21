"""Dataset loading layer (LOCKED).

Re-exports the public API of :mod:`loader.loader` so that
``from loader import DatasetLoader`` keeps working unchanged.
"""

from .loader import (
    NODE_SCOPED_PLUGINS,
    DatasetLoader,
    DatasetLoaderError,
    MetricNotFoundError,
    NodeNotFoundError,
)

__all__ = [
    "DatasetLoader",
    "DatasetLoaderError",
    "MetricNotFoundError",
    "NodeNotFoundError",
    "NODE_SCOPED_PLUGINS",
]
