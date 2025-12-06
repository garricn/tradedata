"""Robinhood data source adapter.

Extracts and normalizes trading data from Robinhood API using robin_stocks library.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional, Protocol

try:
    import robin_stocks.robinhood as rh_module
except ImportError:
    rh_module = None  # type: ignore

from tradedata.data.models import (
    Execution,
    OptionLeg,
    OptionOrder,
    Position,
    StockOrder,
    Transaction,
)
from tradedata.sources.base import DataSourceAdapter


class RobinhoodAPIWrapper:
    """Wrapper for robin_stocks.robinhood to provide flat method access.

    robin_stocks organizes methods under submodules (orders, options, etc),
    but this wrapper provides a flat interface that matches the RobinhoodAPI
    protocol for simpler dependency injection and testing.
    """

    def __init__(self, rh_module: Any):
        """Initialize wrapper with robin_stocks.robinhood module.

        Args:
            rh_module: robin_stocks.robinhood module instance
        """
        self.rh = rh_module

        def _resolve_callable(candidates: list[tuple[str, Any]], label: str):
            for name, getter in candidates:
                try:
                    fn = getter()
                except AttributeError:
                    continue
                if callable(fn):
                    return fn
            raise AttributeError(
                f"robin_stocks missing required API for {label}. "
                f"Expected one of: {[name for name, _ in candidates]}"
            )

        self._get_stock_orders = _resolve_callable(
            [
                (
                    "orders.get_all_stock_orders",
                    lambda: getattr(getattr(self.rh, "orders", None), "get_all_stock_orders", None),
                ),
                ("get_all_stock_orders", lambda: getattr(self.rh, "get_all_stock_orders", None)),
            ],
            "stock orders",
        )
        self._get_option_orders = _resolve_callable(
            [
                (
                    "options.get_all_option_orders",
                    lambda: getattr(
                        getattr(self.rh, "options", None), "get_all_option_orders", None
                    ),
                ),
                ("get_all_option_orders", lambda: getattr(self.rh, "get_all_option_orders", None)),
            ],
            "option orders",
        )
        self._get_stock_positions = _resolve_callable(
            [
                (
                    "stocks.get_all_stock_positions",
                    lambda: getattr(
                        getattr(self.rh, "stocks", None), "get_all_stock_positions", None
                    ),
                ),
                (
                    "get_open_stock_positions",
                    lambda: getattr(self.rh, "get_open_stock_positions", None),
                ),
                ("get_all_positions", lambda: getattr(self.rh, "get_all_positions", None)),
            ],
            "stock positions",
        )
        self._get_option_positions = _resolve_callable(
            [
                (
                    "options.get_all_option_positions",
                    lambda: getattr(
                        getattr(self.rh, "options", None), "get_all_option_positions", None
                    ),
                ),
                (
                    "get_open_option_positions",
                    lambda: getattr(self.rh, "get_open_option_positions", None),
                ),
                ("get_all_positions", lambda: getattr(self.rh, "get_all_positions", None)),
            ],
            "option positions",
        )
        self._get_symbol_by_url = _resolve_callable(
            [
                (
                    "stocks.get_symbol_by_url",
                    lambda: getattr(getattr(self.rh, "stocks", None), "get_symbol_by_url", None),
                ),
                ("get_symbol_by_url", lambda: getattr(self.rh, "get_symbol_by_url", None)),
            ],
            "symbol resolution by instrument URL",
        )

    def login(self, username: str, password: str) -> dict[str, Any]:
        """Login to Robinhood account."""
        return self.rh.login(username, password)  # type: ignore[no-any-return]

    def get_all_stock_orders(self) -> list[dict[str, Any]]:
        """Get all stock orders via orders.get_all_stock_orders()."""
        return self._get_stock_orders() or []  # type: ignore[no-any-return]

    def get_all_option_orders(self) -> list[dict[str, Any]]:
        """Get all option orders via options.get_all_option_orders()."""
        return self._get_option_orders() or []  # type: ignore[no-any-return]

    def get_open_stock_positions(self) -> list[dict[str, Any]]:
        """Get open stock positions via stocks.get_all_stock_positions()."""
        return self._get_stock_positions() or []  # type: ignore[no-any-return]

    def get_open_option_positions(self) -> list[dict[str, Any]]:
        """Get open option positions via options.get_all_option_positions()."""
        return self._get_option_positions() or []  # type: ignore[no-any-return]

    def get_symbol_by_url(self, instrument_url: str) -> Optional[str]:
        """Resolve symbol from instrument URL when provided by robin_stocks."""
        return self._get_symbol_by_url(instrument_url)  # type: ignore[no-any-return]


class RobinhoodAPI(Protocol):
    """Protocol defining the interface for Robinhood API access.

    This protocol defines the methods required from robin_stocks.robinhood
    or any compatible implementation. Used for dependency injection and type safety.
    """

    def login(self, username: str, password: str) -> dict[str, Any]:
        """Login to Robinhood account.

        Args:
            username: Robinhood username
            password: Robinhood password

        Returns:
            Login response dictionary
        """
        ...

    def get_all_stock_orders(self) -> list[dict[str, Any]]:
        """Get all stock orders.

        Returns:
            List of stock order dictionaries
        """
        ...

    def get_all_option_orders(self) -> list[dict[str, Any]]:
        """Get all option orders.

        Returns:
            List of option order dictionaries
        """
        ...

    def get_open_stock_positions(self) -> list[dict[str, Any]]:
        """Get open stock positions.

        Returns:
            List of stock position dictionaries
        """
        ...

    def get_open_option_positions(self) -> list[dict[str, Any]]:
        """Get open option positions.

        Returns:
            List of option position dictionaries
        """
        ...

    def get_symbol_by_url(self, instrument_url: str) -> Optional[str]:
        """Resolve symbol from instrument URL."""
        ...


class RobinhoodAdapter(DataSourceAdapter):
    """Robinhood data source adapter.

    Implements DataSourceAdapter interface to extract and normalize
    trading data from Robinhood API.

    Requires authentication via robin_stocks.login() before use.
    """

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        robin_stocks: Optional[RobinhoodAPI] = None,
    ):
        """Initialize Robinhood adapter.

        Args:
            username: Robinhood username (optional, can login separately)
            password: Robinhood password (optional, can login separately)
            robin_stocks: Robinhood API implementation (defaults to robin_stocks.robinhood).
                         Must implement RobinhoodAPI protocol.
                         Can be injected for testing or alternative implementations.

        Note:
            If username and password are provided, login will be attempted.
            Otherwise, caller must call robin_stocks.login() separately.
        """
        self.username = username
        self.password = password
        # Use injected implementation or create wrapper for default robin_stocks module
        if robin_stocks is not None:
            self.rh: RobinhoodAPI = robin_stocks  # type: ignore[assignment]
        elif rh_module is not None:
            self.rh = RobinhoodAPIWrapper(rh_module)  # type: ignore[assignment]
        else:
            self.rh = None  # type: ignore[assignment]

        if self.rh is None:
            raise ImportError(
                "robin_stocks is not installed. Install it with: pip install robin-stocks"
            )

        if username and password:
            self.rh.login(username, password)

    def extract_transactions(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """Extract transactions from Robinhood API.

        Args:
            start_date: Optional start date filter (ISO format string, e.g., '2025-01-01')
            end_date: Optional end date filter (ISO format string, e.g., '2025-12-31')

        Returns:
            List of raw transaction dictionaries from Robinhood API.
            Includes stock orders, option orders, executions, etc.

        Raises:
            Exception: If API call fails or authentication is required.
        """
        transactions = []

        # Get stock orders - fail hard if API call fails
        stock_orders = self.rh.get_all_stock_orders()
        if stock_orders:
            transactions.extend(stock_orders)

        # Get option orders - fail hard if API call fails
        option_orders = self.rh.get_all_option_orders()
        if option_orders:
            transactions.extend(option_orders)

        # Filter by date if provided
        if start_date or end_date:
            transactions = self._filter_by_date(transactions, start_date, end_date)

        return transactions

    def extract_positions(self) -> list[dict[str, Any]]:
        """Extract current positions from Robinhood API.

        Returns:
            List of raw position dictionaries from Robinhood API.

        Raises:
            Exception: If API call fails or authentication is required.
        """
        positions = []

        # Get stock positions - fail hard if API call fails
        stock_positions = self.rh.get_open_stock_positions()
        if stock_positions:
            positions.extend(stock_positions)

        # Get option positions - fail hard if API call fails
        option_positions = self.rh.get_open_option_positions()
        if option_positions:
            positions.extend(option_positions)

        return positions

    def normalize_transaction(self, raw_transaction: dict[str, Any]) -> Transaction:
        """Convert Robinhood transaction format to unified schema.

        Args:
            raw_transaction: Raw transaction dictionary from Robinhood API

        Returns:
            Transaction model instance with normalized data.

        Raises:
            ValueError: If raw_transaction is missing required fields.
        """
        # Determine transaction type
        transaction_type = self._determine_transaction_type(raw_transaction)

        # Extract common fields
        source_id = raw_transaction.get("id") or raw_transaction.get("order_id", "")
        created_at = self._extract_timestamp(raw_transaction)
        account_id = raw_transaction.get("account", "")

        # Create transaction ID (UUID)
        transaction_id = str(uuid.uuid4())

        # Store raw data as JSON
        raw_data_json = json.dumps(raw_transaction)

        # Create Transaction model
        transaction = Transaction(
            id=transaction_id,
            source="robinhood",
            source_id=str(source_id),
            type=transaction_type,
            created_at=created_at,
            account_id=account_id if account_id else None,
            raw_data=raw_data_json,
        )

        return transaction

    def _filter_by_date(
        self,
        transactions: list[dict[str, Any]],
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> list[dict[str, Any]]:
        """Filter transactions by date range.

        Args:
            transactions: List of transaction dictionaries
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)

        Returns:
            Filtered list of transactions
        """
        filtered = []

        for tx in transactions:
            tx_date = self._extract_timestamp(tx)
            if not tx_date:
                continue

            # Parse transaction timestamp, ensuring it's timezone-aware (UTC)
            tx_datetime = datetime.fromisoformat(tx_date.replace("Z", "+00:00"))
            if tx_datetime.tzinfo is None:
                # If still naive, assume UTC
                tx_datetime = tx_datetime.replace(tzinfo=timezone.utc)

            if start_date:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                # Ensure start_date is timezone-aware (UTC) for comparison
                if start_dt.tzinfo is None:
                    start_dt = start_dt.replace(tzinfo=timezone.utc)
                if tx_datetime < start_dt:
                    continue

            if end_date:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                # Ensure end_date is timezone-aware (UTC) for comparison
                if end_dt.tzinfo is None:
                    end_dt = end_dt.replace(tzinfo=timezone.utc)
                # If end_date is date-only (no time component), include entire day
                if end_dt.time() == datetime.min.time():
                    end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
                if tx_datetime > end_dt:
                    continue

            filtered.append(tx)

        return filtered

    def _determine_transaction_type(self, raw_transaction: dict[str, Any]) -> str:
        """Determine transaction type from raw data.

        Args:
            raw_transaction: Raw transaction dictionary

        Returns:
            Transaction type string (e.g., 'stock', 'option', 'crypto', 'dividend')
        """
        # Check for option-specific fields
        if "legs" in raw_transaction or "option" in raw_transaction.get("instrument", ""):
            return "option"

        # Check for stock-specific fields
        symbol = raw_transaction.get("symbol")
        if symbol and "option" not in raw_transaction.get("instrument", ""):
            return "stock"

        # Check for crypto
        if "crypto" in raw_transaction.get("type", "").lower():
            return "crypto"

        # Check for dividend
        if "dividend" in raw_transaction.get("type", "").lower():
            return "dividend"

        # Default to 'unknown' if unclear
        return "unknown"

    def _extract_timestamp(self, raw_transaction: dict[str, Any]) -> str:
        """Extract ISO timestamp from raw transaction.

        Args:
            raw_transaction: Raw transaction dictionary

        Returns:
            ISO format timestamp string
        """
        # Try various timestamp fields
        timestamp_fields = [
            "created_at",
            "updated_at",
            "last_transaction_at",
            "execution_date",
            "timestamp",
        ]

        for field in timestamp_fields:
            if field in raw_transaction and raw_transaction[field]:
                timestamp = raw_transaction[field]
                # Ensure ISO format
                if isinstance(timestamp, str):
                    return timestamp
                # If it's a datetime object, convert to ISO
                if hasattr(timestamp, "isoformat"):
                    return str(timestamp.isoformat())

        # Default to current time if no timestamp found
        return datetime.utcnow().isoformat() + "Z"

    def extract_option_order(
        self, raw_transaction: dict[str, Any], transaction_id: str
    ) -> Optional[OptionOrder]:
        """Extract OptionOrder from raw transaction.

        Args:
            raw_transaction: Raw transaction dictionary from Robinhood API
            transaction_id: Transaction ID to use as foreign key

        Returns:
            OptionOrder model instance, or None if not an option order
        """
        if self._determine_transaction_type(raw_transaction) != "option":
            return None

        # Extract option order fields
        chain_symbol = raw_transaction.get("chain_symbol", "")
        opening_strategy = raw_transaction.get("opening_strategy")
        closing_strategy = raw_transaction.get("closing_strategy")
        direction = raw_transaction.get("direction")
        premium = self._safe_float(raw_transaction.get("premium"))
        net_amount = self._safe_float(raw_transaction.get("net_amount"))

        return OptionOrder(
            id=transaction_id,
            chain_symbol=chain_symbol,
            opening_strategy=opening_strategy,
            closing_strategy=closing_strategy,
            direction=direction,
            premium=premium,
            net_amount=net_amount,
        )

    def extract_option_legs(
        self, raw_transaction: dict[str, Any], option_order_id: str
    ) -> list[OptionLeg]:
        """Extract OptionLeg models from raw transaction.

        Args:
            raw_transaction: Raw transaction dictionary from Robinhood API
            option_order_id: Option order ID to use as foreign key

        Returns:
            List of OptionLeg model instances
        """
        legs = []
        raw_legs = raw_transaction.get("legs", [])

        for raw_leg in raw_legs:
            leg_id = str(uuid.uuid4())

            # Extract leg fields
            strike_price = self._safe_float(raw_leg.get("strike_price", 0)) or 0.0
            expiration_date = self._extract_expiration_date(raw_leg)
            option_type = raw_leg.get("option_type", "").lower()
            side = raw_leg.get("side", "").lower()
            position_effect = raw_leg.get("position_effect", "").lower()
            ratio_quantity = int(raw_leg.get("ratio_quantity", 1))

            leg = OptionLeg(
                id=leg_id,
                order_id=option_order_id,
                strike_price=strike_price,
                expiration_date=expiration_date,
                option_type=option_type,
                side=side,
                position_effect=position_effect,
                ratio_quantity=ratio_quantity,
            )
            legs.append(leg)

        return legs

    def extract_executions(
        self,
        raw_transaction: dict[str, Any],
        transaction_id: str,
        leg_ids: Optional[list[str]] = None,
    ) -> list[Execution]:
        """Extract Execution models from raw transaction.

        Args:
            raw_transaction: Raw transaction dictionary from Robinhood API
            transaction_id: Transaction ID to use as foreign key
            leg_ids: Optional list of leg IDs to match executions to legs

        Returns:
            List of Execution model instances
        """
        executions = []
        raw_executions = raw_transaction.get("executions", [])

        for idx, raw_exec in enumerate(raw_executions):
            exec_id = str(uuid.uuid4())

            # Match execution to leg if leg_ids provided
            leg_id = None
            if leg_ids and idx < len(leg_ids):
                leg_id = leg_ids[idx]

            price = self._safe_float(raw_exec.get("price", 0)) or 0.0
            quantity = self._safe_float(raw_exec.get("quantity", 0)) or 0.0
            timestamp = self._extract_timestamp(raw_exec)
            settlement_date = raw_exec.get("settlement_date")

            execution = Execution(
                id=exec_id,
                order_id=transaction_id,
                leg_id=leg_id,
                price=price,
                quantity=quantity,
                timestamp=timestamp,
                settlement_date=settlement_date,
            )
            executions.append(execution)

        return executions

    def extract_stock_order(
        self, raw_transaction: dict[str, Any], transaction_id: str
    ) -> Optional[StockOrder]:
        """Extract StockOrder from raw transaction.

        Args:
            raw_transaction: Raw transaction dictionary from Robinhood API
            transaction_id: Transaction ID to use as foreign key

        Returns:
            StockOrder model instance, or None if not a stock order
        """
        if self._determine_transaction_type(raw_transaction) != "stock":
            return None

        # Extract stock order fields
        symbol = raw_transaction.get("symbol", "")
        if not symbol:
            return None
        side = raw_transaction.get("side", "").lower()
        quantity = self._safe_float(raw_transaction.get("quantity", 0)) or 0.0
        price = self._safe_float(raw_transaction.get("price")) or 0.0
        average_price = self._safe_float(raw_transaction.get("average_price")) or 0.0

        return StockOrder(
            id=transaction_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            average_price=average_price,
        )

    def normalize_position(self, raw_position: dict[str, Any]) -> Position:
        """Convert Robinhood position format to unified schema.

        Args:
            raw_position: Raw position dictionary from Robinhood API

        Returns:
            Position model instance with normalized data.
        """
        position_id = str(uuid.uuid4())
        symbol = raw_position.get("symbol") or raw_position.get("chain_symbol") or ""
        if not symbol:
            instrument_url = raw_position.get("instrument")
            if instrument_url:
                resolved = self.rh.get_symbol_by_url(instrument_url)
                if resolved:
                    symbol = resolved
        quantity = self._safe_float(raw_position.get("quantity", 0)) or 0.0
        cost_basis = self._safe_float(raw_position.get("cost_basis")) or 0.0
        current_price = self._safe_float(raw_position.get("current_price")) or 0.0
        unrealized_pnl = self._safe_float(raw_position.get("unrealized_pnl")) or 0.0
        last_updated = self._extract_timestamp(raw_position)

        return Position(
            id=position_id,
            source="robinhood",
            symbol=symbol,
            quantity=quantity,
            cost_basis=cost_basis,
            current_price=current_price,
            unrealized_pnl=unrealized_pnl,
            last_updated=last_updated,
        )

    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float.

        Args:
            value: Value to convert

        Returns:
            Float value, or None if conversion fails
        """
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _extract_expiration_date(self, raw_leg: dict[str, Any]) -> str:
        """Extract expiration date from option leg.

        Args:
            raw_leg: Raw leg dictionary

        Returns:
            ISO format expiration date string
        """
        # Try various expiration date fields
        exp_fields = ["expiration_date", "expires_at", "expiry", "expiration"]

        for field in exp_fields:
            if field in raw_leg and raw_leg[field]:
                exp_date = raw_leg[field]
                if isinstance(exp_date, str):
                    return exp_date
                if hasattr(exp_date, "isoformat"):
                    return str(exp_date.isoformat())

        # Default to a far future date if not found
        return "2099-12-31"
