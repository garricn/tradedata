"""Repository for Transaction entities."""

from typing import Optional

from tradedata.data.models import Transaction
from tradedata.data.repositories.base import BaseRepository


class TransactionRepository(BaseRepository[Transaction]):
    """Repository for Transaction entities."""

    def exists_by_source_id(self, source: str, source_id: str) -> bool:
        """Check if a transaction exists for a given source/source_id."""
        row = self.storage.fetchone(
            """
            SELECT 1 FROM transactions WHERE source = ? AND source_id = ? LIMIT 1
            """,
            (source, source_id),
        )
        return row is not None

    def get_by_id(self, entity_id: str) -> Optional[Transaction]:
        """Get transaction by ID."""
        row = self.storage.fetchone(
            """
            SELECT id, source, source_id, type, created_at, account_id, raw_data
            FROM transactions WHERE id = ?
            """,
            (entity_id,),
        )
        if row is None:
            return None
        return Transaction.from_db_row(row)

    def create(self, entity: Transaction, conn=None) -> Transaction:
        """Create a new transaction."""
        if conn is not None:
            conn.execute(
                """
                INSERT INTO transactions
                    (id, source, source_id, type, created_at, account_id, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                entity.to_db_tuple(),
            )
            return entity

        with self.storage.transaction() as tx_conn:
            tx_conn.execute(
                """
                INSERT INTO transactions
                    (id, source, source_id, type, created_at, account_id, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                entity.to_db_tuple(),
            )
        return entity

    def update(self, entity: Transaction, conn=None) -> Transaction:
        """Update an existing transaction."""
        params = (
            entity.source,
            entity.source_id,
            entity.type,
            entity.created_at,
            entity.account_id,
            entity.raw_data,
            entity.id,
        )
        if conn is not None:
            conn.execute(
                """
                UPDATE transactions
                SET source = ?, source_id = ?, type = ?, created_at = ?,
                    account_id = ?, raw_data = ?
                WHERE id = ?
                """,
                params,
            )
            return entity

        with self.storage.transaction() as tx_conn:
            tx_conn.execute(
                """
                UPDATE transactions
                SET source = ?, source_id = ?, type = ?, created_at = ?,
                    account_id = ?, raw_data = ?
                WHERE id = ?
                """,
                params,
            )
        return entity

    def delete(self, entity_id: str, conn=None) -> bool:
        """Delete a transaction by ID."""
        if conn is not None:
            cursor = conn.execute("DELETE FROM transactions WHERE id = ?", (entity_id,))
            return bool(cursor.rowcount > 0)

        with self.storage.transaction() as tx_conn:
            cursor = tx_conn.execute("DELETE FROM transactions WHERE id = ?", (entity_id,))
            return bool(cursor.rowcount > 0)

    def find_all(self) -> list[Transaction]:
        """Find all transactions."""
        rows = self.storage.fetchall(
            """
            SELECT id, source, source_id, type, created_at, account_id, raw_data
            FROM transactions
            """
        )
        return [Transaction.from_db_row(row) for row in rows]

    def find_by_source(self, source: str) -> list[Transaction]:
        """Find transactions by source."""
        rows = self.storage.fetchall(
            """
            SELECT id, source, source_id, type, created_at, account_id, raw_data
            FROM transactions WHERE source = ?
            """,
            (source,),
        )
        return [Transaction.from_db_row(row) for row in rows]

    def find_by_type(self, transaction_type: str) -> list[Transaction]:
        """Find transactions by type."""
        rows = self.storage.fetchall(
            """
            SELECT id, source, source_id, type, created_at, account_id, raw_data
            FROM transactions WHERE type = ?
            """,
            (transaction_type,),
        )
        return [Transaction.from_db_row(row) for row in rows]
