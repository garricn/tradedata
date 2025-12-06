"""Repository for Execution entities."""

from typing import Optional

from tradedata.data.models import Execution
from tradedata.data.repositories.base import BaseRepository


class ExecutionRepository(BaseRepository[Execution]):
    """Repository for Execution entities."""

    def get_by_id(self, entity_id: str) -> Optional[Execution]:
        """Get execution by ID."""
        row = self.storage.fetchone(
            """
            SELECT id, order_id, leg_id, price, quantity, timestamp, settlement_date
            FROM executions WHERE id = ?
            """,
            (entity_id,),
        )
        if row is None:
            return None
        return Execution.from_db_row(row)

    def create(self, entity: Execution, conn=None) -> Execution:
        """Create a new execution."""
        if conn is not None:
            conn.execute(
                """
                INSERT INTO executions
                    (id, order_id, leg_id, price, quantity, timestamp, settlement_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                entity.to_db_tuple(),
            )
            return entity

        with self.storage.transaction() as tx_conn:
            tx_conn.execute(
                """
                INSERT INTO executions
                    (id, order_id, leg_id, price, quantity, timestamp, settlement_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                entity.to_db_tuple(),
            )
        return entity

    def update(self, entity: Execution, conn=None) -> Execution:
        """Update an existing execution."""
        params = (
            entity.order_id,
            entity.leg_id,
            entity.price,
            entity.quantity,
            entity.timestamp,
            entity.settlement_date,
            entity.id,
        )
        if conn is not None:
            conn.execute(
                """
                UPDATE executions
                SET order_id = ?, leg_id = ?, price = ?, quantity = ?,
                    timestamp = ?, settlement_date = ?
                WHERE id = ?
                """,
                params,
            )
            return entity

        with self.storage.transaction() as tx_conn:
            tx_conn.execute(
                """
                UPDATE executions
                SET order_id = ?, leg_id = ?, price = ?, quantity = ?,
                    timestamp = ?, settlement_date = ?
                WHERE id = ?
                """,
                params,
            )
        return entity

    def delete(self, entity_id: str, conn=None) -> bool:
        """Delete an execution by ID."""
        if conn is not None:
            cursor = conn.execute("DELETE FROM executions WHERE id = ?", (entity_id,))
            return bool(cursor.rowcount > 0)

        with self.storage.transaction() as tx_conn:
            cursor = tx_conn.execute("DELETE FROM executions WHERE id = ?", (entity_id,))
            return bool(cursor.rowcount > 0)

    def find_all(self) -> list[Execution]:
        """Find all executions."""
        rows = self.storage.fetchall(
            """
            SELECT id, order_id, leg_id, price, quantity, timestamp, settlement_date
            FROM executions
            """
        )
        return [Execution.from_db_row(row) for row in rows]

    def find_by_order_id(self, order_id: str) -> list[Execution]:
        """Find executions by order ID."""
        rows = self.storage.fetchall(
            """
            SELECT id, order_id, leg_id, price, quantity, timestamp, settlement_date
            FROM executions WHERE order_id = ?
            """,
            (order_id,),
        )
        return [Execution.from_db_row(row) for row in rows]
