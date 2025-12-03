"""Tests for repository dependency injection."""

import json

from tradedata.data.models import Transaction
from tradedata.data.repositories import TransactionRepository
from tradedata.data.storage import Storage


class TestRepositoryDependencyInjection:
    """Tests for repository dependency injection."""

    def test_repositories_use_injected_storage(self):
        """Test that repositories use the injected storage instance."""
        storage1 = Storage(db_path=":memory:")
        storage2 = Storage(db_path=":memory:")

        repo1 = TransactionRepository(storage1)
        repo2 = TransactionRepository(storage2)

        tx = Transaction(
            id="tx-1",
            source="robinhood",
            source_id="rh-123",
            type="option",
            created_at="2025-12-02T10:00:00Z",
            account_id="acc-123",
            raw_data=json.dumps({}),
        )

        repo1.create(tx)

        # tx should be in storage1 but not storage2
        assert repo1.get_by_id("tx-1") is not None
        assert repo2.get_by_id("tx-1") is None

        storage1.close()
        storage2.close()
