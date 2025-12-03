"""Tests for data validation module."""

import pytest

from tradedata.data.models import (
    Execution,
    OptionLeg,
    OptionOrder,
    Position,
    StockOrder,
    Transaction,
    TransactionLink,
)
from tradedata.data.validator import (
    ValidationError,
    validate_execution,
    validate_option_leg,
    validate_option_order,
    validate_position,
    validate_stock_order,
    validate_transaction,
    validate_transaction_link,
)


class TestTransactionValidation:
    """Tests for transaction validation."""

    def test_valid_transaction(self):
        """Test validation of valid transaction."""
        tx = Transaction(
            id="550e8400-e29b-41d4-a716-446655440000",
            source="robinhood",
            source_id="order-123",
            type="stock",
            created_at="2025-12-01T10:00:00Z",
            account_id="account-456",
            raw_data='{"symbol": "AAPL"}',
        )
        # Should not raise
        validate_transaction(tx)

    def test_transaction_missing_id(self):
        """Test validation fails with missing id."""
        tx = Transaction(
            id="",
            source="robinhood",
            source_id="order-123",
            type="stock",
            created_at="2025-12-01T10:00:00Z",
            account_id=None,
            raw_data="{}",
        )
        with pytest.raises(ValidationError, match="Transaction.id"):
            validate_transaction(tx)

    def test_transaction_invalid_uuid(self):
        """Test validation fails with invalid UUID."""
        tx = Transaction(
            id="not-a-uuid",
            source="robinhood",
            source_id="order-123",
            type="stock",
            created_at="2025-12-01T10:00:00Z",
            account_id=None,
            raw_data="{}",
        )
        with pytest.raises(ValidationError, match="invalid UUID format"):
            validate_transaction(tx)

    def test_transaction_invalid_timestamp(self):
        """Test validation fails with invalid timestamp."""
        tx = Transaction(
            id="550e8400-e29b-41d4-a716-446655440000",
            source="robinhood",
            source_id="order-123",
            type="stock",
            created_at="not-a-timestamp",
            account_id=None,
            raw_data="{}",
        )
        with pytest.raises(ValidationError, match="created_at.*invalid ISO"):
            validate_transaction(tx)

    def test_transaction_timestamp_with_z(self):
        """Test validation accepts timestamp with Z suffix."""
        tx = Transaction(
            id="550e8400-e29b-41d4-a716-446655440000",
            source="robinhood",
            source_id="order-123",
            type="stock",
            created_at="2025-12-01T10:00:00Z",
            account_id=None,
            raw_data="{}",
        )
        validate_transaction(tx)


class TestOptionOrderValidation:
    """Tests for option order validation."""

    def test_valid_option_order(self):
        """Test validation of valid option order."""
        order = OptionOrder(
            id="550e8400-e29b-41d4-a716-446655440000",
            chain_symbol="AAPL 250117C150",
            opening_strategy="vertical_call_spread",
            closing_strategy=None,
            direction="debit",
            premium=100.0,
            net_amount=-100.0,
        )
        validate_option_order(order)

    def test_option_order_missing_chain_symbol(self):
        """Test validation fails with missing chain_symbol."""
        order = OptionOrder(
            id="550e8400-e29b-41d4-a716-446655440000",
            chain_symbol="",
            opening_strategy=None,
            closing_strategy=None,
            direction=None,
            premium=None,
            net_amount=None,
        )
        with pytest.raises(ValidationError, match="chain_symbol"):
            validate_option_order(order)


class TestOptionLegValidation:
    """Tests for option leg validation."""

    def test_valid_option_leg(self):
        """Test validation of valid option leg."""
        leg = OptionLeg(
            id="550e8400-e29b-41d4-a716-446655440000",
            order_id="550e8400-e29b-41d4-a716-446655440001",
            strike_price=150.0,
            expiration_date="2025-01-17",
            option_type="call",
            side="buy",
            position_effect="open",
            ratio_quantity=1,
        )
        validate_option_leg(leg)

    def test_option_leg_invalid_option_type(self):
        """Test validation fails with invalid option_type."""
        leg = OptionLeg(
            id="550e8400-e29b-41d4-a716-446655440000",
            order_id="550e8400-e29b-41d4-a716-446655440001",
            strike_price=150.0,
            expiration_date="2025-01-17",
            option_type="invalid",
            side="buy",
            position_effect="open",
            ratio_quantity=1,
        )
        with pytest.raises(ValidationError, match="option_type.*call.*put"):
            validate_option_leg(leg)

    def test_option_leg_invalid_side(self):
        """Test validation fails with invalid side."""
        leg = OptionLeg(
            id="550e8400-e29b-41d4-a716-446655440000",
            order_id="550e8400-e29b-41d4-a716-446655440001",
            strike_price=150.0,
            expiration_date="2025-01-17",
            option_type="call",
            side="invalid",
            position_effect="open",
            ratio_quantity=1,
        )
        with pytest.raises(ValidationError, match="side.*buy.*sell"):
            validate_option_leg(leg)

    def test_option_leg_negative_strike(self):
        """Test validation fails with negative strike price."""
        leg = OptionLeg(
            id="550e8400-e29b-41d4-a716-446655440000",
            order_id="550e8400-e29b-41d4-a716-446655440001",
            strike_price=-150.0,
            expiration_date="2025-01-17",
            option_type="call",
            side="buy",
            position_effect="open",
            ratio_quantity=1,
        )
        with pytest.raises(ValidationError, match="strike_price.*positive"):
            validate_option_leg(leg)

    def test_option_leg_zero_ratio_quantity(self):
        """Test validation fails with zero ratio_quantity."""
        leg = OptionLeg(
            id="550e8400-e29b-41d4-a716-446655440000",
            order_id="550e8400-e29b-41d4-a716-446655440001",
            strike_price=150.0,
            expiration_date="2025-01-17",
            option_type="call",
            side="buy",
            position_effect="open",
            ratio_quantity=0,
        )
        with pytest.raises(ValidationError, match="ratio_quantity.*positive"):
            validate_option_leg(leg)


