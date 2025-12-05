"""Show commands for transactions and positions."""

from typing import Iterable

import click
from rich import box
from rich.console import Console
from rich.table import Table

from tradedata.application import listing


def _table(headers: list[str], rows: Iterable[list[str]]) -> str:
    """Render a simple table using rich."""
    table = Table(show_header=True, header_style="bold", box=box.SIMPLE)
    for header in headers:
        table.add_column(header)
    for row in rows:
        table.add_row(*row)

    console = Console(
        force_terminal=False,
        color_system=None,
        width=120,
        soft_wrap=True,
        record=True,
    )
    console.print(table)
    output = console.export_text()
    return str(output)


@click.group(name="show")
def show() -> None:
    """Show data from the local database."""


@show.command("transactions")
@click.option(
    "--type",
    "transaction_type",
    type=click.Choice(["stock", "option"]),
    help="Filter by transaction type.",
)
@click.option(
    "--days",
    type=int,
    help="Only include transactions from the past N days.",
)
def show_transactions(transaction_type: str | None, days: int | None) -> None:
    """Show stored transactions with optional filters."""
    transactions = listing.list_transactions(transaction_type=transaction_type, days=days)
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
