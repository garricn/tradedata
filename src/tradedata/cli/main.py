"""CLI entrypoint for tradedata."""

import click

from tradedata.cli.commands.login import login


@click.group()
def cli() -> None:
    """TradeData CLI: sync and inspect trading data."""


# Register subcommands
cli.add_command(login)


if __name__ == "__main__":
    cli()
