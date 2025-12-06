"""Sync commands for transactions and positions."""

from typing import Optional

import click

from tradedata.application import robinhood_sync


@click.group()
def sync() -> None:
    """Sync data from brokers into the local database."""


@sync.command("transactions")
@click.option("--source", default="robinhood", help="Data source name.")
@click.option("--start-date", help="Optional start date (YYYY-MM-DD).")
@click.option("--end-date", help="Optional end date (YYYY-MM-DD).")
@click.option(
    "--types",
    "-t",
    multiple=True,
    help=(
        "Transaction types to include; repeat or comma-separate "
        "(e.g., --types stock,option,crypto or -t stock -t option)."
    ),
)
def sync_transactions(
    source: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    types: Optional[tuple[str, ...]] = None,
) -> None:
    """Sync transactions into the local database."""
    parsed_types = _parse_types_option(types)
    transactions = robinhood_sync.sync_transactions(
        source=source,
        start_date=start_date,
        end_date=end_date,
        types=parsed_types,
    )
    click.echo(f"Synced {len(transactions)} transactions from {source}.")


@sync.command("positions")
@click.option("--source", default="robinhood", help="Data source name.")
def sync_positions(source: str) -> None:
    """Sync positions into the local database."""
    positions = robinhood_sync.sync_positions(source=source)
    click.echo(f"Synced {len(positions)} positions from {source}.")


def _parse_types_option(types: Optional[tuple[str, ...]]) -> Optional[list[str]]:
    """Flatten repeatable/CSV types into a list."""
    if not types:
        return None
    flattened: list[str] = []
    for entry in types:
        parts = [part.strip() for part in entry.replace(",", " ").split() if part.strip()]
        flattened.extend(parts)
    return flattened or None
