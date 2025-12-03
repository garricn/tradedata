"""Tests for storage layer."""

import os
import sqlite3
import tempfile

from tradedata.data.schema import get_default_db_path
from tradedata.data.storage import Storage


def test_storage_default_path():
    """Test Storage uses default path when no parameter provided."""
    storage = Storage()
    expected = str(get_default_db_path())
    assert storage.db_path == expected
    storage.close()


def test_storage_custom_path():
    """Test Storage uses custom path when provided."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "custom.db")
        storage = Storage(db_path=db_path)
        assert storage.db_path == db_path
        storage.close()


def test_storage_env_var_path(monkeypatch):
    """Test Storage uses environment variable path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = os.path.join(tmpdir, "env.db")
        monkeypatch.setenv("TRADEDATA_DB_PATH", env_path)
        storage = Storage()
        assert storage.db_path == env_path
        storage.close()


def test_storage_parameter_overrides_env(monkeypatch):
    """Test Storage parameter overrides environment variable."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = os.path.join(tmpdir, "env.db")
        custom_path = os.path.join(tmpdir, "custom.db")
        monkeypatch.setenv("TRADEDATA_DB_PATH", env_path)
        storage = Storage(db_path=custom_path)
        assert storage.db_path == custom_path
        storage.close()


def test_storage_memory_database():
    """Test Storage with in-memory database."""
    storage = Storage(db_path=":memory:")
    assert storage.db_path == ":memory:"
    storage.close()


def test_storage_creates_directory():
    """Test Storage creates database directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "subdir", "nested", "test.db")
        storage = Storage(db_path=db_path)
        assert os.path.exists(os.path.dirname(db_path))
        storage.close()


def test_storage_connection():
    """Test Storage connection management."""
    storage = Storage(db_path=":memory:")
    conn = storage.connect()
    assert isinstance(conn, sqlite3.Connection)
    assert storage._connection is not None
    storage.close()
    assert storage._connection is None


def test_storage_context_manager():
    """Test Storage as context manager."""
    with Storage(db_path=":memory:") as storage:
        conn = storage.connect()
        assert isinstance(conn, sqlite3.Connection)
    # Connection should be closed after context
    assert storage._connection is None


def test_storage_transaction_commit():
    """Test transaction commits on success."""
    storage = Storage(db_path=":memory:")
    # Initialize schema
    storage.executescript("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT);")

    with storage.transaction() as conn:
        conn.execute("INSERT INTO test (name) VALUES (?)", ("test1",))
        conn.execute("INSERT INTO test (name) VALUES (?)", ("test2",))

    # Verify data was committed
    rows = storage.fetchall("SELECT name FROM test ORDER BY name")
    assert len(rows) == 2
    assert rows[0][0] == "test1"
    assert rows[1][0] == "test2"
    storage.close()


def test_storage_transaction_rollback():
    """Test transaction rolls back on exception."""
    storage = Storage(db_path=":memory:")
    # Initialize schema
    storage.executescript("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT);")

    try:
        with storage.transaction() as conn:
            conn.execute("INSERT INTO test (name) VALUES (?)", ("test1",))
            conn.execute("INSERT INTO test (name) VALUES (?)", ("test2",))
            # Force an error
            raise ValueError("Test error")
    except ValueError:
        pass

    # Verify data was rolled back
    rows = storage.fetchall("SELECT name FROM test")
    assert len(rows) == 0
    storage.close()


def test_storage_execute():
    """Test execute method."""
    storage = Storage(db_path=":memory:")
    storage.executescript("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT);")

    storage.execute("INSERT INTO test (name) VALUES (?)", ("test",))
    rows = storage.fetchall("SELECT name FROM test")
    assert len(rows) == 1
    assert rows[0][0] == "test"
    storage.close()


def test_storage_executemany():
    """Test executemany method."""
    storage = Storage(db_path=":memory:")
    storage.executescript("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT);")

    params = [("test1",), ("test2",), ("test3",)]
    storage.executemany("INSERT INTO test (name) VALUES (?)", params)
    rows = storage.fetchall("SELECT name FROM test ORDER BY name")
    assert len(rows) == 3
    assert rows[0][0] == "test1"
    assert rows[1][0] == "test2"
    assert rows[2][0] == "test3"
    storage.close()


