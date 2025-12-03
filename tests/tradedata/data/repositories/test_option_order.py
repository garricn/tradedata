"""Tests for OptionOrderRepository."""

import json

from tradedata.data.models import OptionOrder, Transaction
from tradedata.data.repositories import OptionOrderRepository, TransactionRepository
from tradedata.data.storage import Storage


class TestOptionOrderRepository:
    """Tests for OptionOrderRepository."""

    def test_create_and_get_by_id(self):
        """Test creating and retrieving an option order."""
        storage = Storage(db_path=":memory:")
        tx_repo = TransactionRepository(storage)
        repo = OptionOrderRepository(storage)

        # Create parent transaction first
        transaction = Transaction(
            id="order-1",
            source="robinhood",
            source_id="rh-123",
            type="option",
            created_at="2025-12-02T10:00:00Z",
            account_id="acc-123",
            raw_data=json.dumps({}),
        )
        tx_repo.create(transaction)

        order = OptionOrder(
            id="order-1",
            chain_symbol="AAPL",
            opening_strategy="vertical_call_spread",
            closing_strategy=None,
            direction="debit",
            premium=100.50,
            net_amount=-100.50,
        )

        created = repo.create(order)
        assert created.id == order.id

        retrieved = repo.get_by_id("order-1")
        assert retrieved is not None
        assert retrieved.chain_symbol == "AAPL"
        assert retrieved.premium == 100.50

        storage.close()

    def test_update(self):
        """Test updating an option order."""
        storage = Storage(db_path=":memory:")
        tx_repo = TransactionRepository(storage)
        repo = OptionOrderRepository(storage)

        # Create parent transaction first
        transaction = Transaction(
            id="order-1",
            source="robinhood",
            source_id="rh-123",
            type="option",
            created_at="2025-12-02T10:00:00Z",
            account_id="acc-123",
            raw_data=json.dumps({}),
        )
        tx_repo.create(transaction)

        order = OptionOrder(
            id="order-1",
            chain_symbol="AAPL",
            opening_strategy="vertical_call_spread",
            closing_strategy=None,
            direction="debit",
            premium=100.50,
            net_amount=-100.50,
        )
        repo.create(order)

        order.premium = 150.75
        repo.update(order)

        retrieved = repo.get_by_id("order-1")
        assert retrieved is not None
        assert retrieved.premium == 150.75

        storage.close()

    def test_delete(self):
        """Test deleting an option order."""
        storage = Storage(db_path=":memory:")
        tx_repo = TransactionRepository(storage)
        repo = OptionOrderRepository(storage)

        # Create parent transaction first
        transaction = Transaction(
            id="order-1",
            source="robinhood",
            source_id="rh-123",
            type="option",
            created_at="2025-12-02T10:00:00Z",
            account_id="acc-123",
            raw_data=json.dumps({}),
        )
        tx_repo.create(transaction)

        order = OptionOrder(
            id="order-1",
            chain_symbol="AAPL",
            opening_strategy="vertical_call_spread",
            closing_strategy=None,
            direction="debit",
            premium=100.50,
            net_amount=-100.50,
        )
        repo.create(order)

        deleted = repo.delete("order-1")
        assert deleted is True

        retrieved = repo.get_by_id("order-1")
        assert retrieved is None

        storage.close()
