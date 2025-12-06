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

    def create(self, entity: OptionOrder, conn=None) -> OptionOrder:
        """Create a new option order."""
        if conn is not None:
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

        with self.storage.transaction() as tx_conn:
            tx_conn.execute(
                """
                INSERT INTO option_orders
                    (id, chain_symbol, opening_strategy, closing_strategy,
                     direction, premium, net_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                entity.to_db_tuple(),
            )
        return entity

    def update(self, entity: OptionOrder, conn=None) -> OptionOrder:
        """Update an existing option order."""
        params = (
            entity.chain_symbol,
            entity.opening_strategy,
            entity.closing_strategy,
            entity.direction,
            entity.premium,
            entity.net_amount,
            entity.id,
        )
        if conn is not None:
            conn.execute(
                """
                UPDATE option_orders
                SET chain_symbol = ?, opening_strategy = ?, closing_strategy = ?,
                    direction = ?, premium = ?, net_amount = ?
                WHERE id = ?
                """,
                params,
            )
            return entity

        with self.storage.transaction() as tx_conn:
            tx_conn.execute(
                """
                UPDATE option_orders
                SET chain_symbol = ?, opening_strategy = ?, closing_strategy = ?,
                    direction = ?, premium = ?, net_amount = ?
                WHERE id = ?
                """,
                params,
            )
        return entity

    def delete(self, entity_id: str, conn=None) -> bool:
        """Delete an option order by ID."""
        if conn is not None:
            cursor = conn.execute("DELETE FROM option_orders WHERE id = ?", (entity_id,))
            return bool(cursor.rowcount > 0)

        with self.storage.transaction() as tx_conn:
            cursor = tx_conn.execute("DELETE FROM option_orders WHERE id = ?", (entity_id,))
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
