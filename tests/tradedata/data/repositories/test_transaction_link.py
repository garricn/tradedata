"""Tests for TransactionLinkRepository."""

import json

from tradedata.data.models import Transaction, TransactionLink
from tradedata.data.repositories import TransactionLinkRepository, TransactionRepository
from tradedata.data.storage import Storage


class TestTransactionLinkRepository:
    """Tests for TransactionLinkRepository."""

    def test_create_and_get_by_id(self):
        """Test creating and retrieving a transaction link."""
        storage = Storage(db_path=":memory:")
        tx_repo = TransactionRepository(storage)
        repo = TransactionLinkRepository(storage)

        # Create parent transactions first
        for tx_id in ["tx-open-1", "tx-close-1"]:
            transaction = Transaction(
                id=tx_id,
                source="robinhood",
                source_id=f"rh-{tx_id}",
                type="option",
                created_at="2025-12-02T10:00:00Z",
                account_id="acc-123",
                raw_data=json.dumps({}),
            )
            tx_repo.create(transaction)

        link = TransactionLink(
            id="link-1",
            opening_transaction_id="tx-open-1",
            closing_transaction_id="tx-close-1",
            link_type="spread",
            created_at="2025-12-02T10:00:00Z",
        )

        created = repo.create(link)
        assert created.id == link.id

        retrieved = repo.get_by_id("link-1")
        assert retrieved is not None
        assert retrieved.link_type == "spread"

        storage.close()

    def test_find_by_opening_transaction(self):
        """Test finding links by opening transaction ID."""
        storage = Storage(db_path=":memory:")
        tx_repo = TransactionRepository(storage)
        repo = TransactionLinkRepository(storage)

        # Create parent transactions first
        for tx_id in ["tx-open-1", "tx-close-1", "tx-close-2"]:
            transaction = Transaction(
                id=tx_id,
                source="robinhood",
                source_id=f"rh-{tx_id}",
                type="option",
                created_at="2025-12-02T10:00:00Z",
                account_id="acc-123",
                raw_data=json.dumps({}),
            )
            tx_repo.create(transaction)

        link1 = TransactionLink(
            id="link-1",
            opening_transaction_id="tx-open-1",
            closing_transaction_id="tx-close-1",
            link_type="spread",
            created_at="2025-12-02T10:00:00Z",
        )
        link2 = TransactionLink(
            id="link-2",
            opening_transaction_id="tx-open-1",
            closing_transaction_id="tx-close-2",
            link_type="spread",
            created_at="2025-12-02T11:00:00Z",
        )

        repo.create(link1)
        repo.create(link2)

        opening_links = repo.find_by_opening_transaction("tx-open-1")
        assert len(opening_links) == 2

        storage.close()

    def test_find_by_closing_transaction(self):
        """Test finding links by closing transaction ID."""
        storage = Storage(db_path=":memory:")
        tx_repo = TransactionRepository(storage)
        repo = TransactionLinkRepository(storage)

        # Create parent transactions first
        for tx_id in ["tx-open-1", "tx-close-1"]:
            transaction = Transaction(
                id=tx_id,
                source="robinhood",
                source_id=f"rh-{tx_id}",
                type="option",
                created_at="2025-12-02T10:00:00Z",
                account_id="acc-123",
                raw_data=json.dumps({}),
            )
            tx_repo.create(transaction)

        link = TransactionLink(
            id="link-1",
            opening_transaction_id="tx-open-1",
            closing_transaction_id="tx-close-1",
            link_type="spread",
            created_at="2025-12-02T10:00:00Z",
        )

        repo.create(link)

        closing_links = repo.find_by_closing_transaction("tx-close-1")
        assert len(closing_links) == 1
        assert closing_links[0].closing_transaction_id == "tx-close-1"

        storage.close()
