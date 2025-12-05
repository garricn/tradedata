"""Tests for Robinhood adapter."""

import json
from unittest.mock import MagicMock

import pytest

from tradedata.sources.robinhood import RobinhoodAdapter


class TestRobinhoodAdapter:
    """Tests for RobinhoodAdapter class."""

    def test_init_without_credentials(self):
        """Test adapter initialization without credentials."""
        mock_rh = MagicMock()
        adapter = RobinhoodAdapter(robin_stocks=mock_rh)
        assert adapter.username is None
        assert adapter.password is None
        assert adapter.rh is mock_rh

    def test_init_with_credentials(self):
        """Test adapter initialization with credentials."""
        mock_rh = MagicMock()
        adapter = RobinhoodAdapter(username="test_user", password="test_pass", robin_stocks=mock_rh)
        assert adapter.username == "test_user"
        assert adapter.password == "test_pass"
        assert adapter.rh is mock_rh
        mock_rh.login.assert_called_once_with("test_user", "test_pass")

    def test_extract_transactions(self):
        """Test extracting transactions from Robinhood API."""
        mock_rh = MagicMock()
        mock_rh.get_all_stock_orders.return_value = [
            {"id": "stock-1", "symbol": "AAPL", "created_at": "2025-01-01T10:00:00Z"},
        ]
        mock_rh.get_all_option_orders.return_value = [
            {"id": "option-1", "legs": [], "created_at": "2025-01-02T10:00:00Z"},
        ]

        adapter = RobinhoodAdapter(robin_stocks=mock_rh)
        transactions = adapter.extract_transactions()

        assert len(transactions) == 2
        assert transactions[0]["id"] == "stock-1"
        assert transactions[1]["id"] == "option-1"
        mock_rh.get_all_stock_orders.assert_called_once()
        mock_rh.get_all_option_orders.assert_called_once()

    def test_extract_transactions_with_date_filter(self):
        """Test extracting transactions with date filtering."""
        mock_rh = MagicMock()
        mock_rh.get_all_stock_orders.return_value = [
            {"id": "stock-1", "symbol": "AAPL", "created_at": "2025-01-15T10:00:00Z"},
            {"id": "stock-2", "symbol": "MSFT", "created_at": "2025-02-15T10:00:00Z"},
        ]
        mock_rh.get_all_option_orders.return_value = []

        adapter = RobinhoodAdapter(robin_stocks=mock_rh)
        transactions = adapter.extract_transactions(start_date="2025-01-20", end_date="2025-02-10")

        # Only stock-2 should be in range
        assert len(transactions) == 0  # stock-1 is before start, stock-2 is after end

    def test_extract_positions(self):
        """Test extracting positions from Robinhood API."""
        mock_rh = MagicMock()
        mock_rh.get_open_stock_positions.return_value = [
            {"symbol": "AAPL", "quantity": "10.0", "cost_basis": "150.0"},
        ]
        mock_rh.get_open_option_positions.return_value = [
            {"symbol": "AAPL250120C150", "quantity": "5.0"},
        ]

        adapter = RobinhoodAdapter(robin_stocks=mock_rh)
        positions = adapter.extract_positions()

        assert len(positions) == 2
        assert positions[0]["symbol"] == "AAPL"
        assert positions[1]["symbol"] == "AAPL250120C150"

    def test_normalize_transaction_stock(self):
        """Test normalizing a stock transaction."""
        raw_tx = {
            "id": "rh-stock-123",
            "symbol": "AAPL",
            "side": "buy",
            "quantity": "10.0",
            "price": "150.0",
            "created_at": "2025-01-15T10:00:00Z",
            "account": "acc-123",
        }

        mock_rh = MagicMock()
        adapter = RobinhoodAdapter(robin_stocks=mock_rh)
        transaction = adapter.normalize_transaction(raw_tx)

        assert transaction.source == "robinhood"
        assert transaction.source_id == "rh-stock-123"
        assert transaction.type == "stock"
        assert transaction.created_at == "2025-01-15T10:00:00Z"
        assert transaction.account_id == "acc-123"
        assert json.loads(transaction.raw_data) == raw_tx

    def test_normalize_transaction_option(self):
        """Test normalizing an option transaction."""
        raw_tx = {
            "id": "rh-option-456",
            "legs": [],
            "chain_symbol": "AAPL",
            "created_at": "2025-01-15T10:00:00Z",
        }

        mock_rh = MagicMock()
        adapter = RobinhoodAdapter(robin_stocks=mock_rh)
        transaction = adapter.normalize_transaction(raw_tx)

        assert transaction.source == "robinhood"
        assert transaction.source_id == "rh-option-456"
        assert transaction.type == "option"

    def test_extract_option_order(self):
        """Test extracting OptionOrder from raw transaction."""
        raw_tx = {
            "id": "rh-option-789",
            "legs": [],
            "chain_symbol": "AAPL",
            "opening_strategy": "vertical_call_spread",
            "closing_strategy": None,
            "direction": "debit",
            "premium": "2.50",
            "net_amount": "-250.00",
        }

        mock_rh = MagicMock()
        adapter = RobinhoodAdapter(robin_stocks=mock_rh)
        transaction = adapter.normalize_transaction(raw_tx)
        option_order = adapter.extract_option_order(raw_tx, transaction.id)

        assert option_order is not None
        assert option_order.id == transaction.id
        assert option_order.chain_symbol == "AAPL"
        assert option_order.opening_strategy == "vertical_call_spread"
        assert option_order.direction == "debit"
        assert option_order.premium == 2.50
        assert option_order.net_amount == -250.00

    def test_extract_option_legs(self):
        """Test extracting OptionLeg models from raw transaction."""
        raw_tx = {
            "id": "rh-option-789",
            "legs": [
                {
                    "strike_price": "150.0",
                    "expiration_date": "2025-01-17",
                    "option_type": "call",
                    "side": "buy",
                    "position_effect": "open",
                    "ratio_quantity": 1,
                },
                {
                    "strike_price": "155.0",
                    "expiration_date": "2025-01-17",
                    "option_type": "call",
                    "side": "sell",
                    "position_effect": "open",
                    "ratio_quantity": 1,
                },
            ],
        }

        mock_rh = MagicMock()
        adapter = RobinhoodAdapter(robin_stocks=mock_rh)
        transaction = adapter.normalize_transaction(raw_tx)
        option_order = adapter.extract_option_order(raw_tx, transaction.id)
        order_id = option_order.id if option_order else transaction.id
        legs = adapter.extract_option_legs(raw_tx, order_id)

        assert len(legs) == 2
        assert legs[0].strike_price == 150.0
        assert legs[0].option_type == "call"
        assert legs[0].side == "buy"
        assert legs[1].strike_price == 155.0
        assert legs[1].side == "sell"

    def test_extract_executions(self):
        """Test extracting Execution models from raw transaction."""
        raw_tx = {
            "id": "rh-order-123",
            "executions": [
                {
                    "price": "2.50",
                    "quantity": "10.0",
                    "timestamp": "2025-01-15T10:05:00Z",
                },
                {
                    "price": "2.55",
                    "quantity": "5.0",
                    "timestamp": "2025-01-15T10:10:00Z",
                },
            ],
        }

        mock_rh = MagicMock()
        adapter = RobinhoodAdapter(robin_stocks=mock_rh)
        transaction = adapter.normalize_transaction(raw_tx)
        executions = adapter.extract_executions(raw_tx, transaction.id)

        assert len(executions) == 2
        assert executions[0].price == 2.50
        assert executions[0].quantity == 10.0
        assert executions[1].price == 2.55
        assert executions[1].quantity == 5.0

    def test_extract_stock_order(self):
        """Test extracting StockOrder from raw transaction."""
        raw_tx = {
            "id": "rh-stock-123",
            "symbol": "AAPL",
            "side": "buy",
            "quantity": "10.0",
            "price": "150.0",
            "average_price": "150.5",
        }

        mock_rh = MagicMock()
        adapter = RobinhoodAdapter(robin_stocks=mock_rh)
        transaction = adapter.normalize_transaction(raw_tx)
        stock_order = adapter.extract_stock_order(raw_tx, transaction.id)

        assert stock_order is not None
        assert stock_order.id == transaction.id
        assert stock_order.symbol == "AAPL"
        assert stock_order.side == "buy"
        assert stock_order.quantity == 10.0
        assert stock_order.price == 150.0
        assert stock_order.average_price == 150.5

    def test_extract_stock_order_missing_symbol_raises(self):
        """StockOrder extraction should fail when symbol is missing."""
        raw_tx = {
            "id": "rh-stock-123",
            "side": "buy",
            "quantity": "10.0",
            "price": "150.0",
            "average_price": "150.5",
        }

        mock_rh = MagicMock()
        adapter = RobinhoodAdapter(robin_stocks=mock_rh)
        transaction = adapter.normalize_transaction(raw_tx)

        with pytest.raises(ValueError):
            adapter.extract_stock_order(raw_tx, transaction.id)

    def test_normalize_position(self):
        """Test normalizing a position."""
        raw_position = {
            "symbol": "AAPL",
            "quantity": "10.0",
            "cost_basis": "150.0",
            "current_price": "155.0",
            "unrealized_pnl": "50.0",
            "updated_at": "2025-01-15T10:00:00Z",
        }

        mock_rh = MagicMock()
        adapter = RobinhoodAdapter(robin_stocks=mock_rh)
        position = adapter.normalize_position(raw_position)

        assert position.source == "robinhood"
        assert position.symbol == "AAPL"
        assert position.quantity == 10.0
        assert position.cost_basis == 150.0
        assert position.current_price == 155.0
        assert position.unrealized_pnl == 50.0

    def test_determine_transaction_type(self):
        """Test determining transaction type from raw data."""
        mock_rh = MagicMock()
        adapter = RobinhoodAdapter(robin_stocks=mock_rh)

        # Option transaction
        option_tx = {"legs": []}
        assert adapter._determine_transaction_type(option_tx) == "option"

        # Stock transaction
        stock_tx = {"symbol": "AAPL"}
        assert adapter._determine_transaction_type(stock_tx) == "stock"

        # Crypto transaction
        crypto_tx = {"type": "crypto_purchase"}
        assert adapter._determine_transaction_type(crypto_tx) == "crypto"

        # Dividend transaction
        dividend_tx = {"type": "dividend"}
        assert adapter._determine_transaction_type(dividend_tx) == "dividend"

    def test_extract_timestamp(self):
        """Test extracting timestamp from raw transaction."""
        mock_rh = MagicMock()
        adapter = RobinhoodAdapter(robin_stocks=mock_rh)

        # Test with created_at
        tx1 = {"created_at": "2025-01-15T10:00:00Z"}
        assert adapter._extract_timestamp(tx1) == "2025-01-15T10:00:00Z"

        # Test with updated_at
        tx2 = {"updated_at": "2025-01-15T11:00:00Z"}
        assert adapter._extract_timestamp(tx2) == "2025-01-15T11:00:00Z"

        # Test with no timestamp (should default to current time)
        tx3 = {}
        timestamp = adapter._extract_timestamp(tx3)
        assert timestamp is not None
        assert "Z" in timestamp or "+" in timestamp
