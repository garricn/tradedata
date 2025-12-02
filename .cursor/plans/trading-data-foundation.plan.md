# Trading Data Foundation Plan

## Project Overview

**Project Name:** `TradeData`

**Purpose:** Unified trading data foundation layer that:

- Extracts and normalizes data from multiple brokers/data sources
- Enriches transactions with market data (Greeks, IV, technicals)
- Provides source of truth storage with validation
- Exports clean, normalized data for analytics and other tools

**Key Principle:** This is the **single source of truth** for all trading data. All other projects consume from here.

______________________________________________________________________

## Value Proposition: Why Not Just Use `robin_stocks` Directly?

### What `robin_stocks` Provides:

- Direct API access to Robinhood
- Raw transaction data
- Current market data
- Real-time quotes

### What This Project Adds:

**1. Historical Data Enrichment (The Big One)**

- `robin_stocks` gives you current market data, but **not historical snapshots**

- This project fetches and stores market data **at exact trade timestamps**:

  - What were the Greeks when you opened that spread?
  - What was the IV when you sold that put?
  - What was the RSI when you entered that day trade?

- **You can't get this from `robin_stocks` directly** - it only provides current data

**2. Persistent Storage & Caching**

- `robin_stocks` requires API calls every time
- This project stores data locally (SQLite)
- Fast queries without hitting API
- Works offline once data is synced
- Reduces API rate limiting issues

**3. Data Normalization & Validation**

- `robin_stocks` returns raw API responses (inconsistent formats)
- This project normalizes to consistent schema
- Validates data integrity
- Handles edge cases and missing data

**4. Multi-Source Support (Future)**

- `robin_stocks` is Robinhood-only
- This project will support multiple brokers
- Unified interface regardless of source
- Aggregate data from multiple accounts

**5. Analytics-Ready Data**

- Pre-processed and enriched data
- **Transaction Linking:** This project provides basic transaction linking (entries → exits) based on simple matching (symbol, strategy type, timing window). Links are stored in `transaction_links` table. **Design:** Optional (clients can ignore), overridable (clients can add/modify links), simple initially (basic matching logic). Clients can implement custom linking logic if needed.
- Position tracking and P&L calculations
- Ready for performance analysis

**6. Time-Series Analysis**

- Historical snapshots enable:

  - "What conditions led to my best trades?"
  - "What IV rank works best for my strategy?"
  - "What technical indicators predicted my winners?"

**Example Use Case:**

```python
# With robin_stocks directly:
# - Get transaction: "I sold a put on 2025-11-21"
# - Want to know: What was the IV at that time?
# - Problem: Can't get historical IV, only current IV

# With TradeData:
transaction = query.get_transaction(id)
enriched = transaction.enriched_data
print(enriched.iv_at_trade_time)  # 0.35 (stored from trade time)
print(enriched.greeks_at_trade_time)  # {delta: -0.25, theta: 0.05, ...}
print(enriched.rsi_at_trade_time)  # 45.2
```

**Bottom Line:** If you only need current market data and don't care about historical analysis, use `robin_stocks` directly. If you want to analyze your trading performance with historical context (Greeks, IV, technicals at trade time), this project is essential.

______________________________________________________________________

## Architecture

### Project Type

**Primary:** Python library/package that can be imported by other projects

**Secondary:** CLI tool for direct user interaction

**Not:** Backend server (that would be a separate project)

**Design Pattern:**

- Core functionality as importable Python modules
- CLI as thin wrapper around library functions
- Other projects (web app, MCP server) import and use the library
- Can be installed via pip: `pip install tradedata`

**Database Architecture:**

The library manages its own database internally. Clients **never access the database directly** - they use the library's Python API.

**How it works:**

1. Library manages SQLite database (default: `~/.tradedata/trading.db` or configurable)

1. Clients interact through library functions, not SQL

1. Database location can be configured via:

   ```
        - Constructor parameter: `DataStore(db_path="/path/to/db.db")`
        - Environment variable: `TRADEDATA_DB_PATH`
        - Config file: `~/.tradedata/config.yaml` (future)
   ```

1. Library abstracts all database operations

**Client Usage Pattern:**

