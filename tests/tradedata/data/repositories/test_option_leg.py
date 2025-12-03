"""Tests for OptionLegRepository."""

import json

from tradedata.data.models import OptionLeg, OptionOrder, Transaction
from tradedata.data.repositories import (
    OptionLegRepository,
    OptionOrderRepository,
    TransactionRepository,
)
from tradedata.data.storage import Storage


class TestOptionLegRepository:
    """Tests for OptionLegRepository."""

    def test_create_and_get_by_id(self):
        """Test creating and retrieving an option leg."""
        storage = Storage(db_path=":memory:")
        tx_repo = TransactionRepository(storage)
        order_repo = OptionOrderRepository(storage)
        repo = OptionLegRepository(storage)

        # Create parent transaction and option order first
        transaction = Transaction(
            id="order-1",
            source="robinhood",
            source_id="rh-123",
            type="option",
            created_at="2025-12-02T10:00:00Z",
            account_id="acc-123",
            raw_data=json.dumps({}),
        )
        tx_repo.create(transaction)

        order = OptionOrder(
            id="order-1",
            chain_symbol="AAPL",
            opening_strategy="vertical_call_spread",
            closing_strategy=None,
            direction="debit",
            premium=100.50,
            net_amount=-100.50,
        )
        order_repo.create(order)

        leg = OptionLeg(
            id="leg-1",
            order_id="order-1",
            strike_price=150.0,
            expiration_date="2025-12-19",
            option_type="call",
            side="buy",
            position_effect="open",
            ratio_quantity=1,
        )

        created = repo.create(leg)
        assert created.id == leg.id

        retrieved = repo.get_by_id("leg-1")
        assert retrieved is not None
        assert retrieved.strike_price == 150.0
        assert retrieved.option_type == "call"

        storage.close()

    def test_find_by_order_id(self):
        """Test finding option legs by order ID."""
        storage = Storage(db_path=":memory:")
        tx_repo = TransactionRepository(storage)
        order_repo = OptionOrderRepository(storage)
        repo = OptionLegRepository(storage)

        # Create parent transactions and option orders first
        for order_id in ["order-1", "order-2"]:
            transaction = Transaction(
                id=order_id,
                source="robinhood",
                source_id=f"rh-{order_id}",
                type="option",
                created_at="2025-12-02T10:00:00Z",
                account_id="acc-123",
                raw_data=json.dumps({}),
            )
            tx_repo.create(transaction)

            order = OptionOrder(
                id=order_id,
                chain_symbol="AAPL",
                opening_strategy="vertical_call_spread",
                closing_strategy=None,
                direction="debit",
                premium=100.50,
                net_amount=-100.50,
            )
            order_repo.create(order)

        leg1 = OptionLeg(
            id="leg-1",
            order_id="order-1",
            strike_price=150.0,
            expiration_date="2025-12-19",
            option_type="call",
            side="buy",
            position_effect="open",
            ratio_quantity=1,
        )
        leg2 = OptionLeg(
            id="leg-2",
            order_id="order-1",
            strike_price=155.0,
            expiration_date="2025-12-19",
            option_type="call",
            side="sell",
            position_effect="open",
            ratio_quantity=1,
        )
        leg3 = OptionLeg(
            id="leg-3",
            order_id="order-2",
            strike_price=160.0,
            expiration_date="2025-12-19",
            option_type="put",
            side="buy",
            position_effect="open",
            ratio_quantity=1,
        )

        repo.create(leg1)
        repo.create(leg2)
        repo.create(leg3)

        order1_legs = repo.find_by_order_id("order-1")
        assert len(order1_legs) == 2

        storage.close()
