"""Data validation for trading data models.

Validates normalized data to ensure integrity before storage.
Fails hard and fast on any validation error.
"""

from datetime import datetime

from tradedata.data.models import (
    Execution,
    OptionLeg,
    OptionOrder,
    Position,
    StockOrder,
    Transaction,
    TransactionLink,
)


class ValidationError(Exception):
    """Raised when data validation fails."""

    pass


def _is_valid_iso_timestamp(timestamp: str) -> bool:
    """Check if string is valid ISO 8601 timestamp.

    Args:
        timestamp: String to validate

    Returns:
        True if valid ISO timestamp, False otherwise
    """
    try:
        # Try parsing with Z suffix
        if timestamp.endswith("Z"):
            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        else:
            datetime.fromisoformat(timestamp)
        return True
    except (ValueError, TypeError):
        return False


def _is_uuid(value: str) -> bool:
    """Check if string is valid UUID format.

    Args:
        value: String to validate

    Returns:
        True if valid UUID, False otherwise
    """
    try:
        # Simple UUID check: 36 chars, hyphens in right places
        if len(value) != 36:
            return False
        parts = value.split("-")
        if len(parts) != 5:
            return False
        # Check lengths: 8-4-4-4-12
        return [len(p) for p in parts] == [8, 4, 4, 4, 12]
    except (AttributeError, TypeError):
        return False


def validate_transaction(transaction: Transaction) -> None:
    """Validate Transaction model.

    Args:
        transaction: Transaction instance to validate

    Raises:
        ValidationError: If validation fails
    """
    # Required fields
    if not transaction.id or not isinstance(transaction.id, str):
        raise ValidationError("Transaction.id: must be non-empty string")
    if not _is_uuid(transaction.id):
        raise ValidationError(f"Transaction.id: invalid UUID format: {transaction.id}")

    if not transaction.source or not isinstance(transaction.source, str):
        raise ValidationError("Transaction.source: must be non-empty string")

    if not transaction.source_id or not isinstance(transaction.source_id, str):
        raise ValidationError("Transaction.source_id: must be non-empty string")

    if not transaction.type or not isinstance(transaction.type, str):
        raise ValidationError("Transaction.type: must be non-empty string")

    if not transaction.created_at or not isinstance(transaction.created_at, str):
        raise ValidationError("Transaction.created_at: must be non-empty string")

    if not _is_valid_iso_timestamp(transaction.created_at):
        raise ValidationError(
            f"Transaction.created_at: invalid ISO timestamp: {transaction.created_at}"
        )

    if not isinstance(transaction.raw_data, str):
        raise ValidationError("Transaction.raw_data: must be string")

    # Optional field validation
    if transaction.account_id is not None and not isinstance(transaction.account_id, str):
        raise ValidationError("Transaction.account_id: must be string or None")


def validate_option_order(order: OptionOrder) -> None:
    """Validate OptionOrder model.

    Args:
        order: OptionOrder instance to validate

    Raises:
        ValidationError: If validation fails
    """
    # Foreign key reference
    if not order.id or not isinstance(order.id, str):
        raise ValidationError("OptionOrder.id: must be non-empty string (FK to transactions)")
    if not _is_uuid(order.id):
        raise ValidationError(f"OptionOrder.id: invalid UUID format: {order.id}")

    # Required fields
    if not order.chain_symbol or not isinstance(order.chain_symbol, str):
        raise ValidationError("OptionOrder.chain_symbol: must be non-empty string")

    # Optional fields with type checks
    if order.opening_strategy is not None and not isinstance(order.opening_strategy, str):
        raise ValidationError("OptionOrder.opening_strategy: must be string or None")

    if order.closing_strategy is not None and not isinstance(order.closing_strategy, str):
        raise ValidationError("OptionOrder.closing_strategy: must be string or None")

    if order.direction is not None and not isinstance(order.direction, str):
        raise ValidationError("OptionOrder.direction: must be string or None")

    if order.premium is not None and not isinstance(order.premium, (int, float)):
        raise ValidationError("OptionOrder.premium: must be number or None")

    if order.net_amount is not None and not isinstance(order.net_amount, (int, float)):
        raise ValidationError("OptionOrder.net_amount: must be number or None")


