"""Application-layer listing helpers for transactions and positions."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from tradedata.data.models import OptionLeg, OptionOrder, Position, StockOrder, Transaction
from tradedata.data.repositories import (
    OptionLegRepository,
    OptionOrderRepository,
    PositionRepository,
    StockOrderRepository,
    TransactionRepository,
)
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


@dataclass
class TransactionTable:
    """Renderable transaction table grouped by type."""

    transaction_type: str
    headers: list[str]
    rows: list[list[str]]


def list_enriched_transaction_tables(
    transaction_types: Optional[list[str]] = None,
    days: Optional[int] = None,
    storage: Optional[Storage] = None,
) -> list[TransactionTable]:
    """Return type-specific enriched transaction tables."""
    storage = storage or Storage()
    transactions = list_transactions(
        transaction_types=transaction_types,
        days=days,
        storage=storage,
    )
    if not transactions:
        return []

    ordered_types: list[str] = []
    transactions_by_type: dict[str, list[Transaction]] = defaultdict(list)
    for tx in transactions:
        if tx.type not in ordered_types:
            ordered_types.append(tx.type)
        transactions_by_type[tx.type].append(tx)

    tx_ids = {tx.id for tx in transactions}
    stock_repo = StockOrderRepository(storage)
    stock_orders = {order.id: order for order in stock_repo.find_all() if order.id in tx_ids}

    option_repo = OptionOrderRepository(storage)
    option_orders = {order.id: order for order in option_repo.find_all() if order.id in tx_ids}

    leg_repo = OptionLegRepository(storage)
    legs_by_order: dict[str, list[OptionLeg]] = defaultdict(list)
    for leg in leg_repo.find_all():
        if leg.order_id in option_orders:
            legs_by_order[leg.order_id].append(leg)

    tables: list[TransactionTable] = []
    for tx_type in ordered_types:
        grouped = transactions_by_type.get(tx_type, [])
        if not grouped:
            continue
        if tx_type == "stock":
            headers, rows = _build_stock_table(grouped, stock_orders)
        elif tx_type == "option":
            headers, rows = _build_option_table(grouped, option_orders, legs_by_order)
        elif tx_type == "dividend":
            headers, rows = _build_dividend_table(grouped)
        elif tx_type == "transfer":
            headers, rows = _build_transfer_table(grouped)
        elif tx_type == "crypto":
            headers, rows = _build_crypto_table(grouped)
        else:
            headers, rows = _build_base_table(grouped)

        tables.append(
            TransactionTable(
                transaction_type=tx_type,
                headers=headers,
                rows=rows,
            )
        )

    return tables


def list_positions(storage: Optional[Storage] = None) -> list[Position]:
    """Return all positions."""
    storage = storage or Storage()
    repo = PositionRepository(storage)
    return repo.find_all()


def _build_stock_table(
    grouped: list[Transaction], stock_orders: dict[str, StockOrder]
) -> tuple[list[str], list[list[str]]]:
    """Build table rows for stock transactions."""
    headers = ["Symbol", "Side", "Qty", "Price", "Avg Price", "Created At", "Source ID"]
    rows: list[list[str]] = []
    for tx in grouped:
        raw = tx.get_raw_data_dict()
        order = stock_orders.get(tx.id)
        symbol = getattr(order, "symbol", None) or str(raw.get("symbol", ""))
        side = getattr(order, "side", None) or str(raw.get("side", ""))
        quantity = getattr(order, "quantity", None) or raw.get("quantity", "")
        price = getattr(order, "price", None) or raw.get("price", "")
        avg_price = getattr(order, "average_price", None) or raw.get("average_price", "")
        rows.append(
            [
                str(symbol),
                str(side),
                str(quantity),
                str(price),
                str(avg_price),
                tx.created_at,
                tx.source_id,
            ]
        )
    return headers, rows


def _format_option_strategy(order: Optional[OptionOrder], raw: dict) -> str:
    """Compose option strategy display."""
    opening = getattr(order, "opening_strategy", None) or raw.get("opening_strategy") or ""
    closing = getattr(order, "closing_strategy", None) or raw.get("closing_strategy") or ""
    if opening and closing:
        return f"{opening} / {closing}"
    if opening:
        return str(opening)
    if closing:
        return str(closing)
    return ""


def _format_option_legs(legs: list[OptionLeg]) -> str:
    """Summarize option legs into a compact string."""
    segments: list[str] = []
    for leg in legs:
        segments.append(
            f"{leg.side} {leg.position_effect} {leg.ratio_quantity}x "
            f"{leg.strike_price} {leg.option_type.upper()} {leg.expiration_date}"
        )
    return " | ".join(segments)


def _build_option_table(
    grouped: list[Transaction],
    option_orders: dict[str, OptionOrder],
    legs_by_order: dict[str, list[OptionLeg]],
) -> tuple[list[str], list[list[str]]]:
    """Build table rows for option transactions."""
    headers = [
        "Chain",
        "Direction",
        "Strategy",
        "Premium",
        "Net Amount",
        "Legs",
        "Created At",
        "Source ID",
    ]
    rows: list[list[str]] = []
    for tx in grouped:
        raw = tx.get_raw_data_dict()
        order = option_orders.get(tx.id)
        chain = getattr(order, "chain_symbol", None) or raw.get("chain_symbol", "")
        direction = getattr(order, "direction", None) or raw.get("direction", "")
        premium = getattr(order, "premium", None) or raw.get("premium", "")
        net_amount = getattr(order, "net_amount", None) or raw.get("net_amount", "")
        legs = legs_by_order.get(tx.id, [])
        legs_summary = _format_option_legs(legs)

        rows.append(
            [
                str(chain),
                str(direction),
                _format_option_strategy(order, raw),
                str(premium),
                str(net_amount),
                legs_summary,
                tx.created_at,
                tx.source_id,
            ]
        )
    return headers, rows


def _build_dividend_table(grouped: list[Transaction]) -> tuple[list[str], list[list[str]]]:
    """Build table rows for dividend transactions."""
    headers = [
        "Amount",
        "Instrument",
        "Payable Date",
        "Record Date",
        "State",
        "Created At",
        "Source ID",
    ]
    rows: list[list[str]] = []
    for tx in grouped:
        raw = tx.get_raw_data_dict()
        rows.append(
            [
                str(raw.get("amount", "")),
                str(raw.get("instrument", raw.get("symbol", ""))),
                str(raw.get("payable_date", "")),
                str(raw.get("record_date", "")),
                str(raw.get("state", "")),
                tx.created_at,
                tx.source_id,
            ]
        )
    return headers, rows


def _build_transfer_table(grouped: list[Transaction]) -> tuple[list[str], list[list[str]]]:
    """Build table rows for transfer transactions."""
    headers = [
        "Direction",
        "Amount",
        "State",
        "Expected Landing",
        "Created At",
        "Source ID",
    ]
    rows: list[list[str]] = []
    for tx in grouped:
        raw = tx.get_raw_data_dict()
        expected_landing = raw.get("expected_landing_datetime") or raw.get(
            "expected_landing_date", ""
        )
        rows.append(
            [
                str(raw.get("direction", "")),
                str(raw.get("amount", "")),
                str(raw.get("state", raw.get("rhs_state", ""))),
                str(expected_landing),
                tx.created_at,
                tx.source_id,
            ]
        )
    return headers, rows


def _build_crypto_table(grouped: list[Transaction]) -> tuple[list[str], list[list[str]]]:
    """Build table rows for crypto transactions."""
    headers = [
        "Currency",
        "Side",
        "Qty",
        "Price",
        "Avg Price",
        "State",
        "Created At",
        "Source ID",
    ]
    rows: list[list[str]] = []
    for tx in grouped:
        raw = tx.get_raw_data_dict()
        rows.append(
            [
                str(raw.get("currency_code", raw.get("symbol", ""))),
                str(raw.get("side", "")),
                str(raw.get("quantity", "")),
                str(raw.get("price", "")),
                str(raw.get("average_price", "")),
                str(raw.get("state", "")),
                tx.created_at,
                tx.source_id,
            ]
        )
    return headers, rows


def _build_base_table(grouped: list[Transaction]) -> tuple[list[str], list[list[str]]]:
    """Fallback table for unknown transaction types."""
    headers = ["ID", "Type", "Source", "Created At", "Source ID"]
    rows: list[list[str]] = []
    for tx in grouped:
        rows.append([tx.id, tx.type, tx.source, tx.created_at, tx.source_id])
    return headers, rows
