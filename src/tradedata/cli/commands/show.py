"""Show commands for transactions and positions."""

import json
from io import StringIO
from typing import Iterable, Optional

import click
from rich import box
from rich.console import Console
from rich.table import Table

from tradedata.application import listing


def _table(headers: list[str], rows: Iterable[list[str]]) -> str:
    """Render a simple table using rich."""
    table = Table(show_header=True, header_style="bold", box=box.SIMPLE, expand=True)
    for header in headers:
        table.add_column(header, overflow="fold")
    for row in rows:
        table.add_row(*row)

    buffer = StringIO()
    console = Console(
        force_terminal=False,
        color_system=None,
        width=120,
        soft_wrap=True,
        record=True,
        file=buffer,
    )
    console.print(table)
    output = buffer.getvalue()
    return str(output).rstrip()


def _detail_table(fields: list[tuple[str, str]]) -> str:
    """Render key/value transaction detail table."""
    table = Table(show_header=True, header_style="bold", box=box.SIMPLE, expand=True)
    table.add_column("Field", overflow="fold")
    table.add_column("Value", overflow="fold")
    for field, value in fields:
        table.add_row(field, value)

    buffer = StringIO()
    console = Console(
        force_terminal=False,
        color_system=None,
        width=120,
        soft_wrap=True,
        record=True,
        file=buffer,
    )
    console.print(table)
    output = buffer.getvalue()
    return str(output).rstrip()


@click.group(name="show")
def show() -> None:
    """Show data from the local database."""


@show.command("transactions")
@click.option(
    "--type",
    "transaction_types",
    multiple=True,
    help=(
        "Filter by transaction types (repeatable or comma-separated, "
        "e.g., --type stock,option or --type stock --type option)."
    ),
)
@click.option(
    "--days",
    type=int,
    help="Only include transactions from the past N days.",
)
@click.option(
    "--raw",
    is_flag=True,
    help="Show the base transaction view instead of enriched, type-specific tables.",
)
@click.option(
    "--last",
    type=click.IntRange(min=1),
    help="Show only the most recent N transactions (after other filters).",
)
@click.option(
    "--id",
    "transaction_ids",
    multiple=True,
    help="Show specific transaction(s) by ID (ignores other filters).",
)
@click.option(
    "--source-id",
    "source_ids",
    multiple=True,
    help="Show transaction(s) by source ID (mutually exclusive with --id).",
)
def show_transactions(
    transaction_types: tuple[str, ...],
    days: Optional[int],
    raw: bool,
    transaction_ids: tuple[str, ...],
    source_ids: tuple[str, ...],
    last: Optional[int],
) -> None:
    """Show stored transactions with optional filters."""
    if transaction_ids and source_ids:
        raise click.UsageError("Use either --id or --source-id, not both.")

    if transaction_ids or source_ids:
        details = listing.get_transaction_details(
            ids=list(transaction_ids) if transaction_ids else None,
            source_ids=list(source_ids) if source_ids else None,
        )
        if not details:
            click.echo("No transactions found.")
            return

        for idx, detail in enumerate(details):
            click.echo(f"Transaction {detail.transaction_id}")
            click.echo(_detail_table(detail.fields))
            if idx < len(details) - 1:
                click.echo()
        return

    tx_types = _parse_types_option(transaction_types)
    if raw:
        transactions = listing.list_transactions(transaction_types=tx_types, days=days, last=last)
        if not transactions:
            click.echo("No transactions found.")
            return

        for tx in transactions:
            merged = {
                "id": tx.id,
                "source": tx.source,
                "source_id": tx.source_id,
                "type": tx.type,
                "created_at": tx.created_at,
                "account_id": tx.account_id,
            }
            raw_dict = tx.get_raw_data_dict()
            for key, value in raw_dict.items():
                merged[f"raw.{key}"] = value
            click.echo(json.dumps(merged, indent=2, sort_keys=True))
            click.echo()
        return

    tables = listing.list_enriched_transaction_tables(
        transaction_types=tx_types, days=days, last=last
    )
    if not tables:
        click.echo("No transactions found.")
        return

    for idx, table in enumerate(tables):
        click.echo(f"{table.transaction_type.capitalize()} transactions")
        click.echo(_table(table.headers, table.rows))
        if idx < len(tables) - 1:
            click.echo()


@show.command("positions")
def show_positions() -> None:
    """Show stored positions."""
    positions = listing.list_positions()
    if not positions:
        click.echo("No positions found.")
        return

    rows: list[list[str]] = []
    for pos in positions:
        rows.append(
            [
                pos.id,
                pos.symbol,
                str(pos.quantity),
                str(pos.cost_basis),
                str(pos.current_price),
                pos.source,
            ]
        )

    output = _table(
        ["ID", "Symbol", "Quantity", "Cost Basis", "Current Price", "Source"],
        rows,
    )
    click.echo(output)


def _parse_types_option(types: Optional[tuple[str, ...]]) -> Optional[list[str]]:
    """Flatten repeatable/CSV types into a list."""
    if not types:
        return None
    flattened: list[str] = []
    for entry in types:
        parts = [part.strip() for part in entry.replace(",", " ").split() if part.strip()]
        flattened.extend(parts)
    return flattened or None