def validate_option_leg(leg: OptionLeg) -> None:
    """Validate OptionLeg model.

    Args:
        leg: OptionLeg instance to validate

    Raises:
        ValidationError: If validation fails
    """
    # Required ID fields
    if not leg.id or not isinstance(leg.id, str):
        raise ValidationError("OptionLeg.id: must be non-empty string")
    if not _is_uuid(leg.id):
        raise ValidationError(f"OptionLeg.id: invalid UUID format: {leg.id}")

    if not leg.order_id or not isinstance(leg.order_id, str):
        raise ValidationError("OptionLeg.order_id: must be non-empty string (FK to option_orders)")
    if not _is_uuid(leg.order_id):
        raise ValidationError(f"OptionLeg.order_id: invalid UUID format: {leg.order_id}")

    # Required fields with business logic
    if not isinstance(leg.strike_price, (int, float)):
        raise ValidationError("OptionLeg.strike_price: must be number")
    if leg.strike_price < 0:
        raise ValidationError(f"OptionLeg.strike_price: must be positive, got {leg.strike_price}")

    if not leg.expiration_date or not isinstance(leg.expiration_date, str):
        raise ValidationError("OptionLeg.expiration_date: must be non-empty string")
    if not _is_valid_iso_timestamp(leg.expiration_date):
        raise ValidationError(f"OptionLeg.expiration_date: invalid ISO date: {leg.expiration_date}")

    if not leg.option_type or not isinstance(leg.option_type, str):
        raise ValidationError("OptionLeg.option_type: must be non-empty string")
    if leg.option_type.lower() not in ["call", "put"]:
        raise ValidationError(
            f"OptionLeg.option_type: must be 'call' or 'put', got {leg.option_type}"
        )

    if not leg.side or not isinstance(leg.side, str):
        raise ValidationError("OptionLeg.side: must be non-empty string")
    if leg.side.lower() not in ["buy", "sell"]:
        raise ValidationError(f"OptionLeg.side: must be 'buy' or 'sell', got {leg.side}")

    if not leg.position_effect or not isinstance(leg.position_effect, str):
        raise ValidationError("OptionLeg.position_effect: must be non-empty string")
    if leg.position_effect.lower() not in ["open", "close"]:
        raise ValidationError(
            f"OptionLeg.position_effect: must be 'open' or 'close', got {leg.position_effect}"
        )

    if not isinstance(leg.ratio_quantity, int):
        raise ValidationError("OptionLeg.ratio_quantity: must be integer")
    if leg.ratio_quantity <= 0:
        raise ValidationError(
            f"OptionLeg.ratio_quantity: must be positive, got {leg.ratio_quantity}"
        )


def validate_execution(execution: Execution) -> None:
    """Validate Execution model.

    Args:
        execution: Execution instance to validate

    Raises:
        ValidationError: If validation fails
    """
    # Required ID fields
    if not execution.id or not isinstance(execution.id, str):
        raise ValidationError("Execution.id: must be non-empty string")
    if not _is_uuid(execution.id):
        raise ValidationError(f"Execution.id: invalid UUID format: {execution.id}")

    if not execution.order_id or not isinstance(execution.order_id, str):
        raise ValidationError("Execution.order_id: must be non-empty string (FK to transactions)")
    if not _is_uuid(execution.order_id):
        raise ValidationError(f"Execution.order_id: invalid UUID format: {execution.order_id}")

    # Optional leg_id validation
    if execution.leg_id is not None and not isinstance(execution.leg_id, str):
        raise ValidationError("Execution.leg_id: must be string or None")
    if execution.leg_id is not None and not _is_uuid(execution.leg_id):
        raise ValidationError(f"Execution.leg_id: invalid UUID format: {execution.leg_id}")

    # Required numeric fields
    if not isinstance(execution.price, (int, float)):
        raise ValidationError("Execution.price: must be number")
    if execution.price < 0:
        raise ValidationError(f"Execution.price: must be non-negative, got {execution.price}")

    if not isinstance(execution.quantity, (int, float)):
        raise ValidationError("Execution.quantity: must be number")
    if execution.quantity <= 0:
        raise ValidationError(f"Execution.quantity: must be positive, got {execution.quantity}")

    # Required timestamp field
    if not execution.timestamp or not isinstance(execution.timestamp, str):
        raise ValidationError("Execution.timestamp: must be non-empty string")
    if not _is_valid_iso_timestamp(execution.timestamp):
        raise ValidationError(f"Execution.timestamp: invalid ISO timestamp: {execution.timestamp}")

    # Optional settlement date
    if execution.settlement_date is not None and not isinstance(execution.settlement_date, str):
        raise ValidationError("Execution.settlement_date: must be string or None")
    if execution.settlement_date is not None and not _is_valid_iso_timestamp(
        execution.settlement_date
    ):
        raise ValidationError(
            f"Execution.settlement_date: invalid ISO date: {execution.settlement_date}"
        )


