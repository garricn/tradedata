"""Tests for CLI login command."""

from click.testing import CliRunner

from tradedata.cli.main import cli


def test_login_stores_credentials_and_logs_in(monkeypatch):
    """Happy path: prompts, logs in via adapter, then stores credentials."""
    calls = {}

    def fake_create_adapter(source, username=None, password=None):
        calls["create_adapter"] = (source, username, password)
        return object()

    def fake_store_credentials(source, email, password):
        calls["store_credentials"] = (source, email, password)

    monkeypatch.setattr(
        "tradedata.cli.commands.login.create_adapter",
        fake_create_adapter,
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


def test_login_failure_does_not_store(monkeypatch):
    """If login fails, exit non-zero and do not store credentials."""
    calls = {}

    def fake_create_adapter(source, username=None, password=None):
        raise RuntimeError("boom")

    def fake_store_credentials(source, email, password):
        calls["store_credentials"] = True

    monkeypatch.setattr(
        "tradedata.cli.commands.login.create_adapter",
        fake_create_adapter,
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
