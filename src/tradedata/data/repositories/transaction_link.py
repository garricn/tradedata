"""Repository for TransactionLink entities."""

from typing import Optional

from tradedata.data.models import TransactionLink
from tradedata.data.repositories.base import BaseRepository


class TransactionLinkRepository(BaseRepository[TransactionLink]):
    """Repository for TransactionLink entities."""

    def get_by_id(self, entity_id: str) -> Optional[TransactionLink]:
        """Get transaction link by ID."""
        row = self.storage.fetchone(
            """
            SELECT id, opening_transaction_id, closing_transaction_id, link_type, created_at
            FROM transaction_links WHERE id = ?
            """,
            (entity_id,),
        )
        if row is None:
            return None
        return TransactionLink.from_db_row(row)

    def create(self, entity: TransactionLink, conn=None) -> TransactionLink:
        """Create a new transaction link."""
        if conn is not None:
            conn.execute(
                """
                INSERT INTO transaction_links
                    (id, opening_transaction_id, closing_transaction_id,
                     link_type, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                entity.to_db_tuple(),
            )
            return entity

        with self.storage.transaction() as tx_conn:
            tx_conn.execute(
                """
                INSERT INTO transaction_links
                    (id, opening_transaction_id, closing_transaction_id,
                     link_type, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                entity.to_db_tuple(),
            )
        return entity

    def update(self, entity: TransactionLink, conn=None) -> TransactionLink:
        """Update an existing transaction link."""
        params = (
            entity.opening_transaction_id,
            entity.closing_transaction_id,
            entity.link_type,
            entity.created_at,
            entity.id,
        )
        if conn is not None:
            conn.execute(
                """
                UPDATE transaction_links
                SET opening_transaction_id = ?, closing_transaction_id = ?,
                    link_type = ?, created_at = ?
                WHERE id = ?
                """,
                params,
            )
            return entity

        with self.storage.transaction() as tx_conn:
            tx_conn.execute(
                """
                UPDATE transaction_links
                SET opening_transaction_id = ?, closing_transaction_id = ?,
                    link_type = ?, created_at = ?
                WHERE id = ?
                """,
                params,
            )
        return entity

    def delete(self, entity_id: str, conn=None) -> bool:
        """Delete a transaction link by ID."""
        if conn is not None:
            cursor = conn.execute("DELETE FROM transaction_links WHERE id = ?", (entity_id,))
            return bool(cursor.rowcount > 0)

        with self.storage.transaction() as tx_conn:
            cursor = tx_conn.execute("DELETE FROM transaction_links WHERE id = ?", (entity_id,))
            return bool(cursor.rowcount > 0)

    def find_all(self) -> list[TransactionLink]:
        """Find all transaction links."""
        rows = self.storage.fetchall(
            """
            SELECT id, opening_transaction_id, closing_transaction_id, link_type, created_at
            FROM transaction_links
            """
        )
        return [TransactionLink.from_db_row(row) for row in rows]

    def find_by_opening_transaction(self, opening_transaction_id: str) -> list[TransactionLink]:
        """Find transaction links by opening transaction ID."""
        rows = self.storage.fetchall(
            """
            SELECT id, opening_transaction_id, closing_transaction_id, link_type, created_at
            FROM transaction_links WHERE opening_transaction_id = ?
            """,
            (opening_transaction_id,),
        )
        return [TransactionLink.from_db_row(row) for row in rows]

    def find_by_closing_transaction(self, closing_transaction_id: str) -> list[TransactionLink]:
        """Find transaction links by closing transaction ID."""
        rows = self.storage.fetchall(
            """
            SELECT id, opening_transaction_id, closing_transaction_id, link_type, created_at
            FROM transaction_links WHERE closing_transaction_id = ?
            """,
            (closing_transaction_id,),
        )
        return [TransactionLink.from_db_row(row) for row in rows]