```python
# Client project imports the library
from tradedata import DataStore, sync, enrich, query

# Initialize with optional database path
# (defaults to ~/.tradedata/trading.db if not specified, or TRADEDATA_DB_PATH env var)
store = DataStore(db_path="/path/to/shared/db.db")  # Optional: share DB
# OR
store = DataStore()  # Uses default location or TRADATA_DB_PATH env var

# Clients use library API, not direct DB access
transactions = store.sync_from_robinhood()
enriched = store.enrich_transactions(transactions)
results = store.query_transactions(type="option", days=30)

# Data is returned as Python objects, not raw SQL
for tx in results:
    print(tx.symbol, tx.enriched_data.iv_at_trade_time)
```

**Database Sharing Options:**

1. **Separate databases (default):** Each project has its own DB

- `rhmonitor` → `~/.rhmonitor/trading.db`
- `web-app` → `~/.web-app/trading.db`
- `TradeData` → `~/.tradedata/trading.db` (default)

2. **Shared database (optional):** Configure same path

- `rhmonitor` → `/shared/data/trading.db`
- `web-app` → `/shared/data/trading.db` (same file)

3. **In-memory (for testing):** `DataStore(db_path=":memory:")`

**Key Point:** Clients don't write SQL or access the database directly. They use the library's API which handles all database operations internally.

### Data Sources (Multi-Source Support)

**Phase 1 (Immediate):**

- Robinhood API (via `robin_stocks`)
- Transactions (stocks, options, crypto, dividends, transfers)
- Current positions
- Account information

**Phase 2 (Future):**

- Other brokers (IBKR, TD Ameritrade, etc.)
- Market data providers (Alpha Vantage, Polygon, Yahoo Finance)
- Manual imports (CSV, Excel)

**Design:** Plugin-based architecture - each data source is a separate module that implements a common interface.

### Stored vs Computed Data

**MUST STORE (Source Data - Cannot be Recomputed):**

- All transaction data (from brokers)
- All position data (from brokers)
- Market data snapshots at trade time:
  - Greeks (delta, gamma, theta, vega) at exact timestamp
  - Implied volatility at exact timestamp
  - Underlying stock price at exact timestamp
  - Option chain data at exact timestamp

**SHOULD STORE (Computed but Expensive/Historical):**

- Technical indicators at trade timestamp (RSI, MACD, EMA, etc.)
  - **Reason:** Historical accuracy - what was RSI at trade time
  - **Reason:** Performance - don't recalculate every query
  - **Reason:** Consistency - same calculation method preserved

**CAN COMPUTE (On-Demand):**

- Current technical indicators (for real-time monitoring)
- Performance metrics (P&L, win rate, etc.) - computed from stored data
- Aggregations and summaries

**Storage Strategy:**

- Store historical snapshots (at trade time) in `enriched_data` table
- Provide computation functions for on-demand calculations
- Cache computed values when appropriate
- Allow users to choose: use stored or recompute

**Example:**

```python
# Stored: RSI at trade time (2025-11-21 20:25:59)
enriched_data.rsi_at_trade_time = 45.2

# Computed: Current RSI (for real-time monitoring)
current_rsi = calculate_rsi(symbol, timeframe='1min')
```

______________________________________________________________________

## Phase 1: Core Data Infrastructure

### 1.1 Data Normalization & Storage

**Goal:** Create unified schema that works across all data sources

**Files:**

- `src/data/schema.py` - Database schema definitions
- `src/data/models.py` - Python data models (dataclasses/Pydantic)
- `src/data/normalize.py` - Normalization logic
- `src/data/storage.py` - SQLite operations (low-level)
- `src/data/repository.py` - Repository pattern for data access
- `src/data/validator.py` - Data validation

**Database Schema:**

