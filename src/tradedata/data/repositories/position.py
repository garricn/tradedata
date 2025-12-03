"""Repository for Position entities."""

from typing import Optional

from tradedata.data.models import Position
from tradedata.data.repositories.base import BaseRepository


class PositionRepository(BaseRepository[Position]):
    """Repository for Position entities."""

    def get_by_id(self, entity_id: str) -> Optional[Position]:
        """Get position by ID."""
        row = self.storage.fetchone(
            """
            SELECT id, source, symbol, quantity, cost_basis, current_price,
                   unrealized_pnl, last_updated
            FROM positions WHERE id = ?
            """,
            (entity_id,),
        )
        if row is None:
            return None
        return Position.from_db_row(row)

    def create(self, entity: Position) -> Position:
        """Create a new position."""
        with self.storage.transaction() as conn:
            conn.execute(
                """
                INSERT INTO positions
                    (id, source, symbol, quantity, cost_basis, current_price,
                     unrealized_pnl, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                entity.to_db_tuple(),
            )
        return entity

    def update(self, entity: Position) -> Position:
        """Update an existing position."""
        with self.storage.transaction() as conn:
            conn.execute(
                """
                UPDATE positions
                SET source = ?, symbol = ?, quantity = ?, cost_basis = ?,
                    current_price = ?, unrealized_pnl = ?, last_updated = ?
                WHERE id = ?
                """,
                (
                    entity.source,
                    entity.symbol,
                    entity.quantity,
                    entity.cost_basis,
                    entity.current_price,
                    entity.unrealized_pnl,
                    entity.last_updated,
                    entity.id,
                ),
            )
        return entity

    def delete(self, entity_id: str) -> bool:
        """Delete a position by ID."""
        with self.storage.transaction() as conn:
            cursor = conn.execute("DELETE FROM positions WHERE id = ?", (entity_id,))
            return bool(cursor.rowcount > 0)

    def find_all(self) -> list[Position]:
        """Find all positions."""
        rows = self.storage.fetchall(
            """
            SELECT id, source, symbol, quantity, cost_basis, current_price,
                   unrealized_pnl, last_updated
            FROM positions
            """
        )
        return [Position.from_db_row(row) for row in rows]

    def find_by_source(self, source: str) -> list[Position]:
        """Find positions by source."""
        rows = self.storage.fetchall(
            """
            SELECT id, source, symbol, quantity, cost_basis, current_price,
                   unrealized_pnl, last_updated
            FROM positions WHERE source = ?
            """,
            (source,),
        )
        return [Position.from_db_row(row) for row in rows]
