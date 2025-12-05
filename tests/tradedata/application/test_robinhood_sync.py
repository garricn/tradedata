"""Tests for transaction sync orchestration."""

import json
import uuid
from unittest.mock import MagicMock

import pytest

from tradedata.application import robinhood_sync
from tradedata.data.models import Execution, OptionLeg, OptionOrder, StockOrder, Transaction
from tradedata.data.repositories import (
    ExecutionRepository,
    OptionLegRepository,
    OptionOrderRepository,
    StockOrderRepository,
    TransactionRepository,
)
from tradedata.data.storage import Storage
from tradedata.data.validator import ValidationError


class FakeAdapter:
    """Fake adapter that returns deterministic data for integration-style test."""

    def __init__(self):
        self.logged_in = False
        self.option_tx_id = str(uuid.uuid4())
        self.stock_tx_id = str(uuid.uuid4())
        self.raw_option = {"id": "raw-option"}
        self.raw_stock = {"id": "raw-stock"}

    def login(self, username: str, password: str) -> None:
        self.logged_in = True
        self.login_args = (username, password)

    def extract_transactions(self, start_date=None, end_date=None):
        self.extract_args = (start_date, end_date)
        return [self.raw_option, self.raw_stock]

    def normalize_transaction(self, raw_transaction):
        if raw_transaction is self.raw_option:
            return Transaction(
                id=self.option_tx_id,
                source="robinhood",
                source_id="opt-123",
                type="option",
                created_at="2025-01-01T00:00:00Z",
                account_id=None,
                raw_data=json.dumps(raw_transaction),
            )

        return Transaction(
            id=self.stock_tx_id,
            source="robinhood",
            source_id="stk-123",
            type="stock",
            created_at="2025-01-02T00:00:00Z",
            account_id=None,
            raw_data=json.dumps(raw_transaction),
        )

    def extract_option_order(self, raw_transaction, transaction_id):
        if raw_transaction is not self.raw_option:
            return None

        return OptionOrder(
            id=transaction_id,
            chain_symbol="AAPL",
            opening_strategy="vertical_call_spread",
            closing_strategy=None,
            direction="debit",
            premium=2.5,
            net_amount=-250.0,
        )

    def extract_option_legs(self, raw_transaction, option_order_id):
        if raw_transaction is not self.raw_option:
            return []

        return [
            OptionLeg(
                id=str(uuid.uuid4()),
                order_id=option_order_id,
                strike_price=150.0,
                expiration_date="2025-06-01T00:00:00Z",
                option_type="call",
                side="buy",
                position_effect="open",
                ratio_quantity=1,
            ),
            OptionLeg(
                id=str(uuid.uuid4()),
                order_id=option_order_id,
                strike_price=155.0,
                expiration_date="2025-06-01T00:00:00Z",
                option_type="call",
                side="sell",
                position_effect="open",
                ratio_quantity=1,
            ),
        ]

    def extract_executions(self, raw_transaction, transaction_id, leg_ids=None):
        if raw_transaction is not self.raw_option:
            return []

        leg_id = leg_ids[0] if leg_ids else None
        return [
            Execution(
                id=str(uuid.uuid4()),
                order_id=transaction_id,
                leg_id=leg_id,
                price=2.5,
                quantity=10.0,
                timestamp="2025-01-01T10:00:00Z",
                settlement_date=None,
            )
        ]

    def extract_stock_order(self, raw_transaction, transaction_id):
        if raw_transaction is not self.raw_stock:
            return None

        return StockOrder(
            id=transaction_id,
            symbol="MSFT",
            side="buy",
            quantity=5,
            price=100.0,
            average_price=100.0,
        )


def test_sync_transactions_persists_option_and_stock(monkeypatch):
    """Integration-style test that data flows through validation and storage."""
    storage = Storage(db_path=":memory:")
    adapter = FakeAdapter()
    monkeypatch.setattr(
        robinhood_sync.credentials,
        "get_credentials",
        lambda source: ("user", "pw"),
    )

    stored = robinhood_sync.sync_transactions(
        source="robinhood",
        storage=storage,
        adapter=adapter,
    )

    assert adapter.logged_in
    assert len(stored) == 2

    tx_repo = TransactionRepository(storage)
    option_repo = OptionOrderRepository(storage)
    leg_repo = OptionLegRepository(storage)
    execution_repo = ExecutionRepository(storage)
    stock_repo = StockOrderRepository(storage)

    assert len(tx_repo.find_all()) == 2
    assert option_repo.get_by_id(adapter.option_tx_id) is not None
    assert len(leg_repo.find_all()) == 2
    assert len(execution_repo.find_all()) == 1
    assert stock_repo.get_by_id(adapter.stock_tx_id) is not None


def test_sync_transactions_uses_factory_when_adapter_not_provided(monkeypatch):
    """Ensure factory creation and login are invoked when adapter is omitted."""
    mock_adapter = MagicMock()
    mock_adapter.extract_transactions.return_value = []

    def mock_get_credentials(source):
        return ("user", "pw")

    monkeypatch.setattr(robinhood_sync, "create_adapter", MagicMock(return_value=mock_adapter))
    monkeypatch.setattr(robinhood_sync.credentials, "get_credentials", mock_get_credentials)

    storage = Storage(db_path=":memory:")
    robinhood_sync.sync_transactions(
        source="robinhood", start_date="2025-01-01", end_date="2025-02-01", storage=storage
    )

    robinhood_sync.create_adapter.assert_called_once_with("robinhood")
    mock_adapter.login.assert_called_once_with("user", "pw")
    mock_adapter.extract_transactions.assert_called_once_with(
        start_date="2025-01-01", end_date="2025-02-01"
    )


def test_sync_transactions_raises_on_validation_failure(monkeypatch):
    """Fail fast when validation errors occur."""
    bad_adapter = MagicMock()
    tx_id = str(uuid.uuid4())
    bad_adapter.normalize_transaction.return_value = Transaction(
        id=tx_id,
        source="robinhood",
        source_id="bad",
        type="stock",
        created_at="2025-01-02T00:00:00Z",
        account_id=None,
        raw_data=json.dumps({"id": "bad"}),
    )
    bad_adapter.extract_transactions.return_value = [{"id": "bad"}]
    bad_adapter.extract_option_order.return_value = None
    bad_adapter.extract_stock_order.return_value = None

    monkeypatch.setattr(robinhood_sync.credentials, "get_credentials", lambda source: ("u", "p"))
    monkeypatch.setattr(
        robinhood_sync, "validate_transaction", MagicMock(side_effect=ValidationError("boom"))
    )

    storage = Storage(db_path=":memory:")

    with pytest.raises(ValidationError):
        robinhood_sync.sync_transactions(storage=storage, adapter=bad_adapter)

    assert TransactionRepository(storage).find_all() == []