```python
# Core tables (unified across all sources):
- transactions
 - id (UUID, primary key)
 - source (robinhood, ibkr, etc.)
 - source_id (original ID from source)
 - type (stock, option, crypto, dividend, transfer)
 - created_at (ISO timestamp)
 - account_id
 - raw_data (JSON blob of original data)

- option_orders
 - id (UUID, foreign key to transactions)
 - chain_symbol
 - opening_strategy
 - closing_strategy
 - direction (debit/credit)
 - premium
 - net_amount

- option_legs
 - id (UUID)
 - order_id (foreign key to option_orders)
 - strike_price
 - expiration_date
 - option_type (call/put)
 - side (buy/sell)
 - position_effect (open/close)
 - ratio_quantity

- executions
 - id (UUID)
 - order_id (foreign key)
 - leg_id (foreign key, nullable)
 - price
 - quantity
 - timestamp (ISO)
 - settlement_date

- stock_orders
 - id (UUID, foreign key to transactions)
 - symbol
 - side (buy/sell)
 - quantity
 - price
 - average_price

- positions
 - id (UUID)
 - source
 - symbol (or option identifier)
 - quantity
 - cost_basis
 - current_price (cached)
 - unrealized_pnl
 - last_updated

- enriched_data
 - transaction_id (foreign key)
 - timestamp (when enrichment was done)
 - greeks (JSON: delta, gamma, theta, vega)
 - implied_volatility
 - underlying_price
 - technical_indicators (JSON: RSI, MACD, EMA, etc.)

- transaction_links
 - id (UUID)
 - opening_transaction_id (foreign key to transactions)
 - closing_transaction_id (foreign key to transactions)
 - link_type (spread, covered_call, etc.)
 - created_at (when link was established)
```

**Data Models:**

- Use Python `dataclasses` or `Pydantic` models to represent database entities in memory
- Models map 1:1 with database tables (Transaction, OptionOrder, OptionLeg, etc.)
- Type-safe data structures for all operations
- Models handle serialization/deserialization to/from database
- Example: `Transaction`, `OptionOrder`, `OptionLeg`, `EnrichedData`, etc.

**Repository Pattern:**

- Repository layer abstracts database operations from business logic
- Each entity type has a repository (TransactionRepository, OptionOrderRepository, etc.)
- Repositories provide clean, typed API for CRUD operations
- Benefits: testability (easy to mock), separation of concerns, consistent interface
- Example: `TransactionRepository.get_by_id()`, `TransactionRepository.create()`, etc.

**Transaction Management:**

- Use SQLite transactions for multi-step operations (e.g., inserting transaction + legs + executions)
- Context managers for automatic rollback on errors
- All related inserts/updates wrapped in single transaction for data integrity
- Example: Creating an option order with multiple legs must be atomic

**Normalization Strategy:**

- Each data source has an adapter that converts to unified schema
- Preserve original data in `raw_data` JSON field
- Extract common fields to normalized columns
- Validate data integrity (required fields, data types, constraints)

### 1.2 Data Source Adapters

**Files:**

- `src/sources/base.py` - Abstract base class for data sources
- `src/sources/robinhood.py` - Robinhood adapter
- `src/sources/factory.py` - Source factory pattern

**Adapter Interface:**

```python
class DataSourceAdapter(ABC):
    @abstractmethod
    def extract_transactions(self, start_date=None, end_date=None):
        """Extract transactions from source"""
        pass

    @abstractmethod
    def extract_positions(self):
        """Extract current positions"""
        pass

    @abstractmethod
    def normalize_transaction(self, raw_transaction):
        """Convert source-specific format to unified schema"""
        pass
```

**Robinhood Adapter:**

- Uses existing `extract_transactions_api.py` logic
- Converts Robinhood JSON to unified schema
- Handles multi-leg options, executions, etc.

### 1.3 Data Validation

**File:** `src/data/validator.py`

**Validation Rules:**

- Required fields present
- Data types correct (timestamps, decimals, etc.)
- Referential integrity (legs reference orders, etc.)
- Business logic (e.g., option legs have strike/expiration)
- Duplicate detection (same transaction from multiple sources)
- Data freshness checks

**Error Handling:** Fail loud, hard, and fast. Validation failures raise exceptions immediately. No graceful degradation during initial development.

______________________________________________________________________

## Phase 2: Data Enrichment

### 2.1 Enrichment Pipeline

**File:** `src/enrichment/enricher.py`

**Enrichment Process:**

1. Identify transactions that need enrichment (options, stocks)

1. For each transaction, fetch market data at exact timestamp:

   ```
        - Option chain data → Greeks, IV
        - Historical stock data → Technical indicators
   ```

1. Store enriched data in `enriched_data` table

1. **Error Handling:** Fail loud, hard, and fast. No graceful error handling during initial development. If enrichment fails, raise exception immediately.

**Enrichment Sources:**

- Option Greeks: `robin_stocks.options.get_option_market_data()`
- Historical stock data: `robin_stocks.stocks.get_historicals()`
- Technical indicators: Calculate from historical data (pandas-ta or ta-lib)

### 2.2 Greeks Fetcher

**File:** `src/enrichment/greeks.py`

