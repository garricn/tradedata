import json
from pathlib import Path
from typing import Any

from click.testing import CliRunner

from tradedata.cli.main import cli
from tradedata.data.models import OptionLeg, OptionOrder, StockOrder, Transaction
from tradedata.data.repositories import (
    OptionLegRepository,
    OptionOrderRepository,
    StockOrderRepository,
    TransactionRepository,
)
from tradedata.data.storage import Storage


def _seed_transactions(db_path: Path) -> None:
    storage = Storage(str(db_path))
    tx_repo = TransactionRepository(storage)
    stock_repo = StockOrderRepository(storage)
    option_repo = OptionOrderRepository(storage)
    leg_repo = OptionLegRepository(storage)

    stock_raw = {
        "id": "stock-order-1",
        "symbol": "MSFT",
        "side": "buy",
        "quantity": "5",
        "price": "320.00",
        "average_price": "320.10",
        "created_at": "2025-12-01T10:00:00Z",
        "account": "acc-1",
    }
    stock_tx = Transaction(
        id="tx-stock",
        source="robinhood",
        source_id="stock-order-1",
        type="stock",
        created_at="2025-12-01T10:00:00Z",
        account_id="acc-1",
        raw_data=json.dumps(stock_raw),
    )
    tx_repo.create(stock_tx)
    stock_repo.create(
        StockOrder(
            id=stock_tx.id,
            symbol="MSFT",
            side="buy",
            quantity=5,
            price=320.0,
            average_price=320.10,
        )
    )

    option_raw: dict[str, Any] = {
        "id": "opt-order-1",
        "chain_symbol": "AAPL",
        "direction": "debit",
        "opening_strategy": "vertical_call_spread",
        "premium": "2.50",
        "net_amount": "-250.00",
        "legs": [
            {
                "id": "leg-1",
                "strike_price": "150.0",
                "expiration_date": "2025-12-19",
                "option_type": "call",
                "side": "buy",
                "position_effect": "open",
                "ratio_quantity": 1,
            },
            {
                "id": "leg-2",
                "strike_price": "155.0",
                "expiration_date": "2025-12-19",
                "option_type": "call",
                "side": "sell",
                "position_effect": "open",
                "ratio_quantity": 1,
            },
        ],
        "created_at": "2025-12-01T15:00:00Z",
        "account": "acc-1",
    }
    option_tx = Transaction(
        id="tx-option",
        source="robinhood",
        source_id="opt-order-1",
        type="option",
        created_at="2025-12-01T15:00:00Z",
        account_id="acc-1",
        raw_data=json.dumps(option_raw),
    )
    tx_repo.create(option_tx)
    option_repo.create(
        OptionOrder(
            id=option_tx.id,
            chain_symbol="AAPL",
            opening_strategy="vertical_call_spread",
            closing_strategy=None,
            direction="debit",
            premium=2.50,
            net_amount=-250.00,
        )
    )
    for raw_leg in option_raw["legs"]:
        leg_repo.create(
            OptionLeg(
                id=raw_leg["id"],
                order_id=option_tx.id,
                strike_price=float(raw_leg["strike_price"]),
                expiration_date=raw_leg["expiration_date"],
                option_type=raw_leg["option_type"],
                side=raw_leg["side"],
                position_effect=raw_leg["position_effect"],
                ratio_quantity=int(raw_leg["ratio_quantity"]),
            )
        )

    dividend_raw = {
        "id": "dividend-1",
        "amount": "3.00",
        "instrument": "https://api.robinhood.com/instruments/FAKE-INSTRUMENT/",
        "payable_date": "2025-12-26",
        "record_date": "2025-12-05",
        "state": "pending",
        "created_at": "2025-12-05T00:00:00Z",
    }
    dividend_tx = Transaction(
        id="tx-dividend",
        source="robinhood",
        source_id="dividend-1",
        type="dividend",
        created_at="2025-12-05T00:00:00Z",
        account_id="acc-1",
        raw_data=json.dumps(dividend_raw),
    )
    tx_repo.create(dividend_tx)

    transfer_raw = {
        "id": "transfer-1",
        "direction": "deposit",
        "amount": "100.00",
        "state": "completed",
        "expected_landing_date": "2025-06-02",
        "created_at": "2025-05-29T19:28:55.118509-04:00",
    }
    transfer_tx = Transaction(
        id="tx-transfer",
        source="robinhood",
        source_id="transfer-1",
        type="transfer",
        created_at="2025-05-29T19:28:55.118509-04:00",
        account_id="acc-1",
        raw_data=json.dumps(transfer_raw),
    )
    tx_repo.create(transfer_tx)


def test_show_transactions_enriched(tmp_path) -> None:
    db_path = tmp_path / "tradedata.db"
    _seed_transactions(db_path)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["show", "transactions"],
        env={"TRADEDATA_DB_PATH": str(db_path)},
    )

    assert result.exit_code == 0
    output = result.output
    assert "Stock transactions" in output
    assert "MSFT" in output
    assert "Option transactions" in output
    assert "AAPL" in output
    assert "buy open 1x 150.0" in output
    assert "CALL 2025-12-19" in output
    assert "Dividend transactions" in output
    assert "3.00" in output
    assert "Transfer transactions" in output
    assert "deposit" in output


def test_show_transactions_raw_flag(tmp_path) -> None:
    db_path = tmp_path / "tradedata.db"
    _seed_transactions(db_path)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["show", "transactions", "--raw"],
        env={"TRADEDATA_DB_PATH": str(db_path)},
    )

    assert result.exit_code == 0
    output = result.output
    assert '"raw.symbol": "MSFT"' in output
    assert '"type": "stock"' in output
    assert '"id": "tx-stock"' in output
    assert "Stock transactions" not in output


def test_show_transactions_last_uses_enriched(monkeypatch):
    """`--last` should invoke enriched table rendering (non-raw)."""

    calls = {}

    def fake_list_enriched_transaction_tables(transaction_types=None, days=None, last=None):
        calls["args"] = {
            "transaction_types": transaction_types,
            "days": days,
            "last": last,
        }
        return [
            type(
                "Table",
                (),
                {
                    "transaction_type": "stock",
                    "headers": ["Symbol", "Side"],
                    "rows": [["AAPL", "buy"]],
                },
            )()
        ]

    monkeypatch.setattr(
        "tradedata.application.listing.list_enriched_transaction_tables",
        fake_list_enriched_transaction_tables,
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["show", "transactions", "--last", "1"])

    assert result.exit_code == 0
    assert "AAPL" in result.output
    assert calls["args"] == {"transaction_types": None, "days": None, "last": 1}


def test_show_transactions_last_requires_value(monkeypatch):
    """`--last` must be given a value (int > 0)."""

    runner = CliRunner()
    result = runner.invoke(cli, ["show", "transactions", "--last"])

    assert result.exit_code != 0
    assert "Error" in result.output
