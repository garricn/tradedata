"""Repository for StockOrder entities."""

from typing import Optional

from tradedata.data.models import StockOrder
from tradedata.data.repositories.base import BaseRepository


class StockOrderRepository(BaseRepository[StockOrder]):
    """Repository for StockOrder entities."""

    def get_by_id(self, entity_id: str) -> Optional[StockOrder]:
        """Get stock order by ID."""
        row = self.storage.fetchone(
            """
            SELECT id, symbol, side, quantity, price, average_price
            FROM stock_orders WHERE id = ?
            """,
            (entity_id,),
        )
        if row is None:
            return None
        return StockOrder.from_db_row(row)

    def create(self, entity: StockOrder, conn=None) -> StockOrder:
        """Create a new stock order."""
        if conn is not None:
            conn.execute(
                """
                INSERT INTO stock_orders (id, symbol, side, quantity, price, average_price)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                entity.to_db_tuple(),
            )
            return entity

        with self.storage.transaction() as tx_conn:
            tx_conn.execute(
                """
                INSERT INTO stock_orders (id, symbol, side, quantity, price, average_price)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                entity.to_db_tuple(),
            )
        return entity

    def update(self, entity: StockOrder, conn=None) -> StockOrder:
        """Update an existing stock order."""
        params = (
            entity.symbol,
            entity.side,
            entity.quantity,
            entity.price,
            entity.average_price,
            entity.id,
        )
        if conn is not None:
            conn.execute(
                """
                UPDATE stock_orders
                SET symbol = ?, side = ?, quantity = ?, price = ?, average_price = ?
                WHERE id = ?
                """,
                params,
            )
            return entity

        with self.storage.transaction() as tx_conn:
            tx_conn.execute(
                """
                UPDATE stock_orders
                SET symbol = ?, side = ?, quantity = ?, price = ?, average_price = ?
                WHERE id = ?
                """,
                params,
            )
        return entity

    def delete(self, entity_id: str, conn=None) -> bool:
        """Delete a stock order by ID."""
        if conn is not None:
            cursor = conn.execute("DELETE FROM stock_orders WHERE id = ?", (entity_id,))
            return bool(cursor.rowcount > 0)

        with self.storage.transaction() as tx_conn:
            cursor = tx_conn.execute("DELETE FROM stock_orders WHERE id = ?", (entity_id,))
            return bool(cursor.rowcount > 0)

    def find_all(self) -> list[StockOrder]:
        """Find all stock orders."""
        rows = self.storage.fetchall(
            """
            SELECT id, symbol, side, quantity, price, average_price
            FROM stock_orders
            """
        )
        return [StockOrder.from_db_row(row) for row in rows]
