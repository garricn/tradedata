"""Tests for TransactionRepository."""

import json

from tradedata.data.models import Transaction
from tradedata.data.repositories import TransactionRepository
from tradedata.data.storage import Storage


class TestTransactionRepository:
    """Tests for TransactionRepository."""

    def test_create_and_get_by_id(self):
        """Test creating and retrieving a transaction."""
        storage = Storage(db_path=":memory:")
        repo = TransactionRepository(storage)

        transaction = Transaction(
            id="tx-1",
            source="robinhood",
            source_id="rh-123",
            type="option",
            created_at="2025-12-02T10:00:00Z",
            account_id="acc-123",
            raw_data=json.dumps({"key": "value"}),
        )

        created = repo.create(transaction)
        assert created.id == transaction.id

        retrieved = repo.get_by_id("tx-1")
        assert retrieved is not None
        assert retrieved.id == transaction.id
        assert retrieved.source == transaction.source
        assert retrieved.type == transaction.type

        storage.close()

    def test_get_by_id_not_found(self):
        """Test getting non-existent transaction."""
        storage = Storage(db_path=":memory:")
        repo = TransactionRepository(storage)

        result = repo.get_by_id("nonexistent")
        assert result is None

        storage.close()

    def test_update(self):
        """Test updating a transaction."""
        storage = Storage(db_path=":memory:")
        repo = TransactionRepository(storage)

        transaction = Transaction(
            id="tx-1",
            source="robinhood",
            source_id="rh-123",
            type="option",
            created_at="2025-12-02T10:00:00Z",
            account_id="acc-123",
            raw_data=json.dumps({"key": "value"}),
        )
        repo.create(transaction)

        transaction.type = "stock"
        repo.update(transaction)

        retrieved = repo.get_by_id("tx-1")
        assert retrieved is not None
        assert retrieved.type == "stock"

        storage.close()

    def test_delete(self):
        """Test deleting a transaction."""
        storage = Storage(db_path=":memory:")
        repo = TransactionRepository(storage)

        transaction = Transaction(
            id="tx-1",
            source="robinhood",
            source_id="rh-123",
            type="option",
            created_at="2025-12-02T10:00:00Z",
            account_id="acc-123",
            raw_data=json.dumps({"key": "value"}),
        )
        repo.create(transaction)

        deleted = repo.delete("tx-1")
        assert deleted is True

        retrieved = repo.get_by_id("tx-1")
        assert retrieved is None

        deleted_again = repo.delete("tx-1")
        assert deleted_again is False

        storage.close()

    def test_find_all(self):
        """Test finding all transactions."""
        storage = Storage(db_path=":memory:")
        repo = TransactionRepository(storage)

        tx1 = Transaction(
            id="tx-1",
            source="robinhood",
            source_id="rh-123",
            type="option",
            created_at="2025-12-02T10:00:00Z",
            account_id="acc-123",
            raw_data=json.dumps({}),
        )
        tx2 = Transaction(
            id="tx-2",
            source="robinhood",
            source_id="rh-124",
            type="stock",
            created_at="2025-12-02T11:00:00Z",
            account_id="acc-123",
            raw_data=json.dumps({}),
        )

        repo.create(tx1)
        repo.create(tx2)

        all_tx = repo.find_all()
        assert len(all_tx) == 2

        storage.close()

    def test_find_by_source(self):
        """Test finding transactions by source."""
        storage = Storage(db_path=":memory:")
        repo = TransactionRepository(storage)

        tx1 = Transaction(
            id="tx-1",
            source="robinhood",
            source_id="rh-123",
            type="option",
            created_at="2025-12-02T10:00:00Z",
            account_id="acc-123",
            raw_data=json.dumps({}),
        )
        tx2 = Transaction(
            id="tx-2",
            source="ibkr",
            source_id="ib-123",
            type="stock",
            created_at="2025-12-02T11:00:00Z",
            account_id="acc-123",
            raw_data=json.dumps({}),
        )

        repo.create(tx1)
        repo.create(tx2)

        robinhood_tx = repo.find_by_source("robinhood")
        assert len(robinhood_tx) == 1
        assert robinhood_tx[0].source == "robinhood"

        storage.close()

    def test_find_by_type(self):
        """Test finding transactions by type."""
        storage = Storage(db_path=":memory:")
        repo = TransactionRepository(storage)

        tx1 = Transaction(
            id="tx-1",
            source="robinhood",
            source_id="rh-123",
            type="option",
            created_at="2025-12-02T10:00:00Z",
            account_id="acc-123",
            raw_data=json.dumps({}),
        )
        tx2 = Transaction(
            id="tx-2",
            source="robinhood",
            source_id="rh-124",
            type="stock",
            created_at="2025-12-02T11:00:00Z",
            account_id="acc-123",
            raw_data=json.dumps({}),
        )

        repo.create(tx1)
        repo.create(tx2)

        option_tx = repo.find_by_type("option")
        assert len(option_tx) == 1
        assert option_tx[0].type == "option"

        storage.close()
