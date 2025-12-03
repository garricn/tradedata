"""Tests for data models."""

import json

from tradedata.data.models import (
    Execution,
    OptionLeg,
    OptionOrder,
    Position,
    StockOrder,
    Transaction,
    TransactionLink,
)


def test_transaction_model():
    """Test Transaction model creation and serialization."""
    raw_data = {"key": "value", "number": 123}
    transaction = Transaction(
        id="test-id-123",
        source="robinhood",
        source_id="rh-123",
        type="option",
        created_at="2025-12-02T10:00:00Z",
        account_id="acc-123",
        raw_data=json.dumps(raw_data),
    )

    # Test to_db_tuple
    db_tuple = transaction.to_db_tuple()
    assert db_tuple == (
        "test-id-123",
        "robinhood",
        "rh-123",
        "option",
        "2025-12-02T10:00:00Z",
        "acc-123",
        json.dumps(raw_data),
    )

    # Test from_db_row
    transaction2 = Transaction.from_db_row(db_tuple)
    assert transaction2.id == transaction.id
    assert transaction2.source == transaction.source
    assert transaction2.source_id == transaction.source_id
    assert transaction2.type == transaction.type
    assert transaction2.created_at == transaction.created_at
    assert transaction2.account_id == transaction.account_id
    assert transaction2.raw_data == transaction.raw_data

    # Test get_raw_data_dict
    assert transaction.get_raw_data_dict() == raw_data


def test_transaction_with_none_account_id():
    """Test Transaction with None account_id."""
    transaction = Transaction(
        id="test-id",
        source="robinhood",
        source_id="rh-123",
        type="option",
        created_at="2025-12-02T10:00:00Z",
        account_id=None,
        raw_data=json.dumps({}),
    )

    db_tuple = transaction.to_db_tuple()
    assert db_tuple[5] is None

    transaction2 = Transaction.from_db_row(db_tuple)
    assert transaction2.account_id is None


def test_option_order_model():
    """Test OptionOrder model creation and serialization."""
    option_order = OptionOrder(
        id="order-123",
        chain_symbol="AAPL",
        opening_strategy="vertical_call_spread",
        closing_strategy="vertical_call_spread",
        direction="debit",
        premium=100.50,
        net_amount=-100.50,
    )

    # Test to_db_tuple
    db_tuple = option_order.to_db_tuple()
    assert db_tuple == (
        "order-123",
        "AAPL",
        "vertical_call_spread",
        "vertical_call_spread",
        "debit",
        100.50,
        -100.50,
    )

    # Test from_db_row
    option_order2 = OptionOrder.from_db_row(db_tuple)
    assert option_order2.id == option_order.id
    assert option_order2.chain_symbol == option_order.chain_symbol
    assert option_order2.opening_strategy == option_order.opening_strategy
    assert option_order2.closing_strategy == option_order.closing_strategy
    assert option_order2.direction == option_order.direction
    assert option_order2.premium == option_order.premium
    assert option_order2.net_amount == option_order.net_amount


def test_option_order_with_none_fields():
    """Test OptionOrder with None optional fields."""
    option_order = OptionOrder(
        id="order-123",
        chain_symbol="AAPL",
        opening_strategy=None,
        closing_strategy=None,
        direction=None,
        premium=None,
        net_amount=None,
    )

    db_tuple = option_order.to_db_tuple()
    assert db_tuple[2] is None
    assert db_tuple[3] is None
    assert db_tuple[4] is None
    assert db_tuple[5] is None
    assert db_tuple[6] is None

    option_order2 = OptionOrder.from_db_row(db_tuple)
    assert option_order2.opening_strategy is None
    assert option_order2.closing_strategy is None
    assert option_order2.direction is None
    assert option_order2.premium is None
    assert option_order2.net_amount is None


