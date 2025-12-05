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
def sync_transactions(
    source: str, start_date: Optional[str] = None, end_date: Optional[str] = None
) -> None:
    """Sync transactions into the local database."""
    transactions = robinhood_sync.sync_transactions(
        source=source, start_date=start_date, end_date=end_date
    )
    click.echo(f"Synced {len(transactions)} transactions from {source}.")


@sync.command("positions")
@click.option("--source", default="robinhood", help="Data source name.")
def sync_positions(source: str) -> None:
    """Sync positions into the local database."""
    positions = robinhood_sync.sync_positions(source=source)
    click.echo(f"Synced {len(positions)} positions from {source}.")
