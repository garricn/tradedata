"""Application-layer listing helpers for transactions and positions."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from tradedata.data.models import Position, Transaction
from tradedata.data.repositories import PositionRepository, TransactionRepository
from tradedata.data.storage import Storage


def _parse_timestamp(value: str) -> Optional[datetime]:
    """Parse ISO-ish timestamp into UTC datetime."""
    normalized = value
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo:
        return parsed.astimezone(timezone.utc)
    return parsed.replace(tzinfo=timezone.utc)


def _within_days(timestamp: Optional[datetime], days: int) -> bool:
    """Check if timestamp is within the past N days."""
    if timestamp is None:
        return False
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return timestamp >= cutoff


def list_transactions(
    transaction_type: Optional[str] = None,
    transaction_types: Optional[list[str]] = None,
    days: Optional[int] = None,
    storage: Optional[Storage] = None,
) -> list[Transaction]:
    """Return transactions with optional type/days filters."""
    storage = storage or Storage()
    repo = TransactionRepository(storage)
    types_filter = transaction_types or ([transaction_type] if transaction_type else None)
    transactions = repo.find_all()
    if types_filter:
        types_set = set(types_filter)
        transactions = [tx for tx in transactions if tx.type in types_set]

    if days is not None:
        transactions = [
            tx for tx in transactions if _within_days(_parse_timestamp(tx.created_at), days)
        ]

    return transactions


def list_positions(storage: Optional[Storage] = None) -> list[Position]:
    """Return all positions."""
    storage = storage or Storage()
    repo = PositionRepository(storage)
    return repo.find_all()