def test_option_leg_model():
    """Test OptionLeg model creation and serialization."""
    option_leg = OptionLeg(
        id="leg-123",
        order_id="order-123",
        strike_price=150.0,
        expiration_date="2025-12-19",
        option_type="call",
        side="buy",
        position_effect="open",
        ratio_quantity=1,
    )

    # Test to_db_tuple
    db_tuple = option_leg.to_db_tuple()
    assert db_tuple == (
        "leg-123",
        "order-123",
        150.0,
        "2025-12-19",
        "call",
        "buy",
        "open",
        1,
    )

    # Test from_db_row
    option_leg2 = OptionLeg.from_db_row(db_tuple)
    assert option_leg2.id == option_leg.id
    assert option_leg2.order_id == option_leg.order_id
    assert option_leg2.strike_price == option_leg.strike_price
    assert option_leg2.expiration_date == option_leg.expiration_date
    assert option_leg2.option_type == option_leg.option_type
    assert option_leg2.side == option_leg.side
    assert option_leg2.position_effect == option_leg.position_effect
    assert option_leg2.ratio_quantity == option_leg.ratio_quantity


def test_execution_model():
    """Test Execution model creation and serialization."""
    execution = Execution(
        id="exec-123",
        order_id="order-123",
        leg_id="leg-123",
        price=2.50,
        quantity=10.0,
        timestamp="2025-12-02T10:00:00Z",
        settlement_date="2025-12-04",
    )

    # Test to_db_tuple
    db_tuple = execution.to_db_tuple()
    assert db_tuple == (
        "exec-123",
        "order-123",
        "leg-123",
        2.50,
        10.0,
        "2025-12-02T10:00:00Z",
        "2025-12-04",
    )

    # Test from_db_row
    execution2 = Execution.from_db_row(db_tuple)
    assert execution2.id == execution.id
    assert execution2.order_id == execution.order_id
    assert execution2.leg_id == execution.leg_id
    assert execution2.price == execution.price
    assert execution2.quantity == execution.quantity
    assert execution2.timestamp == execution.timestamp
    assert execution2.settlement_date == execution.settlement_date


def test_execution_with_none_leg_id():
    """Test Execution with None leg_id."""
    execution = Execution(
        id="exec-123",
        order_id="order-123",
        leg_id=None,
        price=2.50,
        quantity=10.0,
        timestamp="2025-12-02T10:00:00Z",
        settlement_date=None,
    )

    db_tuple = execution.to_db_tuple()
    assert db_tuple[2] is None
    assert db_tuple[6] is None

    execution2 = Execution.from_db_row(db_tuple)
    assert execution2.leg_id is None
    assert execution2.settlement_date is None


def test_stock_order_model():
    """Test StockOrder model creation and serialization."""
    stock_order = StockOrder(
        id="stock-order-123",
        symbol="AAPL",
        side="buy",
        quantity=100.0,
        price=150.0,
        average_price=149.50,
    )

    # Test to_db_tuple
    db_tuple = stock_order.to_db_tuple()
    assert db_tuple == ("stock-order-123", "AAPL", "buy", 100.0, 150.0, 149.50)

    # Test from_db_row
    stock_order2 = StockOrder.from_db_row(db_tuple)
    assert stock_order2.id == stock_order.id
    assert stock_order2.symbol == stock_order.symbol
    assert stock_order2.side == stock_order.side
    assert stock_order2.quantity == stock_order.quantity
    assert stock_order2.price == stock_order.price
    assert stock_order2.average_price == stock_order.average_price


def test_stock_order_with_none_fields():
    """Test StockOrder with None optional fields."""
    stock_order = StockOrder(
        id="stock-order-123",
        symbol="AAPL",
        side="buy",
        quantity=100.0,
        price=None,
        average_price=None,
    )

    db_tuple = stock_order.to_db_tuple()
    assert db_tuple[4] is None
    assert db_tuple[5] is None

    stock_order2 = StockOrder.from_db_row(db_tuple)
    assert stock_order2.price is None
    assert stock_order2.average_price is None


def test_position_model():
    """Test Position model creation and serialization."""
    position = Position(
        id="pos-123",
        source="robinhood",
        symbol="AAPL",
        quantity=100.0,
        cost_basis=15000.0,
        current_price=155.0,
        unrealized_pnl=500.0,
        last_updated="2025-12-02T10:00:00Z",
    )

    # Test to_db_tuple
    db_tuple = position.to_db_tuple()
    assert db_tuple == (
        "pos-123",
        "robinhood",
        "AAPL",
        100.0,
        15000.0,
        155.0,
        500.0,
        "2025-12-02T10:00:00Z",
    )

    # Test from_db_row
    position2 = Position.from_db_row(db_tuple)
    assert position2.id == position.id
    assert position2.source == position.source
    assert position2.symbol == position.symbol
    assert position2.quantity == position.quantity
    assert position2.cost_basis == position.cost_basis
    assert position2.current_price == position.current_price
    assert position2.unrealized_pnl == position.unrealized_pnl
    assert position2.last_updated == position.last_updated