def validate_stock_order(order: StockOrder) -> None:
    """Validate StockOrder model.

    Args:
        order: StockOrder instance to validate

    Raises:
        ValidationError: If validation fails
    """
    # Foreign key
    if not order.id or not isinstance(order.id, str):
        raise ValidationError("StockOrder.id: must be non-empty string (FK to transactions)")
    if not _is_uuid(order.id):
        raise ValidationError(f"StockOrder.id: invalid UUID format: {order.id}")

    # Required fields
    if not order.symbol or not isinstance(order.symbol, str):
        raise ValidationError("StockOrder.symbol: must be non-empty string")

    if not order.side or not isinstance(order.side, str):
        raise ValidationError("StockOrder.side: must be non-empty string")
    if order.side.lower() not in ["buy", "sell"]:
        raise ValidationError(f"StockOrder.side: must be 'buy' or 'sell', got {order.side}")

    if not isinstance(order.quantity, (int, float)):
        raise ValidationError("StockOrder.quantity: must be number")
    if order.quantity <= 0:
        raise ValidationError(f"StockOrder.quantity: must be positive, got {order.quantity}")

    # Optional fields
    if order.price is not None and not isinstance(order.price, (int, float)):
        raise ValidationError("StockOrder.price: must be number or None")
    if order.price is not None and order.price < 0:
        raise ValidationError(f"StockOrder.price: must be non-negative, got {order.price}")

    if order.average_price is not None and not isinstance(order.average_price, (int, float)):
        raise ValidationError("StockOrder.average_price: must be number or None")
    if order.average_price is not None and order.average_price < 0:
        raise ValidationError(
            f"StockOrder.average_price: must be non-negative, got {order.average_price}"
        )


def validate_position(position: Position) -> None:
    """Validate Position model.

    Args:
        position: Position instance to validate

    Raises:
        ValidationError: If validation fails
    """
    # Required ID fields
    if not position.id or not isinstance(position.id, str):
        raise ValidationError("Position.id: must be non-empty string")
    if not _is_uuid(position.id):
        raise ValidationError(f"Position.id: invalid UUID format: {position.id}")

    # Required fields
    if not position.source or not isinstance(position.source, str):
        raise ValidationError("Position.source: must be non-empty string")

    if not position.symbol or not isinstance(position.symbol, str):
        raise ValidationError("Position.symbol: must be non-empty string")

    if not isinstance(position.quantity, (int, float)):
        raise ValidationError("Position.quantity: must be number")

    if position.account_id is not None and not isinstance(position.account_id, str):
        raise ValidationError("Position.account_id: must be string or None")

    # Optional fields
    if position.cost_basis is not None and not isinstance(position.cost_basis, (int, float)):
        raise ValidationError("Position.cost_basis: must be number or None")

    if position.current_price is not None and not isinstance(position.current_price, (int, float)):
        raise ValidationError("Position.current_price: must be number or None")

    if position.unrealized_pnl is not None and not isinstance(
        position.unrealized_pnl, (int, float)
    ):
        raise ValidationError("Position.unrealized_pnl: must be number or None")

    # Timestamp field
    if not position.last_updated or not isinstance(position.last_updated, str):
        raise ValidationError("Position.last_updated: must be non-empty string")
    if not _is_valid_iso_timestamp(position.last_updated):
        raise ValidationError(
            f"Position.last_updated: invalid ISO timestamp: {position.last_updated}"
        )


def validate_transaction_link(link: TransactionLink) -> None:
    """Validate TransactionLink model.

    Args:
        link: TransactionLink instance to validate

    Raises:
        ValidationError: If validation fails
    """
    # Required ID fields
    if not link.id or not isinstance(link.id, str):
        raise ValidationError("TransactionLink.id: must be non-empty string")
    if not _is_uuid(link.id):
        raise ValidationError(f"TransactionLink.id: invalid UUID format: {link.id}")

    if not link.opening_transaction_id or not isinstance(link.opening_transaction_id, str):
        raise ValidationError(
            "TransactionLink.opening_transaction_id: must be non-empty string (FK to transactions)"
        )
    if not _is_uuid(link.opening_transaction_id):
        opening_id = link.opening_transaction_id
        raise ValidationError(
            f"TransactionLink.opening_transaction_id: invalid UUID format: {opening_id}"
        )

    if not link.closing_transaction_id or not isinstance(link.closing_transaction_id, str):
        raise ValidationError(
            "TransactionLink.closing_transaction_id: must be non-empty string (FK to transactions)"
        )
    if not _is_uuid(link.closing_transaction_id):
        closing_id = link.closing_transaction_id
        raise ValidationError(
            f"TransactionLink.closing_transaction_id: invalid UUID format: {closing_id}"
        )

    # Business logic: opening and closing should be different
    if link.opening_transaction_id == link.closing_transaction_id:
        raise ValidationError(
            "TransactionLink: opening_transaction_id and closing_transaction_id must be different"
        )

    # Optional field
    if link.link_type is not None and not isinstance(link.link_type, str):
        raise ValidationError("TransactionLink.link_type: must be string or None")

    # Required timestamp
    if not link.created_at or not isinstance(link.created_at, str):
        raise ValidationError("TransactionLink.created_at: must be non-empty string")
    if not _is_valid_iso_timestamp(link.created_at):
        created_at = link.created_at
        raise ValidationError(f"TransactionLink.created_at: invalid ISO timestamp: {created_at}")
