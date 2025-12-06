"""Show commands for transactions and positions."""

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
def show_transactions(
    transaction_types: tuple[str, ...],
    days: Optional[int],
    raw: bool,
    last: Optional[int],
) -> None:
    """Show stored transactions with optional filters."""
    tx_types = _parse_types_option(transaction_types)
    if raw:
        transactions = listing.list_transactions(transaction_types=tx_types, days=days, last=last)
        if not transactions:
            click.echo("No transactions found.")
            return

        rows: list[list[str]] = []
        for tx in transactions:
            rows.append([tx.id, tx.type, tx.source, tx.created_at, tx.source_id])

        output = _table(
            ["ID", "Type", "Source", "Created At", "Source ID"],
            rows,
        )
        click.echo(output)
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
