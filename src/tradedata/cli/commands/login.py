"""Login command for establishing and storing credentials."""

from typing import Optional

import click

from tradedata.application import CredentialsNotFoundError, credentials
from tradedata.sources import create_adapter


@click.command()
@click.argument("source", default="robinhood")
@click.option("--email", help="Account email; prompts if not provided.")
@click.option(
    "--password",
    help="Account password; prompts if not provided.",
    hide_input=True,
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Re-prompt and overwrite stored credentials even if found in keyring.",
)
def login(
    source: str,
    email: Optional[str] = None,
    password: Optional[str] = None,
    force: bool = False,
) -> None:
    """Login to a data source and store credentials securely."""

    email_value = email
    password_value = password

    if not force and not email_value and not password_value:
        try:
            stored_email, stored_password = credentials.get_credentials(source)
            email_value = stored_email
            password_value = stored_password
        except CredentialsNotFoundError:
            # No stored credentials; will prompt below
            pass

    if email_value is None:
        email_value = click.prompt("Email")
    if password_value is None:
        password_value = click.prompt("Password", hide_input=True)

    try:
        # Attempt login (adapters handle session/MFA flows)
        create_adapter(source, username=email_value, password=password_value)
    except Exception as exc:  # pragma: no cover - pass through unknown adapter errors
        click.echo(f"Error: failed to login to {source}: {exc}", err=True)
        raise SystemExit(1) from exc

    # Only store credentials after successful login
    credentials.store_credentials(source, email_value, password_value)
    click.echo(f"Logged in to {source} and stored credentials securely.")