- Fetch option chain data at specific timestamp
- Extract Greeks (delta, gamma, theta, vega) for exact contract
- **Error Handling:** If historical data unavailable, raise exception (fail fast)
- Cache results to avoid re-fetching
- **Re-enrichment:** Allow re-enriching transactions (overwrite existing enriched data) - useful if we add new indicators or improve enrichment logic

### 2.3 Technical Indicators

**File:** `src/enrichment/technicals.py`

- Calculate RSI, MACD, EMA, etc. from historical price data
- Support multiple timeframes (1min, 5min, daily, etc.)
- Store indicators at trade timestamp

### 2.4 IV Fetcher

**File:** `src/enrichment/iv.py`

- Extract implied volatility from option chain data
- Calculate IV rank/percentile if possible
- Store IV at trade timestamp

______________________________________________________________________

## Phase 3: Data Sync & Updates

### 3.1 Incremental Sync

**File:** `src/sync/syncer.py`

- Track last sync timestamp per data source
- Only fetch new/updated transactions since last sync
- Handle full sync vs incremental sync
- Detect and resolve conflicts (same transaction from multiple sources)
- **Note:** Sync and enrichment are separate operations. Sync fetches raw data, enrichment happens separately.

### 3.2 Position Updates

**File:** `src/positions/tracker.py`

- Fetch current positions from sources
- Update position table
- Calculate unrealized P&L
- Track position lifecycle (open → close)

______________________________________________________________________

## Phase 4: Data Export & APIs

### 4.1 Export Functions

**File:** `src/export/exporters.py`

**Export Formats:**

- CSV (for Excel analysis)
- JSON (for other tools)
- SQL dump (for backup/migration)
- Parquet (for data science workflows)

**Export Options:**

- Filter by date range, transaction type, symbol
- Include/exclude enriched data
- Include/exclude raw data

### 4.2 Transaction Linking

**File:** `src/linking/linker.py`

**Purpose:** Provide basic transaction linking (entries → exits) to make data analytics-ready.

**Design Principles:**

- **Optional:** Clients can ignore links entirely
- **Overridable:** Clients can add, modify, or delete links via API
- **Simple initially:** Basic matching logic (symbol, strategy type, timing window)

**Linking Logic (Initial):**

- Match opening and closing transactions by:

  - Same underlying symbol
  - Same strategy type (e.g., "vertical_call_spread")
  - Opening transaction has `position_effect = "open"`
  - Closing transaction has `position_effect = "close"`
  - Closing transaction occurs after opening (within reasonable time window)

- Store links in `transaction_links` table

- Allow manual override via API

**API Functions:**

- `link_transactions()` - Run automatic linking on transactions
- `get_linked_transactions(transaction_id)` - Get related transactions
- `add_link(opening_id, closing_id, link_type)` - Manually add link
- `remove_link(link_id)` - Remove a link

**Future Enhancements:**

- More sophisticated matching algorithms
- FIFO vs LIFO linking strategies
- Multi-leg spread detection
- Custom linking rules

### 4.3 Query API

**File:** `src/api/query.py`

**Functions:**

- `get_transactions(filters)` - Query transactions
- `get_positions()` - Get current positions
- `get_performance_metrics()` - Pre-calculated metrics
- `get_enriched_data(transaction_id)` - Get enrichment for transaction
- `get_linked_transactions(transaction_id)` - Get linked transactions (uses linking API)

**Use Cases:**

- CLI tools query via Python API
- Future web app queries via API
- MCP server exposes via MCP protocol

______________________________________________________________________

## Phase 5: CLI Interface

### 5.1 CLI Commands

**File:** `src/cli/main.py`

**Commands:**

- `tradedata sync [source]` - Sync data from source(s) (separate from enrichment)
- `tradedata enrich [--transaction-id]` - Enrich transactions (explicit, separate from sync)
- `tradedata link` - Link related transactions (entries → exits)
- `tradedata query [filters]` - Query transactions
- `tradedata export [format] [--output]` - Export data
- `tradedata validate` - Validate data integrity
- `tradedata status` - Show sync status, data counts

**Example Usage:**

```bash
# Sync from Robinhood (separate step)
tradedata sync robinhood

# Enrich all option transactions (separate step, explicit)
tradedata enrich --type option

# Link related transactions (optional, separate step)
tradedata link

# Query recent option trades
tradedata query --type option --days 30

# Export to CSV
tradedata export csv --output trades.csv --include-enriched
```

