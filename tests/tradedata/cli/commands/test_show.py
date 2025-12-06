"""Tests for CLI show commands."""

from datetime import datetime, timezone

from click.testing import CliRunner

from tradedata.application.listing import TransactionTable
from tradedata.cli.main import cli
from tradedata.data.models import Position, Transaction


def test_show_transactions_invokes_listing(monkeypatch):
    """Ensure CLI passes filters to application layer and prints rows."""
    now = datetime.now(timezone.utc)
    tx = Transaction(
        id="tx-recent",
        source="robinhood",
        source_id="rh-1",
        type="stock",
        created_at=now.isoformat(),
        account_id=None,
        raw_data="{}",
    )

    captured = {}

    def fake_list_enriched(transaction_types=None, days=None, storage=None):
        captured["transaction_types"] = transaction_types
        captured["days"] = days
        return [
            TransactionTable(
                transaction_type="stock",
                headers=["ID", "Type"],
                rows=[[tx.id, tx.type]],
            )
        ]

    monkeypatch.setattr(
        "tradedata.cli.commands.show.listing.list_enriched_transaction_tables",
        fake_list_enriched,
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["show", "transactions", "--type", "stock,crypto", "--days", "10"])

    assert result.exit_code == 0
    assert captured["transaction_types"] == ["stock", "crypto"]
    assert captured["days"] == 10
    assert "tx-recent" in result.output
    assert "stock" in result.output


def test_show_positions_invokes_listing(monkeypatch):
    """Ensure CLI prints positions returned by application layer."""
    position = Position(
        id="pos-1",
        source="robinhood",
        symbol="AAPL",
        quantity=10.0,
        cost_basis=150.0,
        current_price=155.0,
        unrealized_pnl=50.0,
        last_updated=datetime.now(timezone.utc).isoformat(),
    )

    def fake_list_positions():
        return [position]

    monkeypatch.setattr(
        "tradedata.cli.commands.show.listing.list_positions",
        fake_list_positions,
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["show", "positions"])

    assert result.exit_code == 0
    assert "AAPL" in result.output
    assert "pos-1" in result.output
