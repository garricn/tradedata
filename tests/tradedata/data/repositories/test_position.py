"""Tests for PositionRepository."""

from tradedata.data.models import Position
from tradedata.data.repositories import PositionRepository
from tradedata.data.storage import Storage


class TestPositionRepository:
    """Tests for PositionRepository."""

    def test_create_and_get_by_id(self):
        """Test creating and retrieving a position."""
        storage = Storage(db_path=":memory:")
        repo = PositionRepository(storage)

        position = Position(
            id="pos-1",
            source="robinhood",
            symbol="AAPL",
            quantity=100.0,
            cost_basis=15000.0,
            current_price=155.0,
            unrealized_pnl=500.0,
            last_updated="2025-12-02T10:00:00Z",
        )

        created = repo.create(position)
        assert created.id == position.id

        retrieved = repo.get_by_id("pos-1")
        assert retrieved is not None
        assert retrieved.symbol == "AAPL"
        assert retrieved.quantity == 100.0

        storage.close()

    def test_find_by_source(self):
        """Test finding positions by source."""
        storage = Storage(db_path=":memory:")
        repo = PositionRepository(storage)

        pos1 = Position(
            id="pos-1",
            source="robinhood",
            symbol="AAPL",
            quantity=100.0,
            cost_basis=15000.0,
            current_price=155.0,
            unrealized_pnl=500.0,
            last_updated="2025-12-02T10:00:00Z",
        )
        pos2 = Position(
            id="pos-2",
            source="ibkr",
            symbol="TSLA",
            quantity=50.0,
            cost_basis=10000.0,
            current_price=200.0,
            unrealized_pnl=0.0,
            last_updated="2025-12-02T10:00:00Z",
        )

        repo.create(pos1)
        repo.create(pos2)

        robinhood_pos = repo.find_by_source("robinhood")
        assert len(robinhood_pos) == 1
        assert robinhood_pos[0].source == "robinhood"

        storage.close()
