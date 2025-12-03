"""Low-level SQLite storage operations with connection and transaction management."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from tradedata.data.schema import (
    create_database_directory,
    get_db_path,
    get_schema_sql,
)


class Storage:
    """Low-level SQLite storage with connection and transaction management.

    Provides:
    - Connection management
    - Transaction support with context managers
    - Automatic rollback on errors
    - Database path configuration (parameter, env var, default)
    - In-memory database support for testing
    - Automatic directory creation
    """

    def __init__(self, db_path: Optional[str] = None):
        """Initialize storage with database path.

        Args:
            db_path: Optional database path. If None, uses get_db_path() logic.
                    Supports ':memory:' for in-memory database.
        """
        self._db_path = get_db_path(db_path)
        self._connection: Optional[sqlite3.Connection] = None
        self._ensure_database_initialized()

    @property
    def db_path(self) -> str:
        """Get the database path.

        Returns:
            Database path string.
        """
        return self._db_path

    def _ensure_database_initialized(self) -> None:
        """Ensure database directory exists and database is initialized."""
        create_database_directory(self._db_path)

        # Initialize database if it doesn't exist or is empty
        # For in-memory, we'll initialize on first connect
        if self._db_path != ":memory:":
            db_file = Path(self._db_path)
            if not db_file.exists():
                # Create and initialize database
                conn = sqlite3.connect(self._db_path)
                conn.execute("PRAGMA foreign_keys = ON")
                conn.executescript(get_schema_sql())
                conn.close()

    def connect(self) -> sqlite3.Connection:
        """Get or create a database connection.

        Returns:
            SQLite connection. Connection has foreign keys enabled.
        """
        if self._connection is None:
            self._connection = sqlite3.connect(self._db_path)
            self._connection.execute("PRAGMA foreign_keys = ON")
            # Initialize schema for in-memory databases
            if self._db_path == ":memory:":
                self._connection.executescript(get_schema_sql())
        return self._connection

    def close(self) -> None:
        """Close the database connection."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __enter__(self) -> "Storage":
        """Context manager entry - returns self."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - closes connection."""
        self.close()

    @contextmanager
    def transaction(self):
        """Context manager for database transactions.

        Automatically commits on success, rolls back on exception.

        Yields:
            SQLite connection for use within transaction.

        Example:
            with storage.transaction() as conn:
                conn.execute("INSERT INTO ...")
                conn.execute("UPDATE ...")
        """
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def execute(self, sql: str, parameters: tuple = ()) -> sqlite3.Cursor:
        """Execute a single SQL statement.

        Args:
            sql: SQL statement to execute.
            parameters: Optional parameters for parameterized query.

        Returns:
            Cursor with results. Use cursor.lastrowid to get inserted row ID.
        """
        conn = self.connect()
        return conn.execute(sql, parameters)

    def executemany(self, sql: str, parameters: list[tuple]) -> sqlite3.Cursor:
        """Execute SQL statement multiple times with different parameters.

        Args:
            sql: SQL statement to execute.
            parameters: List of parameter tuples.

        Returns:
            Cursor with results.
        """
        conn = self.connect()
        return conn.executemany(sql, parameters)

    def executescript(self, sql: str) -> None:
        """Execute multiple SQL statements.

        Args:
            sql: SQL script with multiple statements.
        """
        conn = self.connect()
        conn.executescript(sql)

    def fetchone(self, sql: str, parameters: tuple = ()) -> Optional[tuple]:
        """Execute query and fetch one row.

        Args:
            sql: SQL query.
            parameters: Optional parameters for parameterized query.

        Returns:
            Single row tuple, or None if no results.
        """
        cursor = self.execute(sql, parameters)
        result = cursor.fetchone()
        if result is None:
            return None
        return tuple(result)

    def fetchall(self, sql: str, parameters: tuple = ()) -> list[tuple]:
        """Execute query and fetch all rows.

        Args:
            sql: SQL query.
            parameters: Optional parameters for parameterized query.

        Returns:
            List of row tuples.
        """
        cursor = self.execute(sql, parameters)
        return cursor.fetchall()
