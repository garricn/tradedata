"""Base repository class for all entity repositories."""

from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

from tradedata.data.storage import Storage

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Abstract base repository for all entity repositories.

    Provides common CRUD operations that can be overridden by subclasses.
    """

    def __init__(self, storage: Storage):
        """Initialize repository with storage dependency.

        Args:
            storage: Storage instance for database operations.
        """
        self.storage = storage

    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get entity by ID.

        Args:
            entity_id: Entity identifier.

        Returns:
            Entity instance, or None if not found.
        """
        pass

    @abstractmethod
    def create(self, entity: T) -> T:
        """Create a new entity.

        Args:
            entity: Entity instance to create.

        Returns:
            Created entity instance.
        """
        pass

    @abstractmethod
    def update(self, entity: T) -> T:
        """Update an existing entity.

        Args:
            entity: Entity instance with updated data.

        Returns:
            Updated entity instance.
        """
        pass

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Delete an entity by ID.

        Args:
            entity_id: Entity identifier.

        Returns:
            True if deleted, False if not found.
        """
        pass

    @abstractmethod
    def find_all(self) -> list[T]:
        """Find all entities.

        Returns:
            List of all entity instances.
        """
        pass
