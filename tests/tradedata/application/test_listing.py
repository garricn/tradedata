"""Tests for application listing helpers."""

from datetime import datetime, timedelta, timezone

from tradedata.application import listing
from tradedata.data.models import Position, Transaction


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
