"""Repository for OptionOrder entities."""

from typing import Optional

from tradedata.data.models import OptionOrder
from tradedata.data.repositories.base import BaseRepository


class OptionOrderRepository(BaseRepository[OptionOrder]):
    """Repository for OptionOrder entities."""

    def get_by_id(self, entity_id: str) -> Optional[OptionOrder]:
        """Get option order by ID."""
        row = self.storage.fetchone(
            """
            SELECT id, chain_symbol, opening_strategy, closing_strategy,
                   direction, premium, net_amount
            FROM option_orders WHERE id = ?
            """,
            (entity_id,),
        )
        if row is None:
            return None
        return OptionOrder.from_db_row(row)

    def create(self, entity: OptionOrder) -> OptionOrder:
        """Create a new option order."""
        with self.storage.transaction() as conn:
            conn.execute(
                """
                INSERT INTO option_orders
                    (id, chain_symbol, opening_strategy, closing_strategy,
                     direction, premium, net_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                entity.to_db_tuple(),
            )
        return entity

    def update(self, entity: OptionOrder) -> OptionOrder:
        """Update an existing option order."""
        with self.storage.transaction() as conn:
            conn.execute(
                """
                UPDATE option_orders
                SET chain_symbol = ?, opening_strategy = ?, closing_strategy = ?,
                    direction = ?, premium = ?, net_amount = ?
                WHERE id = ?
                """,
                (
                    entity.chain_symbol,
                    entity.opening_strategy,
                    entity.closing_strategy,
                    entity.direction,
                    entity.premium,
                    entity.net_amount,
                    entity.id,
                ),
            )
        return entity

    def delete(self, entity_id: str) -> bool:
        """Delete an option order by ID."""
        with self.storage.transaction() as conn:
            cursor = conn.execute("DELETE FROM option_orders WHERE id = ?", (entity_id,))
            return bool(cursor.rowcount > 0)

    def find_all(self) -> list[OptionOrder]:
        """Find all option orders."""
        rows = self.storage.fetchall(
            """
            SELECT id, chain_symbol, opening_strategy, closing_strategy,
                   direction, premium, net_amount
            FROM option_orders
            """
        )
        return [OptionOrder.from_db_row(row) for row in rows]
