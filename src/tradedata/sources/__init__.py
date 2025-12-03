"""Data source adapters for extracting and normalizing trading data.

This package provides:
- Abstract base class for data source adapters
- Factory pattern for creating adapters
- Implementations for specific data sources (e.g., Robinhood)
"""

from tradedata.sources.base import DataSourceAdapter
from tradedata.sources.factory import SourceFactory, create_adapter

__all__ = ["DataSourceAdapter", "SourceFactory", "create_adapter"]