______________________________________________________________________

## Technical Stack

**Core:**

- Python 3.9+
- SQLite for storage (can migrate to PostgreSQL later if needed)
- `pandas` for data manipulation
- `click` for CLI

**Package Management:**

- `uv` for fast Python package installation and dependency management
- `pyproject.toml` for project configuration and dependencies
- Virtual environment management via `uv`

**Data Sources:**

- `robin_stocks` for Robinhood API
- Future: Other broker APIs

**Enrichment:**

- `pandas-ta` or `ta-lib` for technical indicators
- `robin_stocks` for market data

**Validation:**

- `pydantic` for data models and validation (optional, can use dataclasses instead)
- Custom validation logic for business rules

**Development Tools:**

- `pytest` + `pytest-cov` + `pytest-mock` for testing
- `ruff` for linting and formatting
- `mypy` for type checking (gradual adoption)
- `bandit` for security scanning
- `pre-commit` for git hooks

______________________________________________________________________

## File Structure

```
tradedata/
├── src/
│   ├── data/
│   │   ├── __init__.py
│   │   ├── schema.py           # Database schema
│   │   ├── models.py            # Python data models (dataclasses/Pydantic)
│   │   ├── normalize.py         # Normalization logic
│   │   ├── storage.py           # SQLite operations (low-level)
│   │   ├── repository.py        # Repository pattern for data access
│   │   └── validator.py          # Data validation
│   ├── sources/
│   │   ├── __init__.py
│   │   ├── base.py              # Abstract base class
│   │   ├── robinhood.py         # Robinhood adapter
│   │   └── factory.py           # Source factory
│   ├── enrichment/
│   │   ├── __init__.py
│   │   ├── enricher.py          # Main enrichment pipeline
│   │   ├── greeks.py            # Fetch Greeks
│   │   ├── technicals.py        # Calculate technicals
│   │   └── iv.py                # Fetch IV
│   ├── sync/
│   │   ├── __init__.py
│   │   └── syncer.py            # Sync logic
│   ├── positions/
│   │   ├── __init__.py
│   │   └── tracker.py           # Position tracking
│   ├── linking/
│   │   ├── __init__.py
│   │   └── linker.py            # Transaction linking
│   ├── export/
│   │   ├── __init__.py
│   │   └── exporters.py         # Export functions
│   ├── api/
│   │   ├── __init__.py
│   │   └── query.py             # Query API
│   └── cli/
│       ├── __init__.py
│       └── main.py              # CLI interface
├── data/
│   └── trading.db               # SQLite database
├── config/
│   └── sources.yaml              # Data source configuration
├── pyproject.toml                # Project config and dependencies (uv)
├── README.md
└── .env.example
```

______________________________________________________________________

## Success Criteria

1. **Data Normalization:**

   ```
        - All Robinhood transactions stored in unified schema
        - Data validation ensures correctness
        - Original data preserved in raw_data field
   ```

1. **Enrichment:**

   ```
        - Greeks, IV, technicals fetched for historical timestamps
        - Enrichment pipeline fails fast on errors (no graceful handling)
        - Results cached to avoid re-fetching
        - Re-enrichment supported (overwrite existing enriched data)
   ```

1. **Multi-Source Ready:**

   ```
        - Architecture supports adding new data sources
        - Adapter pattern makes it easy to add sources
        - Unified schema works across sources
   ```

1. **Export & Query:**

   ```
        - Data can be exported in multiple formats
        - Query API provides easy access to data
        - CLI is user-friendly and well-documented
   ```

______________________________________________________________________

## Migration from rhscrape

**Initial Data Import:**

- Use existing `robinhood_transactions_api_2025-11-23.json` from `rhscrape`
- Import all 1,438 transactions into new database
- Validate data integrity after import

**Ongoing:**

- `rhscrape` can continue to export JSON
- `TradeData` imports from JSON or directly from API
- Eventually `TradeData` becomes primary data source

______________________________________________________________________

## Development Standards

### Error Handling Philosophy

**During Initial Development:**

- **Fail loud, hard, and fast** - no graceful error handling
- No backwards compatibility concerns
- Exceptions raised immediately on any error
- No partial results or degraded modes
- This is a personal project - prioritize development speed over production robustness

**Examples:**

- If enrichment fails → raise exception immediately
- If validation fails → raise exception immediately
- If API call fails → raise exception immediately
- If data is missing → raise exception immediately

