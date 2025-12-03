"""Tests for source factory pattern."""

from typing import Any, Optional

import pytest

from tradedata.data.models import Transaction
from tradedata.sources.base import DataSourceAdapter
from tradedata.sources.factory import SourceFactory, create_adapter, get_factory


class MockAdapter(DataSourceAdapter):
    """Mock adapter for testing."""

    def __init__(self, test_param: str = "default"):
        """Initialize mock adapter."""
        self.test_param = test_param

    def extract_transactions(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """Extract transactions (mock)."""
        return [{"id": "test-1", "source": "mock"}]

    def extract_positions(self) -> list[dict[str, Any]]:
        """Extract positions (mock)."""
        return [{"symbol": "AAPL", "quantity": 10}]

    def normalize_transaction(self, raw_transaction: dict[str, Any]) -> Transaction:
        """Normalize transaction (mock)."""
        return Transaction(
            id="normalized-1",
            source="mock",
            source_id="test-1",
            type="option",
            created_at="2025-12-02T10:00:00Z",
            account_id=None,
            raw_data="{}",
        )


class TestSourceFactory:
    """Tests for SourceFactory class."""

    def test_register_and_create_adapter(self):
        """Test registering and creating an adapter."""
        factory = SourceFactory()
        factory.register("mock", MockAdapter)

        adapter = factory.create_adapter("mock")
        assert isinstance(adapter, MockAdapter)

    def test_register_with_constructor_args(self):
        """Test creating adapter with constructor arguments."""
        factory = SourceFactory()
        factory.register("mock", MockAdapter)

        adapter = factory.create_adapter("mock", test_param="custom")
        assert adapter.test_param == "custom"

    def test_register_duplicate_raises_error(self):
        """Test that registering duplicate source raises ValueError."""
        factory = SourceFactory()
        factory.register("mock", MockAdapter)

        with pytest.raises(ValueError, match="already registered"):
            factory.register("mock", MockAdapter)

    def test_register_invalid_class_raises_error(self):
        """Test that registering non-adapter class raises TypeError."""
        factory = SourceFactory()

        class NotAnAdapter:
            pass

        with pytest.raises(TypeError, match="must implement DataSourceAdapter"):
            factory.register("invalid", NotAnAdapter)

    def test_create_unregistered_adapter_raises_error(self):
        """Test that creating unregistered adapter raises ValueError."""
        factory = SourceFactory()

        with pytest.raises(ValueError, match="not registered"):
            factory.create_adapter("nonexistent")

    def test_is_registered(self):
        """Test checking if source is registered."""
        factory = SourceFactory()
        assert factory.is_registered("mock") is False

        factory.register("mock", MockAdapter)
        assert factory.is_registered("mock") is True

    def test_list_sources(self):
        """Test listing registered sources."""
        factory = SourceFactory()
        assert factory.list_sources() == []

        factory.register("mock1", MockAdapter)
        factory.register("mock2", MockAdapter)

        sources = factory.list_sources()
        assert "mock1" in sources
        assert "mock2" in sources
        assert len(sources) == 2

    def test_multiple_adapters_same_class(self):
        """Test registering multiple adapters with same class."""
        factory = SourceFactory()
        factory.register("mock1", MockAdapter)
        factory.register("mock2", MockAdapter)

        adapter1 = factory.create_adapter("mock1")
        adapter2 = factory.create_adapter("mock2")

        assert isinstance(adapter1, MockAdapter)
        assert isinstance(adapter2, MockAdapter)
        # They should be different instances
        assert adapter1 is not adapter2


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_get_factory_returns_singleton(self):
        """Test that get_factory returns the same instance."""
        factory1 = get_factory()
        factory2 = get_factory()
        assert factory1 is factory2

    def test_create_adapter_convenience_function(self):
        """Test the create_adapter convenience function."""
        factory = get_factory()
        factory.register("mock", MockAdapter)

        adapter = create_adapter("mock")
        assert isinstance(adapter, MockAdapter)

    def test_create_adapter_with_args(self):
        """Test create_adapter with constructor arguments."""
        factory = get_factory()
        # Use a different source name since 'mock' might already be registered
        factory.register("mock_with_args", MockAdapter)

        adapter = create_adapter("mock_with_args", test_param="convenience")
        assert adapter.test_param == "convenience"
