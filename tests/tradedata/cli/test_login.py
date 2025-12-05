"""Tests for CLI login command."""

from click.testing import CliRunner

from tradedata.application import CredentialsNotFoundError
from tradedata.cli.main import cli


def test_login_uses_stored_credentials(monkeypatch):
    """If stored creds exist, reuse them without prompting."""
    calls = {}

    def fake_create_adapter(source, username=None, password=None):
        calls["create_adapter"] = (source, username, password)
        return object()

    def fake_get_credentials(source):
        return ("cached@example.com", "cachedpass")

    def fake_store_credentials(source, email, password):
        calls["store_credentials"] = (source, email, password)

    monkeypatch.setattr(
        "tradedata.cli.commands.login.create_adapter",
        fake_create_adapter,
    )
    monkeypatch.setattr(
        "tradedata.cli.commands.login.credentials.get_credentials",
        fake_get_credentials,
    )
    monkeypatch.setattr(
        "tradedata.cli.commands.login.credentials.store_credentials",
        fake_store_credentials,
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["login", "robinhood"])

    assert result.exit_code == 0
    assert calls["create_adapter"] == ("robinhood", "cached@example.com", "cachedpass")
    assert calls["store_credentials"] == ("robinhood", "cached@example.com", "cachedpass")


def test_login_prompts_when_missing(monkeypatch):
    """Prompts when no stored credentials and then stores them."""
    calls = {}

    def fake_create_adapter(source, username=None, password=None):
        calls["create_adapter"] = (source, username, password)
        return object()

    def fake_get_credentials(source):
        raise CredentialsNotFoundError("no creds")

    def fake_store_credentials(source, email, password):
        calls["store_credentials"] = (source, email, password)

    monkeypatch.setattr(
        "tradedata.cli.commands.login.create_adapter",
        fake_create_adapter,
    )
    monkeypatch.setattr(
        "tradedata.cli.commands.login.credentials.get_credentials",
        fake_get_credentials,
    )
    monkeypatch.setattr(
        "tradedata.cli.commands.login.credentials.store_credentials",
        fake_store_credentials,
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["login", "robinhood"], input="user@example.com\nsecret\n")

    assert result.exit_code == 0
    assert "Logged in to robinhood" in result.output
    assert calls["create_adapter"] == ("robinhood", "user@example.com", "secret")
    assert calls["store_credentials"] == ("robinhood", "user@example.com", "secret")


def test_login_force_reprompts_even_with_stored(monkeypatch):
    """Force flag should re-prompt even if stored creds exist."""
    calls = {}

    def fake_create_adapter(source, username=None, password=None):
        calls["create_adapter"] = (source, username, password)
        return object()

    def fake_get_credentials(source):
        return ("cached@example.com", "cachedpass")

    def fake_store_credentials(source, email, password):
        calls["store_credentials"] = (source, email, password)

    monkeypatch.setattr(
        "tradedata.cli.commands.login.create_adapter",
        fake_create_adapter,
    )
    monkeypatch.setattr(
        "tradedata.cli.commands.login.credentials.get_credentials",
        fake_get_credentials,
    )
    monkeypatch.setattr(
        "tradedata.cli.commands.login.credentials.store_credentials",
        fake_store_credentials,
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["login", "robinhood", "--force"],
        input="fresh@example.com\nnewpass\n",
    )

    assert result.exit_code == 0
    assert calls["create_adapter"] == ("robinhood", "fresh@example.com", "newpass")
    assert calls["store_credentials"] == ("robinhood", "fresh@example.com", "newpass")


def test_login_failure_does_not_store(monkeypatch):
    """If login fails, exit non-zero and do not store credentials."""
    calls = {}

    def fake_create_adapter(source, username=None, password=None):
        raise RuntimeError("boom")

    def fake_get_credentials(source):
        raise CredentialsNotFoundError("no creds")

    def fake_store_credentials(source, email, password):
        calls["store_credentials"] = True

    monkeypatch.setattr(
        "tradedata.cli.commands.login.create_adapter",
        fake_create_adapter,
    )
    monkeypatch.setattr(
        "tradedata.cli.commands.login.credentials.get_credentials",
        fake_get_credentials,
    )
    monkeypatch.setattr(
        "tradedata.cli.commands.login.credentials.store_credentials",
        fake_store_credentials,
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["login", "robinhood"], input="user@example.com\nsecret\n")

    assert result.exit_code != 0
    assert "failed to login" in result.output
    assert "store_credentials" not in calls