**Future:** Once core functionality is stable, we can add graceful error handling and backwards compatibility.

### Testing

**Testing Framework:**

- `pytest` for unit and integration tests
- `pytest-cov` for coverage reporting
- `pytest-mock` for mocking external APIs

**Test Structure:**

```
tests/
├── unit/
│   ├── test_normalize.py
│   ├── test_enrichment.py
│   └── test_validator.py
├── integration/
│   ├── test_robinhood_adapter.py
│   ├── test_storage.py
│   └── test_enrichment_pipeline.py
└── fixtures/
    └── sample_transactions.json
```

**Test Coverage Goals:**

- Unit tests: 80%+ coverage
- Integration tests for critical paths (data sync, enrichment)
- Mock external APIs (robin_stocks) to avoid rate limits
- Use in-memory SQLite for database tests

**CI/CD:**

- Run tests on every commit
- Enforce coverage thresholds
- Test against multiple Python versions (3.9, 3.10, 3.11)

### Linting & Formatting

**Tools:**

- `ruff` for linting and formatting (fast, modern)
- `mypy` for type checking (optional, gradual adoption)
- `black` as fallback if not using ruff formatting

**Configuration:**

- `.ruff.toml` for linting rules
- `pyproject.toml` for project metadata, dependencies (via uv), and tool configs
- Pre-commit hooks to run linting/formatting before commits

**Standards:**

- Follow PEP 8 style guide
- Type hints for public APIs
- Docstrings for all public functions/classes
- Maximum line length: 100 characters (configurable)

### Static Analysis

**Tools:**

- `ruff` for linting (replaces flake8, isort, etc.)
- `mypy` for type checking (gradual adoption)
- `bandit` for security scanning

**Pre-commit Hooks:**

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
```

### Dependency Injection

**Pattern:** Use dependency injection for testability and flexibility

**Approach:**

- Constructor injection for dependencies
- Abstract base classes for external services (APIs, storage)
- Factory functions for creating instances
- Configuration objects for settings

**Example:**

```python
# Abstract base class
class MarketDataProvider(ABC):
    @abstractmethod
    def get_greeks(self, symbol, strike, expiration, timestamp):
        pass

# Implementation
class RobinhoodMarketData(MarketDataProvider):
    def get_greeks(self, symbol, strike, expiration, timestamp):
        # Use robin_stocks
        pass

# Usage with dependency injection
class Enricher:
    def __init__(self, market_data: MarketDataProvider, storage: Storage):
        self.market_data = market_data
        self.storage = storage

    def enrich_transaction(self, transaction):
        greeks = self.market_data.get_greeks(...)
        # ...

# In tests, inject mock
enricher = Enricher(mock_market_data, mock_storage)
```

**Benefits:**

- Easy to test (inject mocks)
- Easy to swap implementations (e.g., different market data providers)
- Clear dependencies (explicit in constructor)

### Project Type Clarification

**This is a Python Library + CLI Tool:**

1. **Primary: Python Library**

   ```
        - Installable via `uv pip install tradedata` or `pip install tradedata`
        - Importable: `from tradedata import DataStore, sync, enrich`
        - Used by other projects as a dependency
        - Provides clean, typed API
   ```

1. **Secondary: CLI Tool**

   ```
        - Command-line interface for direct user interaction
        - Thin wrapper around library functions
        - Useful for one-off operations, debugging, manual syncs
   ```

1. **NOT:**

   ```
        - Backend server (separate project would be needed)
        - Web application (separate project)
        - Real-time streaming service (separate project)
   ```

**Usage Patterns:**

```python
# Pattern 1: Library usage (most common)
from tradedata import DataStore

store = DataStore()
store.sync_from_robinhood()
transactions = store.query_transactions(type="option")

# Pattern 2: CLI usage
$ tradedata sync robinhood
$ tradedata enrich --type option
$ tradedata query --type option --days 30

# Pattern 3: Other projects import it
# In rhmonitor project:
from tradedata import DataStore
store = DataStore(db_path="/shared/data/trading.db")
```

______________________________________________________________________

## Future Enhancements

- PostgreSQL support (for larger datasets)
- Real-time data streaming
- Data quality monitoring and alerts
- Automated enrichment scheduling
- Data versioning/history tracking
- Multi-account support
- Tax lot tracking
- Cost basis calculations
