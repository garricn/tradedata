"""Tests for database schema and initialization."""

import os
import sqlite3
import tempfile
from pathlib import Path

from tradedata.data.schema import (
    get_db_path,
    get_default_db_path,
    get_schema_sql,
    initialize_database,
)


def test_get_default_db_path():
    """Test default database path is ~/.tradedata/trading.db."""
    path = get_default_db_path()
    assert path.name == "trading.db"
    assert path.parent.name == ".tradedata"
    assert path.parent.parent == Path.home()


def test_get_db_path_with_parameter():
    """Test db_path parameter takes priority."""
    custom_path = "/custom/path/db.db"
    result = get_db_path(db_path=custom_path)
    assert result == custom_path


def test_get_db_path_with_env_var(monkeypatch):
    """Test TRADEDATA_DB_PATH environment variable."""
    env_path = "/env/path/db.db"
    monkeypatch.setenv("TRADEDATA_DB_PATH", env_path)
    result = get_db_path()
    assert result == env_path


def test_get_db_path_parameter_overrides_env(monkeypatch):
    """Test db_path parameter overrides environment variable."""
    monkeypatch.setenv("TRADEDATA_DB_PATH", "/env/path/db.db")
    custom_path = "/custom/path/db.db"
    result = get_db_path(db_path=custom_path)
    assert result == custom_path


def test_get_db_path_default():
    """Test default path when no parameter or env var."""
    # Clear env var if it exists
    if "TRADEDATA_DB_PATH" in os.environ:
        del os.environ["TRADEDATA_DB_PATH"]
    result = get_db_path()
    expected = str(get_default_db_path())
    assert result == expected


def test_get_db_path_memory():
    """Test in-memory database path."""
    result = get_db_path(db_path=":memory:")
    assert result == ":memory:"


def test_initialize_database_in_memory():
    """Test database initialization with in-memory database."""
    conn = initialize_database(db_path=":memory:")
    assert isinstance(conn, sqlite3.Connection)

    # Verify tables exist
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """
    )
    tables = [row[0] for row in cursor.fetchall()]
    expected_tables = [
        "executions",
        "option_legs",
        "option_orders",
        "positions",
        "stock_orders",
        "transaction_links",
        "transactions",
    ]
    assert set(tables) == set(expected_tables)

    conn.close()


def test_initialize_database_file():
    """Test database initialization with file path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        conn = initialize_database(db_path=db_path)

        # Verify file was created
        assert os.path.exists(db_path)

        # Verify tables exist
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """
        )
        tables = [row[0] for row in cursor.fetchall()]
        expected_tables = [
            "executions",
            "option_legs",
            "option_orders",
            "positions",
            "stock_orders",
            "transaction_links",
            "transactions",
        ]
        assert set(tables) == set(expected_tables)

        conn.close()


def test_initialize_database_creates_directory():
    """Test that database directory is created if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "subdir", "nested", "test.db")
        conn = initialize_database(db_path=db_path)

        # Verify directory was created
        assert os.path.exists(os.path.dirname(db_path))
        assert os.path.exists(db_path)

        conn.close()


def test_foreign_keys_enabled():
    """Test that foreign key constraints are enabled."""
    conn = initialize_database(db_path=":memory:")
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys")
    result = cursor.fetchone()
    assert result[0] == 1  # Foreign keys should be enabled
    conn.close()


def test_schema_includes_indexes():
    """Test that schema includes indexes."""
    schema = get_schema_sql()
    assert "CREATE INDEX" in schema
    assert "idx_transactions_source" in schema
    assert "idx_transactions_type" in schema
    assert "idx_transactions_created_at" in schema


def test_transactions_table_structure():
    """Test transactions table has correct columns."""
    conn = initialize_database(db_path=":memory:")
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(transactions)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}
    assert "id" in columns
    assert "source" in columns
    assert "source_id" in columns
    assert "type" in columns
    assert "created_at" in columns
    assert "account_id" in columns
    assert "raw_data" in columns
    conn.close()


def test_option_orders_table_structure():
    """Test option_orders table has correct columns."""
    conn = initialize_database(db_path=":memory:")
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(option_orders)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}
    assert "id" in columns
    assert "chain_symbol" in columns
    assert "opening_strategy" in columns
    assert "closing_strategy" in columns
    assert "direction" in columns
    assert "premium" in columns
    assert "net_amount" in columns
    conn.close()
