"""Data source adapters for extracting and normalizing trading data.

This package provides:
- Abstract base class for data source adapters
- Factory pattern for creating adapters
- Implementations for specific data sources (e.g., Robinhood)
"""

from tradedata.sources.base import DataSourceAdapter
from tradedata.sources.factory import SourceFactory, create_adapter, get_factory
from tradedata.sources.robinhood import RobinhoodAdapter

# Auto-register common adapters
_factory = get_factory()
if not _factory.is_registered("robinhood"):
    _factory.register("robinhood", RobinhoodAdapter)

__all__ = [
    "DataSourceAdapter",
    "SourceFactory",
    "create_adapter",
    "RobinhoodAdapter",
]
