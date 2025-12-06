"""Transaction sync orchestration for Robinhood and other sources.

Coordinates credentials, adapter calls, validation, and persistence.
Designed to be broker-agnostic via the `source` parameter.
"""

from typing import List, Optional

from tradedata.application import credentials
from tradedata.data.models import Position, Transaction
from tradedata.data.repositories import (
    ExecutionRepository,
    OptionLegRepository,
    OptionOrderRepository,
    PositionRepository,
    StockOrderRepository,
    TransactionRepository,
)
from tradedata.data.storage import Storage
from tradedata.data.validator import (
    validate_execution,
    validate_option_leg,
    validate_option_order,
    validate_position,
    validate_stock_order,
    validate_transaction,
)
from tradedata.sources import create_adapter


def _login_adapter(adapter, username: str, password: str) -> None:
    """Log in using adapter-specific login method."""
    login_method = getattr(adapter, "login", None)
    if callable(login_method):
        login_method(username, password)
        return

    # Fallback for adapters exposing underlying API via `rh`
    rh = getattr(adapter, "rh", None)
    if rh is not None and hasattr(rh, "login"):
        rh.login(username, password)
        return

    raise AttributeError("Adapter does not support login")


def sync_transactions(
    source: str = "robinhood",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    storage: Optional[Storage] = None,
    adapter=None,
) -> List[Transaction]:
    """Sync transactions from a source into storage.

    Workflow:
    1. Retrieve credentials from keyring
    2. Create adapter (or use injected adapter)
    3. Login via adapter
    4. Extract raw transactions
    5. Normalize, validate, and persist transaction + related entities

    Args:
        source: Data source name (default: 'robinhood')
        start_date: Optional start date filter (ISO string)
        end_date: Optional end date filter (ISO string)
        storage: Optional Storage instance (defaults to configured database)
        adapter: Optional adapter instance (for testing or custom sources)

    Returns:
        List of stored Transaction models.

    Raises:
        CredentialsNotFoundError: When credentials are not in keyring.
        ValidationError: When any model fails validation.
        AttributeError: When adapter cannot perform login.
        Exception: Propagates any adapter or storage errors.
    """
    username, password = credentials.get_credentials(source)

    adapter = adapter or create_adapter(source)
    _login_adapter(adapter, username, password)

    raw_transactions = adapter.extract_transactions(start_date=start_date, end_date=end_date)

    storage = storage or Storage()
    tx_repo = TransactionRepository(storage)
    option_order_repo = OptionOrderRepository(storage)
    leg_repo = OptionLegRepository(storage)
    execution_repo = ExecutionRepository(storage)
    stock_repo = StockOrderRepository(storage)

    stored_transactions: list[Transaction] = []

    for raw_tx in raw_transactions:
        transaction = adapter.normalize_transaction(raw_tx)
        validate_transaction(transaction)
        if tx_repo.exists_by_source_id(transaction.source, transaction.source_id):
            continue
        tx_repo.create(transaction)
        stored_transactions.append(transaction)

        option_order = adapter.extract_option_order(raw_tx, transaction.id)
        if option_order:
            validate_option_order(option_order)
            option_order_repo.create(option_order)

            legs = adapter.extract_option_legs(raw_tx, option_order.id)
            for leg in legs:
                validate_option_leg(leg)
                leg_repo.create(leg)

            leg_ids = [leg.id for leg in legs] if legs else None
            executions = adapter.extract_executions(raw_tx, transaction.id, leg_ids)
            for execution in executions:
                validate_execution(execution)
                execution_repo.create(execution)
        else:
            stock_order = adapter.extract_stock_order(raw_tx, transaction.id)
            if stock_order:
                validate_stock_order(stock_order)
                stock_repo.create(stock_order)

    return stored_transactions


def sync_positions(
    source: str = "robinhood",
    storage: Optional[Storage] = None,
    adapter=None,
) -> List[Position]:
    """Sync positions from a source into storage.

    Workflow:
    1. Retrieve credentials from keyring
    2. Create adapter (or use injected adapter)
    3. Login via adapter
    4. Extract raw positions
    5. Normalize, validate, and persist positions

    Args:
        source: Data source name (default: 'robinhood')
        storage: Optional Storage instance (defaults to configured database)
        adapter: Optional adapter instance (for testing or custom sources)

    Returns:
        List of stored Position models.

    Raises:
        CredentialsNotFoundError: When credentials are not in keyring.
        ValidationError: When any model fails validation.
        AttributeError: When adapter cannot perform login.
        Exception: Propagates any adapter or storage errors.
    """
    username, password = credentials.get_credentials(source)

    adapter = adapter or create_adapter(source)
    _login_adapter(adapter, username, password)

    raw_positions = adapter.extract_positions()

    storage = storage or Storage()
    position_repo = PositionRepository(storage)

    stored_positions: list[Position] = []

    for raw_pos in raw_positions:
        position = adapter.normalize_position(raw_pos)
        validate_position(position)
        position_repo.create(position)
        stored_positions.append(position)

    return stored_positions
