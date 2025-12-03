"""Tests for ExecutionRepository."""

import json

from tradedata.data.models import Execution, Transaction
from tradedata.data.repositories import ExecutionRepository, TransactionRepository
from tradedata.data.storage import Storage


class TestExecutionRepository:
    """Tests for ExecutionRepository."""

    def test_create_and_get_by_id(self):
        """Test creating and retrieving an execution."""
        storage = Storage(db_path=":memory:")
        tx_repo = TransactionRepository(storage)
        repo = ExecutionRepository(storage)

        # Create parent transaction first (executions reference transactions)
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

        execution = Execution(
            id="exec-1",
            order_id="order-1",
            leg_id=None,  # leg_id is nullable
            price=2.50,
            quantity=10.0,
            timestamp="2025-12-02T10:00:00Z",
            settlement_date="2025-12-04",
        )

        created = repo.create(execution)
        assert created.id == execution.id

        retrieved = repo.get_by_id("exec-1")
        assert retrieved is not None
        assert retrieved.price == 2.50
        assert retrieved.quantity == 10.0

        storage.close()

    def test_find_by_order_id(self):
        """Test finding executions by order ID."""
        storage = Storage(db_path=":memory:")
        tx_repo = TransactionRepository(storage)
        repo = ExecutionRepository(storage)

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

        exec1 = Execution(
            id="exec-1",
            order_id="order-1",
            leg_id=None,
            price=2.50,
            quantity=10.0,
            timestamp="2025-12-02T10:00:00Z",
            settlement_date="2025-12-04",
        )
        exec2 = Execution(
            id="exec-2",
            order_id="order-1",
            leg_id=None,
            price=2.75,
            quantity=10.0,
            timestamp="2025-12-02T10:05:00Z",
            settlement_date="2025-12-04",
        )

        repo.create(exec1)
        repo.create(exec2)

        order1_execs = repo.find_by_order_id("order-1")
        assert len(order1_execs) == 2

        storage.close()
