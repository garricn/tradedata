"""Abstract base class for data source adapters.

Provides unified interface for extracting and normalizing data from different sources.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from tradedata.data.models import Transaction


class DataSourceAdapter(ABC):
    """Abstract base class for data source adapters.

    All data source adapters (Robinhood, IBKR, etc.) must implement this interface
    to provide a unified way to extract and normalize trading data.

    Subclasses should:
    1. Implement extract_transactions() to fetch raw transaction data
    2. Implement extract_positions() to fetch current positions
    3. Implement normalize_transaction() to convert source-specific format to unified schema
    """

    @abstractmethod
    def extract_transactions(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """Extract transactions from source.

        Args:
            start_date: Optional start date filter (ISO format string, e.g., '2025-01-01')
            end_date: Optional end date filter (ISO format string, e.g., '2025-12-31')

        Returns:
            List of raw transaction dictionaries from the source.
            Each dict contains source-specific transaction data that will be
            normalized using normalize_transaction().

        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def extract_positions(self) -> list[dict[str, Any]]:
        """Extract current positions from source.

        Returns:
            List of raw position dictionaries from the source.
            Each dict contains source-specific position data.

        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def normalize_transaction(self, raw_transaction: dict[str, Any]) -> Transaction:
        """Convert source-specific format to unified schema.

        Args:
            raw_transaction: Raw transaction dictionary from extract_transactions()

        Returns:
            Transaction model instance with normalized data.

        Raises:
            NotImplementedError: Must be implemented by subclasses.
            ValueError: If raw_transaction is missing required fields.
        """
        pass
