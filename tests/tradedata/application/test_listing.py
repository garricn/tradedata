"""Tests for application listing helpers."""

from datetime import datetime, timedelta, timezone

from tradedata.application import listing
from tradedata.data.models import OptionLeg, OptionOrder, Position, Transaction


def test_list_transactions_filters_by_type_and_days(monkeypatch):
    """Ensure list_transactions applies both type and recency filters."""
    now = datetime.now(timezone.utc)
    recent_tx = Transaction(
        id="tx-recent",
        source="robinhood",
        source_id="rh-1",
        type="stock",
        created_at=now.isoformat(),
        account_id=None,
        raw_data="{}",
    )
    old_tx = Transaction(
        id="tx-old",
        source="robinhood",
        source_id="rh-2",
        type="stock",
        created_at=(now - timedelta(days=30)).isoformat(),
        account_id=None,
        raw_data="{}",
    )

    class FakeRepo:
        def __init__(self, _storage=None):
            pass

        def find_all(self):
            return [recent_tx, old_tx]

        def find_by_type(self, _transaction_type):
            return [recent_tx, old_tx]

    class FakeStorage:
        def __init__(self, *args, **kwargs):
            pass

    monkeypatch.setattr(
        "tradedata.application.listing.TransactionRepository",
        FakeRepo,
    )
    monkeypatch.setattr(
        "tradedata.application.listing.Storage",
        FakeStorage,
    )

    result = listing.list_transactions(transaction_type="stock", days=10)

    assert result == [recent_tx]


def test_list_positions_returns_all(monkeypatch):
    """Ensure list_positions returns repository results."""
    position = Position(
        id="pos-1",
        source="robinhood",
        symbol="AAPL",
        quantity=10.0,
        cost_basis=150.0,
        current_price=155.0,
        unrealized_pnl=50.0,
        last_updated=datetime.now(timezone.utc).isoformat(),
    )

    class FakeRepo:
        def __init__(self, _storage=None):
            pass

        def find_all(self):
            return [position]

    class FakeStorage:
        def __init__(self, *args, **kwargs):
            pass

    monkeypatch.setattr(
        "tradedata.application.listing.PositionRepository",
        FakeRepo,
    )
    monkeypatch.setattr(
        "tradedata.application.listing.Storage",
        FakeStorage,
    )

    result = listing.list_positions()

    assert result == [position]


def test_list_transactions_last_applies_after_filters(monkeypatch):
    """Ensure list_transactions returns most recent N after filters."""
    now = datetime.now(timezone.utc)
    tx_new = Transaction(
        id="tx-new",
        source="robinhood",
        source_id="rh-new",
        type="stock",
        created_at=now.isoformat(),
        account_id=None,
        raw_data="{}",
    )
    tx_mid = Transaction(
        id="tx-mid",
        source="robinhood",
        source_id="rh-mid",
        type="stock",
        created_at=(now - timedelta(days=1)).isoformat(),
        account_id=None,
        raw_data="{}",
    )
    tx_old = Transaction(
        id="tx-old",
        source="robinhood",
        source_id="rh-old",
        type="stock",
        created_at=(now - timedelta(days=2)).isoformat(),
        account_id=None,
        raw_data="{}",
    )

    class FakeRepo:
        def __init__(self, _storage=None):
            pass

        def find_all(self):
            return [tx_old, tx_new, tx_mid]

    class FakeStorage:
        def __init__(self, *args, **kwargs):
            pass

    monkeypatch.setattr("tradedata.application.listing.TransactionRepository", FakeRepo)
    monkeypatch.setattr("tradedata.application.listing.Storage", FakeStorage)

    result = listing.list_transactions(transaction_type="stock", last=2)

    assert result == [tx_new, tx_mid]


def test_get_transaction_details_includes_raw_and_type_specific(monkeypatch):
    """Ensure transaction detail returns base, raw, and typed fields."""
    tx = Transaction(
        id="tx-1",
        source="robinhood",
        source_id="rh-1",
        type="option",
        created_at="2025-12-01T00:00:00Z",
        account_id="acc-1",
        raw_data='{"symbol":"AAPL","foo":"bar"}',
    )
    option_order = OptionOrder(
        id="tx-1",
        chain_symbol="AAPL",
        opening_strategy="call_buy",
        closing_strategy=None,
        direction="debit",
        premium=1.23,
        net_amount=-123.0,
    )
    leg = OptionLeg(
        id="leg-1",
        order_id="tx-1",
        strike_price=150.0,
        expiration_date="2025-12-19",
        option_type="call",
        side="buy",
        position_effect="open",
        ratio_quantity=1,
    )

    class FakeTxRepo:
        def __init__(self, _storage=None):
            pass

        def find_all(self):
            return [tx]

    class FakeOptionRepo:
        def __init__(self, _storage=None):
            pass

        def find_all(self):
            return [option_order]

    class FakeLegRepo:
        def __init__(self, _storage=None):
            pass

        def find_all(self):
            return [leg]

    class FakeStockRepo:
        def __init__(self, _storage=None):
            pass

        def find_all(self):
            return []

    class FakeStorage:
        def __init__(self, *args, **kwargs):
            pass

    monkeypatch.setattr("tradedata.application.listing.TransactionRepository", FakeTxRepo)
    monkeypatch.setattr("tradedata.application.listing.OptionOrderRepository", FakeOptionRepo)
    monkeypatch.setattr("tradedata.application.listing.OptionLegRepository", FakeLegRepo)
    monkeypatch.setattr("tradedata.application.listing.StockOrderRepository", FakeStockRepo)
    monkeypatch.setattr("tradedata.application.listing.Storage", FakeStorage)

    details = listing.get_transaction_details(ids=["tx-1"])

    assert len(details) == 1
    fields = dict(details[0].fields)
    assert fields["id"] == "tx-1"
    assert fields["raw.foo"] == "bar"
    assert fields["chain_symbol"] == "AAPL"
    assert fields["leg[0].strike_price"] == "150.0"
