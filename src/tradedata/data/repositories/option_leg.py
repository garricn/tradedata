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

    def create(self, entity: OptionLeg) -> OptionLeg:
        """Create a new option leg."""
        with self.storage.transaction() as conn:
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

    def update(self, entity: OptionLeg) -> OptionLeg:
        """Update an existing option leg."""
        with self.storage.transaction() as conn:
            conn.execute(
                """
                UPDATE option_legs
                SET order_id = ?, strike_price = ?, expiration_date = ?,
                    option_type = ?, side = ?, position_effect = ?,
                    ratio_quantity = ?
                WHERE id = ?
                """,
                (
                    entity.order_id,
                    entity.strike_price,
                    entity.expiration_date,
                    entity.option_type,
                    entity.side,
                    entity.position_effect,
                    entity.ratio_quantity,
                    entity.id,
                ),
            )
        return entity

    def delete(self, entity_id: str) -> bool:
        """Delete an option leg by ID."""
        with self.storage.transaction() as conn:
            cursor = conn.execute("DELETE FROM option_legs WHERE id = ?", (entity_id,))
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
