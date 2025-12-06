"""Tests for CLI sync commands."""

from click.testing import CliRunner

from tradedata.cli.main import cli


def test_sync_transactions_invokes_app(monkeypatch):
    """Ensure CLI calls app sync_transactions with options."""
    calls = {}

    def fake_sync_transactions(source, start_date=None, end_date=None, types=None):
        calls["sync_transactions"] = (source, start_date, end_date, types)
        return [{"id": "tx1"}, {"id": "tx2"}]

    monkeypatch.setattr(
        "tradedata.cli.commands.sync.robinhood_sync.sync_transactions",
        fake_sync_transactions,
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "sync",
            "transactions",
            "--source",
            "robinhood",
            "--start-date",
            "2025-01-01",
            "--end-date",
            "2025-02-01",
            "--types",
            "stock",
            "--types",
            "option",
        ],
    )

    assert result.exit_code == 0
    assert calls["sync_transactions"] == (
        "robinhood",
        "2025-01-01",
        "2025-02-01",
        ["stock", "option"],
    )
    assert "Synced 2 transactions" in result.output


def test_sync_positions_invokes_app(monkeypatch):
    """Ensure CLI calls app sync_positions."""
    calls = {}

    def fake_sync_positions(source):
        calls["sync_positions"] = source
        return [{"id": "pos1"}]

    monkeypatch.setattr(
        "tradedata.cli.commands.sync.robinhood_sync.sync_positions",
        fake_sync_positions,
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["sync", "positions", "--source", "robinhood"])

    assert result.exit_code == 0
    assert calls["sync_positions"] == "robinhood"
    assert "Synced 1 positions" in result.output