def test_storage_executescript():
    """Test executescript method."""
    storage = Storage(db_path=":memory:")
    storage.executescript(
        """
        CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT);
        INSERT INTO test (name) VALUES ('test1');
        INSERT INTO test (name) VALUES ('test2');
        """
    )
    rows = storage.fetchall("SELECT name FROM test ORDER BY name")
    assert len(rows) == 2
    storage.close()


def test_storage_fetchone():
    """Test fetchone method."""
    storage = Storage(db_path=":memory:")
    storage.executescript(
        """
        CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT);
        INSERT INTO test (name) VALUES ('test1');
        INSERT INTO test (name) VALUES ('test2');
        """
    )

    row = storage.fetchone("SELECT name FROM test WHERE name = ?", ("test1",))
    assert row is not None
    assert row[0] == "test1"

    row = storage.fetchone("SELECT name FROM test WHERE name = ?", ("nonexistent",))
    assert row is None
    storage.close()


def test_storage_fetchall():
    """Test fetchall method."""
    storage = Storage(db_path=":memory:")
    storage.executescript(
        """
        CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT);
        INSERT INTO test (name) VALUES ('test1');
        INSERT INTO test (name) VALUES ('test2');
        INSERT INTO test (name) VALUES ('test3');
        """
    )

    rows = storage.fetchall("SELECT name FROM test ORDER BY name")
    assert len(rows) == 3
    assert rows[0][0] == "test1"
    assert rows[1][0] == "test2"
    assert rows[2][0] == "test3"
    storage.close()


def test_storage_lastrowid_from_cursor():
    """Test getting lastrowid from cursor after execute."""
    storage = Storage(db_path=":memory:")
    storage.executescript("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT);")

    cursor = storage.execute("INSERT INTO test (name) VALUES (?)", ("test",))
    rowid = cursor.lastrowid
    assert rowid is not None
    assert rowid == 1
    storage.close()


def test_storage_foreign_keys_enabled():
    """Test that foreign keys are enabled."""
    storage = Storage(db_path=":memory:")
    conn = storage.connect()
    cursor = conn.execute("PRAGMA foreign_keys")
    result = cursor.fetchone()
    assert result[0] == 1  # Foreign keys should be enabled
    storage.close()


def test_storage_initializes_database():
    """Test that Storage initializes database with schema."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        storage = Storage(db_path=db_path)

        # Verify tables exist
        tables = storage.fetchall(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        )
        table_names = [row[0] for row in tables]
        expected_tables = [
            "executions",
            "option_legs",
            "option_orders",
            "positions",
            "stock_orders",
            "transaction_links",
            "transactions",
        ]
        assert set(table_names) == set(expected_tables)
        storage.close()


def test_storage_multiple_transactions():
    """Test multiple transactions work correctly."""
    storage = Storage(db_path=":memory:")
    storage.executescript("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT);")

    # First transaction
    with storage.transaction() as conn:
        conn.execute("INSERT INTO test (name) VALUES (?)", ("test1",))

    # Second transaction
    with storage.transaction() as conn:
        conn.execute("INSERT INTO test (name) VALUES (?)", ("test2",))

    rows = storage.fetchall("SELECT name FROM test ORDER BY name")
    assert len(rows) == 2
    storage.close()


def test_storage_nested_transaction_rollback():
    """Test that nested transaction-like operations rollback correctly."""
    storage = Storage(db_path=":memory:")
    storage.executescript("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT);")

    # Outer transaction
    try:
        with storage.transaction() as conn:
            conn.execute("INSERT INTO test (name) VALUES (?)", ("test1",))
            # Inner operation that fails
            try:
                with storage.transaction() as conn2:
                    conn2.execute("INSERT INTO test (name) VALUES (?)", ("test2",))
                    raise ValueError("Inner error")
            except ValueError:
                pass
            # This should still be in outer transaction
            raise ValueError("Outer error")
    except ValueError:
        pass

    # All should be rolled back
    rows = storage.fetchall("SELECT name FROM test")
    assert len(rows) == 0
    storage.close()
