"""Database schema definitions and initialization for trading data foundation."""

import os
import sqlite3
from pathlib import Path
from typing import Optional


def get_default_db_path() -> Path:
    """Get the default database path.

    Returns:
        Path to default database location: ~/.tradedata/trading.db
    """
    home = Path.home()
    return home / ".tradedata" / "trading.db"


def get_db_path(db_path: Optional[str] = None) -> str:
    """Get database path from parameter, environment variable, or default.

    Priority:
    1. db_path parameter (if provided)
    2. TRADEDATA_DB_PATH environment variable
    3. Default: ~/.tradedata/trading.db

    Args:
        db_path: Optional database path. If None, checks env var, then default.

    Returns:
        Database path as string (supports ':memory:' for in-memory database).
    """
    if db_path:
        return db_path

    env_path = os.getenv("TRADEDATA_DB_PATH")
    if env_path:
        return env_path

    default_path = get_default_db_path()
    return str(default_path)


def create_database_directory(db_path: str) -> None:
    """Create database directory if it doesn't exist.

    Args:
        db_path: Path to database file. If ':memory:', does nothing.
    """
    if db_path == ":memory:":
        return

    db_file = Path(db_path)
    db_dir = db_file.parent
    db_dir.mkdir(parents=True, exist_ok=True)


def get_schema_sql() -> str:
    """Get SQL schema for all tables.

    Returns:
        SQL string with CREATE TABLE statements for all 7 core tables.
    """
    return """
-- Core transactions table (unified across all sources)
CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    source_id TEXT NOT NULL,
    type TEXT NOT NULL,
    created_at TEXT NOT NULL,
    account_id TEXT,
    raw_data TEXT NOT NULL,
    UNIQUE(source, source_id)
);

-- Option orders table
CREATE TABLE IF NOT EXISTS option_orders (
    id TEXT PRIMARY KEY,
    chain_symbol TEXT NOT NULL,
    opening_strategy TEXT,
    closing_strategy TEXT,
    direction TEXT,
    premium REAL,
    net_amount REAL,
    FOREIGN KEY (id) REFERENCES transactions(id) ON DELETE CASCADE
);

-- Option legs table
CREATE TABLE IF NOT EXISTS option_legs (
    id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    strike_price REAL NOT NULL,
    expiration_date TEXT NOT NULL,
    option_type TEXT NOT NULL,
    side TEXT NOT NULL,
    position_effect TEXT NOT NULL,
    ratio_quantity INTEGER NOT NULL,
    FOREIGN KEY (order_id) REFERENCES option_orders(id) ON DELETE CASCADE
);

-- Executions table
CREATE TABLE IF NOT EXISTS executions (
    id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    leg_id TEXT,
    price REAL NOT NULL,
    quantity REAL NOT NULL,
    timestamp TEXT NOT NULL,
    settlement_date TEXT,
    FOREIGN KEY (order_id) REFERENCES transactions(id) ON DELETE CASCADE,
    FOREIGN KEY (leg_id) REFERENCES option_legs(id) ON DELETE SET NULL
);

-- Stock orders table
CREATE TABLE IF NOT EXISTS stock_orders (
    id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    quantity REAL NOT NULL,
    price REAL,
    average_price REAL,
    FOREIGN KEY (id) REFERENCES transactions(id) ON DELETE CASCADE
);

-- Positions table
CREATE TABLE IF NOT EXISTS positions (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    account_id TEXT,
    symbol TEXT NOT NULL,
    quantity REAL NOT NULL,
    cost_basis REAL,
    current_price REAL,
    unrealized_pnl REAL,
    last_updated TEXT NOT NULL
);

-- Transaction links table
CREATE TABLE IF NOT EXISTS transaction_links (
    id TEXT PRIMARY KEY,
    opening_transaction_id TEXT NOT NULL,
    closing_transaction_id TEXT NOT NULL,
    link_type TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (opening_transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
    FOREIGN KEY (closing_transaction_id) REFERENCES transactions(id) ON DELETE CASCADE
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_transactions_source ON transactions(source);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type);
CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_option_legs_order_id ON option_legs(order_id);
CREATE INDEX IF NOT EXISTS idx_executions_order_id ON executions(order_id);
CREATE INDEX IF NOT EXISTS idx_positions_source ON positions(source);
CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol);
CREATE INDEX IF NOT EXISTS idx_positions_account_id ON positions(account_id);
CREATE INDEX IF NOT EXISTS idx_transaction_links_opening
    ON transaction_links(opening_transaction_id);
CREATE INDEX IF NOT EXISTS idx_transaction_links_closing
    ON transaction_links(closing_transaction_id);
"""


def initialize_database(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Initialize the database with schema.

    Creates database directory if needed, creates all tables, and returns
    a connection to the database.

    Args:
        db_path: Optional database path. If None, uses get_db_path() logic.
                 Supports ':memory:' for in-memory database.

    Returns:
        SQLite connection to the initialized database.
    """
    path = get_db_path(db_path)
    create_database_directory(path)

    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints

    schema_sql = get_schema_sql()
    conn.executescript(schema_sql)

    return conn
