"""Tests for transaction sync orchestration."""

import json
import uuid
from unittest.mock import MagicMock

import pytest

from tradedata.application import robinhood_sync
from tradedata.data.models import (
    Execution,
    OptionLeg,
    OptionOrder,
    Position,
    StockOrder,
    Transaction,
)
from tradedata.data.repositories import (
    ExecutionRepository,
    OptionLegRepository,
    OptionOrderRepository,
    PositionRepository,
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


def test_sync_transactions_filters_types(monkeypatch):
    """Ensure type filtering skips non-matching transactions."""
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
        types=["stock"],
    )

    assert len(stored) == 1
    assert stored[0].type == "stock"

    tx_repo = TransactionRepository(storage)
    assert len(tx_repo.find_all()) == 1


def test_sync_transactions_is_atomic(monkeypatch):
    """Ensure partial writes are rolled back when a child insert fails."""
    storage = Storage(db_path=":memory:")
    adapter = FakeAdapter()
    monkeypatch.setattr(
        robinhood_sync.credentials,
        "get_credentials",
        lambda source: ("user", "pw"),
    )

    def fail_create(self, entity, conn=None):
        raise RuntimeError("boom")

    monkeypatch.setattr(OptionLegRepository, "create", fail_create)

    with pytest.raises(RuntimeError):
        robinhood_sync.sync_transactions(
            source="robinhood",
            storage=storage,
            adapter=adapter,
        )

    tx_repo = TransactionRepository(storage)
    option_repo = OptionOrderRepository(storage)
    leg_repo = OptionLegRepository(storage)
    execution_repo = ExecutionRepository(storage)
    stock_repo = StockOrderRepository(storage)

    assert len(tx_repo.find_all()) == 0
    assert len(option_repo.find_all()) == 0
    assert len(leg_repo.find_all()) == 0
    assert len(execution_repo.find_all()) == 0
    assert len(stock_repo.find_all()) == 0


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


def test_sync_transactions_skips_existing(monkeypatch):
    """Skip inserting duplicate source/source_id instead of raising."""
    storage = Storage(db_path=":memory:")
    tx_repo = TransactionRepository(storage)

    existing = Transaction(
        id="existing-id",
        source="robinhood",
        source_id="rh-1",
        type="stock",
        created_at="2025-01-01T00:00:00Z",
        account_id=None,
        raw_data="{}",
    )
    tx_repo.create(existing)

    class Adapter:
        def login(self, username, password):
            return None

        def extract_transactions(self, start_date=None, end_date=None):
            return [{"id": "rh-1", "created_at": "2025-01-01T00:00:00Z"}]

        def normalize_transaction(self, raw_transaction):
            return Transaction(
                id=str(uuid.uuid4()),
                source="robinhood",
                source_id="rh-1",
                type="stock",
                created_at=raw_transaction["created_at"],
                account_id=None,
                raw_data="{}",
            )

        def extract_option_order(self, raw_tx, transaction_id):
            return None

        def extract_stock_order(self, raw_tx, transaction_id):
            return None

        def extract_option_legs(self, raw_tx, order_id):
            return []

        def extract_executions(self, raw_tx, transaction_id, leg_ids=None):
            return []

    monkeypatch.setattr(
        "tradedata.application.credentials.get_credentials", lambda source: ("u", "p")
    )

    stored = robinhood_sync.sync_transactions(storage=storage, adapter=Adapter())

    assert stored == []
    assert len(tx_repo.find_all()) == 1


class FakePositionAdapter:
    """Fake adapter for position sync flow."""

    def __init__(self):
        self.logged_in = False
        self.raw_positions = [
            {
                "symbol": "AAPL",
                "quantity": "10.0",
                "cost_basis": "150.0",
                "current_price": "155.0",
                "unrealized_pnl": "50.0",
                "last_updated": "2025-02-01T00:00:00Z",
                "account": "acc-123",
            },
            {
                "symbol": "MSFT",
                "quantity": "5.0",
                "cost_basis": "320.0",
                "current_price": "330.0",
                "unrealized_pnl": "50.0",
                "last_updated": "2025-02-02T00:00:00Z",
                "account_id": "acc-456",
            },
        ]

    def login(self, username: str, password: str) -> None:
        self.logged_in = True
        self.login_args = (username, password)

    def extract_positions(self):
        return self.raw_positions

    def normalize_position(self, raw_position):
        return Position(
            id=str(uuid.uuid4()),
            source="robinhood",
            account_id=raw_position.get("account_id") or raw_position.get("account"),
            symbol=raw_position["symbol"],
            quantity=float(raw_position["quantity"]),
            cost_basis=float(raw_position["cost_basis"]),
            current_price=float(raw_position["current_price"]),
            unrealized_pnl=float(raw_position["unrealized_pnl"]),
            last_updated=raw_position["last_updated"],
        )


def test_sync_positions_persists_positions(monkeypatch):
    """Sync positions end-to-end into storage."""
    storage = Storage(db_path=":memory:")
    adapter = FakePositionAdapter()
    monkeypatch.setattr(
        robinhood_sync.credentials,
        "get_credentials",
        lambda source: ("user", "pw"),
    )

    stored = robinhood_sync.sync_positions(storage=storage, adapter=adapter)

    assert adapter.logged_in
    assert len(stored) == len(adapter.raw_positions)

    repo = PositionRepository(storage)
    positions = repo.find_all()
    assert len(positions) == len(adapter.raw_positions)
    symbols = {p.symbol for p in positions}
    assert symbols == {"AAPL", "MSFT"}
    account_ids = {p.account_id for p in positions}
    assert account_ids == {"acc-123", "acc-456"}


def test_sync_positions_uses_factory_when_adapter_not_provided(monkeypatch):
    """Ensure factory creation and login are invoked for positions."""
    mock_adapter = MagicMock()
    mock_adapter.extract_positions.return_value = []

    def mock_get_credentials(source):
        return ("user", "pw")

    monkeypatch.setattr(robinhood_sync, "create_adapter", MagicMock(return_value=mock_adapter))
    monkeypatch.setattr(robinhood_sync.credentials, "get_credentials", mock_get_credentials)

    storage = Storage(db_path=":memory:")
    robinhood_sync.sync_positions(source="robinhood", storage=storage)

    robinhood_sync.create_adapter.assert_called_once_with("robinhood")
    mock_adapter.login.assert_called_once_with("user", "pw")
    mock_adapter.extract_positions.assert_called_once_with()


def test_sync_positions_raises_on_validation_failure(monkeypatch):
    """Fail fast when position validation errors occur."""
    bad_adapter = MagicMock()
    bad_adapter.extract_positions.return_value = [{"symbol": "bad"}]
    bad_adapter.normalize_position.return_value = Position(
        id=str(uuid.uuid4()),
        source="robinhood",
        account_id=None,
        symbol="bad",
        quantity=1.0,
        cost_basis=None,
        current_price=None,
        unrealized_pnl=None,
        last_updated="2025-02-01T00:00:00Z",
    )

    monkeypatch.setattr(robinhood_sync.credentials, "get_credentials", lambda source: ("u", "p"))
    monkeypatch.setattr(
        robinhood_sync, "validate_position", MagicMock(side_effect=ValidationError("boom"))
    )

    storage = Storage(db_path=":memory:")

    with pytest.raises(ValidationError):
        robinhood_sync.sync_positions(storage=storage, adapter=bad_adapter)

    assert PositionRepository(storage).find_all() == []
