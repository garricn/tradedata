"""CLI entrypoint for tradedata."""

import click

from tradedata.cli.commands.login import login
from tradedata.cli.commands.show import show
from tradedata.cli.commands.sync import sync


@click.group()
def cli() -> None:
    """TradeData CLI: sync and inspect trading data."""


# Register subcommands
cli.add_command(login)
cli.add_command(sync)
cli.add_command(show)


if __name__ == "__main__":
    cli()