def test_position_with_none_fields():
    """Test Position with None optional fields."""
    position = Position(
        id="pos-123",
        source="robinhood",
        symbol="AAPL",
        quantity=100.0,
        cost_basis=None,
        current_price=None,
        unrealized_pnl=None,
        last_updated="2025-12-02T10:00:00Z",
    )

    db_tuple = position.to_db_tuple()
    assert db_tuple[4] is None
    assert db_tuple[5] is None
    assert db_tuple[6] is None

    position2 = Position.from_db_row(db_tuple)
    assert position2.cost_basis is None
    assert position2.current_price is None
    assert position2.unrealized_pnl is None


def test_transaction_link_model():
    """Test TransactionLink model creation and serialization."""
    transaction_link = TransactionLink(
        id="link-123",
        opening_transaction_id="tx-open-123",
        closing_transaction_id="tx-close-123",
        link_type="spread",
        created_at="2025-12-02T10:00:00Z",
    )

    # Test to_db_tuple
    db_tuple = transaction_link.to_db_tuple()
    assert db_tuple == (
        "link-123",
        "tx-open-123",
        "tx-close-123",
        "spread",
        "2025-12-02T10:00:00Z",
    )

    # Test from_db_row
    transaction_link2 = TransactionLink.from_db_row(db_tuple)
    assert transaction_link2.id == transaction_link.id
    assert transaction_link2.opening_transaction_id == transaction_link.opening_transaction_id
    assert transaction_link2.closing_transaction_id == transaction_link.closing_transaction_id
    assert transaction_link2.link_type == transaction_link.link_type
    assert transaction_link2.created_at == transaction_link.created_at


def test_transaction_link_with_none_link_type():
    """Test TransactionLink with None link_type."""
    transaction_link = TransactionLink(
        id="link-123",
        opening_transaction_id="tx-open-123",
        closing_transaction_id="tx-close-123",
        link_type=None,
        created_at="2025-12-02T10:00:00Z",
    )

    db_tuple = transaction_link.to_db_tuple()
    assert db_tuple[3] is None

    transaction_link2 = TransactionLink.from_db_row(db_tuple)
    assert transaction_link2.link_type is None


def test_all_models_have_type_hints():
    """Test that all models have proper type hints."""
    # This is a structural test - if models don't have type hints,
    # mypy would catch it, but we can also verify the dataclass fields
    assert hasattr(Transaction, "__annotations__")
    assert hasattr(OptionOrder, "__annotations__")
    assert hasattr(OptionLeg, "__annotations__")
    assert hasattr(Execution, "__annotations__")
    assert hasattr(StockOrder, "__annotations__")
    assert hasattr(Position, "__annotations__")
    assert hasattr(TransactionLink, "__annotations__")


def test_models_round_trip_serialization():
    """Test that models can be serialized and deserialized correctly."""
    # Test Transaction
    transaction = Transaction(
        id="test-id",
        source="robinhood",
        source_id="rh-123",
        type="option",
        created_at="2025-12-02T10:00:00Z",
        account_id="acc-123",
        raw_data=json.dumps({"test": "data"}),
    )
    db_tuple = transaction.to_db_tuple()
    transaction2 = Transaction.from_db_row(db_tuple)
    assert transaction == transaction2

    # Test OptionOrder
    option_order = OptionOrder(
        id="order-123",
        chain_symbol="AAPL",
        opening_strategy="vertical_call_spread",
        closing_strategy=None,
        direction="debit",
        premium=100.50,
        net_amount=-100.50,
    )
    db_tuple = option_order.to_db_tuple()
    option_order2 = OptionOrder.from_db_row(db_tuple)
    assert option_order == option_order2
