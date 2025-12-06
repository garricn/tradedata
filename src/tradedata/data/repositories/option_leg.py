"""Repository for OptionLeg entities."""

from typing import Optional

from tradedata.data.models import OptionLeg
from tradedata.data.repositories.base import BaseRepository


class OptionLegRepository(BaseRepository[OptionLeg]):
    """Repository for OptionLeg entities."""

    def get_by_id(self, entity_id: str) -> Optional[OptionLeg]:
        """Get option leg by ID."""
        row = self.storage.fetchone(
            """
            SELECT id, order_id, strike_price, expiration_date, option_type,
                   side, position_effect, ratio_quantity
            FROM option_legs WHERE id = ?
            """,
            (entity_id,),
        )
        if row is None:
            return None
        return OptionLeg.from_db_row(row)

    def create(self, entity: OptionLeg, conn=None) -> OptionLeg:
        """Create a new option leg."""
        if conn is not None:
            conn.execute(
                """
                INSERT INTO option_legs
                    (id, order_id, strike_price, expiration_date, option_type,
                     side, position_effect, ratio_quantity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                entity.to_db_tuple(),
            )
            return entity

        with self.storage.transaction() as tx_conn:
            tx_conn.execute(
                """
                INSERT INTO option_legs
                    (id, order_id, strike_price, expiration_date, option_type,
                     side, position_effect, ratio_quantity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                entity.to_db_tuple(),
            )
        return entity

    def update(self, entity: OptionLeg, conn=None) -> OptionLeg:
        """Update an existing option leg."""
        params = (
            entity.order_id,
            entity.strike_price,
            entity.expiration_date,
            entity.option_type,
            entity.side,
            entity.position_effect,
            entity.ratio_quantity,
            entity.id,
        )
        if conn is not None:
            conn.execute(
                """
                UPDATE option_legs
                SET order_id = ?, strike_price = ?, expiration_date = ?,
                    option_type = ?, side = ?, position_effect = ?,
                    ratio_quantity = ?
                WHERE id = ?
                """,
                params,
            )
            return entity

        with self.storage.transaction() as tx_conn:
            tx_conn.execute(
                """
                UPDATE option_legs
                SET order_id = ?, strike_price = ?, expiration_date = ?,
                    option_type = ?, side = ?, position_effect = ?,
                    ratio_quantity = ?
                WHERE id = ?
                """,
                params,
            )
        return entity

    def delete(self, entity_id: str, conn=None) -> bool:
        """Delete an option leg by ID."""
        if conn is not None:
            cursor = conn.execute("DELETE FROM option_legs WHERE id = ?", (entity_id,))
            return bool(cursor.rowcount > 0)

        with self.storage.transaction() as tx_conn:
            cursor = tx_conn.execute("DELETE FROM option_legs WHERE id = ?", (entity_id,))
            return bool(cursor.rowcount > 0)

    def find_all(self) -> list[OptionLeg]:
        """Find all option legs."""
        rows = self.storage.fetchall(
            """
            SELECT id, order_id, strike_price, expiration_date, option_type,
                   side, position_effect, ratio_quantity
            FROM option_legs
            """
        )
        return [OptionLeg.from_db_row(row) for row in rows]

    def find_by_order_id(self, order_id: str) -> list[OptionLeg]:
        """Find option legs by order ID."""
        rows = self.storage.fetchall(
            """
            SELECT id, order_id, strike_price, expiration_date, option_type,
                   side, position_effect, ratio_quantity
            FROM option_legs WHERE order_id = ?
            """,
            (order_id,),
        )
        return [OptionLeg.from_db_row(row) for row in rows]