class TestExecutionValidation:
    """Tests for execution validation."""

    def test_valid_execution(self):
        """Test validation of valid execution."""
        execution = Execution(
            id="550e8400-e29b-41d4-a716-446655440000",
            order_id="550e8400-e29b-41d4-a716-446655440001",
            leg_id="550e8400-e29b-41d4-a716-446655440002",
            price=150.0,
            quantity=10.0,
            timestamp="2025-12-01T10:30:00Z",
            settlement_date="2025-12-03",
        )
        validate_execution(execution)

    def test_execution_negative_price(self):
        """Test validation fails with negative price."""
        execution = Execution(
            id="550e8400-e29b-41d4-a716-446655440000",
            order_id="550e8400-e29b-41d4-a716-446655440001",
            leg_id=None,
            price=-150.0,
            quantity=10.0,
            timestamp="2025-12-01T10:30:00Z",
            settlement_date=None,
        )
        with pytest.raises(ValidationError, match="price.*non-negative"):
            validate_execution(execution)

    def test_execution_zero_quantity(self):
        """Test validation fails with zero quantity."""
        execution = Execution(
            id="550e8400-e29b-41d4-a716-446655440000",
            order_id="550e8400-e29b-41d4-a716-446655440001",
            leg_id=None,
            price=150.0,
            quantity=0.0,
            timestamp="2025-12-01T10:30:00Z",
            settlement_date=None,
        )
        with pytest.raises(ValidationError, match="quantity.*positive"):
            validate_execution(execution)


class TestStockOrderValidation:
    """Tests for stock order validation."""

    def test_valid_stock_order(self):
        """Test validation of valid stock order."""
        order = StockOrder(
            id="550e8400-e29b-41d4-a716-446655440000",
            symbol="AAPL",
            side="buy",
            quantity=100.0,
            price=150.0,
            average_price=150.5,
        )
        validate_stock_order(order)

    def test_stock_order_invalid_side(self):
        """Test validation fails with invalid side."""
        order = StockOrder(
            id="550e8400-e29b-41d4-a716-446655440000",
            symbol="AAPL",
            side="invalid",
            quantity=100.0,
            price=None,
            average_price=None,
        )
        with pytest.raises(ValidationError, match="side.*buy.*sell"):
            validate_stock_order(order)

    def test_stock_order_zero_quantity(self):
        """Test validation fails with zero quantity."""
        order = StockOrder(
            id="550e8400-e29b-41d4-a716-446655440000",
            symbol="AAPL",
            side="buy",
            quantity=0.0,
            price=None,
            average_price=None,
        )
        with pytest.raises(ValidationError, match="quantity.*positive"):
            validate_stock_order(order)


class TestPositionValidation:
    """Tests for position validation."""

    def test_valid_position(self):
        """Test validation of valid position."""
        position = Position(
            id="550e8400-e29b-41d4-a716-446655440000",
            source="robinhood",
            symbol="AAPL",
            quantity=100.0,
            cost_basis=15000.0,
            current_price=150.0,
            unrealized_pnl=100.0,
            last_updated="2025-12-01T10:00:00Z",
        )
        validate_position(position)

    def test_position_missing_symbol(self):
        """Test validation fails with missing symbol."""
        position = Position(
            id="550e8400-e29b-41d4-a716-446655440000",
            source="robinhood",
            symbol="",
            quantity=100.0,
            cost_basis=None,
            current_price=None,
            unrealized_pnl=None,
            last_updated="2025-12-01T10:00:00Z",
        )
        with pytest.raises(ValidationError, match="symbol"):
            validate_position(position)


class TestTransactionLinkValidation:
    """Tests for transaction link validation."""

    def test_valid_transaction_link(self):
        """Test validation of valid transaction link."""
        link = TransactionLink(
            id="550e8400-e29b-41d4-a716-446655440000",
            opening_transaction_id="550e8400-e29b-41d4-a716-446655440001",
            closing_transaction_id="550e8400-e29b-41d4-a716-446655440002",
            link_type="spread",
            created_at="2025-12-01T10:00:00Z",
        )
        validate_transaction_link(link)

    def test_transaction_link_same_ids(self):
        """Test validation fails when opening and closing IDs are same."""
        link = TransactionLink(
            id="550e8400-e29b-41d4-a716-446655440000",
            opening_transaction_id="550e8400-e29b-41d4-a716-446655440001",
            closing_transaction_id="550e8400-e29b-41d4-a716-446655440001",
            link_type=None,
            created_at="2025-12-01T10:00:00Z",
        )
        with pytest.raises(
            ValidationError, match="opening_transaction_id.*closing_transaction_id.*different"
        ):
            validate_transaction_link(link)
