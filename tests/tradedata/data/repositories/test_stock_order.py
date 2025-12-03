"""Tests for StockOrderRepository."""

import json

from tradedata.data.models import StockOrder, Transaction
from tradedata.data.repositories import StockOrderRepository, TransactionRepository
from tradedata.data.storage import Storage


class TestStockOrderRepository:
    """Tests for StockOrderRepository."""

    def test_create_and_get_by_id(self):
        """Test creating and retrieving a stock order."""
        storage = Storage(db_path=":memory:")
        tx_repo = TransactionRepository(storage)
        repo = StockOrderRepository(storage)

        # Create parent transaction first
        transaction = Transaction(
            id="stock-order-1",
            source="robinhood",
            source_id="rh-123",
            type="stock",
            created_at="2025-12-02T10:00:00Z",
            account_id="acc-123",
            raw_data=json.dumps({}),
        )
        tx_repo.create(transaction)

        order = StockOrder(
            id="stock-order-1",
            symbol="AAPL",
            side="buy",
            quantity=100.0,
            price=150.0,
            average_price=149.50,
        )

        created = repo.create(order)
        assert created.id == order.id

        retrieved = repo.get_by_id("stock-order-1")
        assert retrieved is not None
        assert retrieved.symbol == "AAPL"
        assert retrieved.quantity == 100.0

        storage.close()
