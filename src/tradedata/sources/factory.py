"""Factory pattern for creating data source adapters.

Provides a unified way to create and register data source adapters.
"""

from typing import Any, Optional, Type

from tradedata.sources.base import DataSourceAdapter


class SourceFactory:
    """Factory for creating data source adapters.

    Supports registering new source types and creating adapter instances.
    Designed to be easily extended for future sources (IBKR, TD Ameritrade, etc.).

    Example:
        # Register a new source type
        factory = SourceFactory()
        factory.register('robinhood', RobinhoodAdapter)

        # Create an adapter instance
        adapter = factory.create_adapter('robinhood')
    """

    def __init__(self):
        """Initialize factory with empty registry."""
        self._registry: dict[str, Type[DataSourceAdapter]] = {}

    def register(self, source_name: str, adapter_class: Type[DataSourceAdapter]) -> None:
        """Register a new source adapter type.

        Args:
            source_name: Name of the source (e.g., 'robinhood', 'ibkr')
            adapter_class: Adapter class that implements DataSourceAdapter

        Raises:
            ValueError: If source_name is already registered.
            TypeError: If adapter_class does not implement DataSourceAdapter.
        """
        if source_name in self._registry:
            raise ValueError(f"Source '{source_name}' is already registered")

        if not issubclass(adapter_class, DataSourceAdapter):
            raise TypeError(
                f"Adapter class must implement DataSourceAdapter, got {adapter_class.__name__}"
            )

        self._registry[source_name] = adapter_class

    def create_adapter(self, source_name: str, *args: Any, **kwargs: Any) -> DataSourceAdapter:
        """Create an adapter instance for the specified source.

        Args:
            source_name: Name of the source (e.g., 'robinhood', 'ibkr')
            *args: Positional arguments to pass to adapter constructor
            **kwargs: Keyword arguments to pass to adapter constructor

        Returns:
            Adapter instance for the specified source.

        Raises:
            ValueError: If source_name is not registered.
        """
        if source_name not in self._registry:
            available = ", ".join(self._registry.keys()) if self._registry else "none"
            raise ValueError(
                f"Source '{source_name}' is not registered. Available sources: {available}"
            )

        adapter_class = self._registry[source_name]
        return adapter_class(*args, **kwargs)

    def is_registered(self, source_name: str) -> bool:
        """Check if a source is registered.

        Args:
            source_name: Name of the source to check.

        Returns:
            True if source is registered, False otherwise.
        """
        return source_name in self._registry

    def list_sources(self) -> list[str]:
        """List all registered source names.

        Returns:
            List of registered source names.
        """
        return list(self._registry.keys())


# Global factory instance
_default_factory: Optional[SourceFactory] = None


def get_factory() -> SourceFactory:
    """Get the default global factory instance.

    Returns:
        Global SourceFactory instance.
    """
    global _default_factory
    if _default_factory is None:
        _default_factory = SourceFactory()
    return _default_factory


def create_adapter(source_name: str, *args: Any, **kwargs: Any) -> DataSourceAdapter:
    """Convenience function to create an adapter using the default factory.

    Args:
        source_name: Name of the source (e.g., 'robinhood', 'ibkr')
        *args: Positional arguments to pass to adapter constructor
        **kwargs: Keyword arguments to pass to adapter constructor

    Returns:
        Adapter instance for the specified source.

    Raises:
        ValueError: If source_name is not registered.
    """
    return get_factory().create_adapter(source_name, *args, **kwargs)
