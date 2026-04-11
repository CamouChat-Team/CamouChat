"""Contracts for asynchronous message storage backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class StorageInterface(ABC):
    """Base contract for storage implementations.

    All storage backends (SQLite, PostgreSQL, MongoDB, etc.) must implement
    this interface to provide consistent batching, lookup, retrieval, and
    cleanup behavior. Concrete classes own logger defaults and backend-specific
    configuration.
    """

    @abstractmethod
    async def init_db(self) -> None:
        """Initialize database connection."""
        ...

    @abstractmethod
    async def create_table(self) -> None:
        """Create required tables/collections."""
        ...

    @abstractmethod
    async def start_writer(self) -> None:
        """Start background writer task for batch processing."""
        ...

    @abstractmethod
    async def enqueue_insert(self) -> None:
        """
        Add messages to queue for batch insertion.

        Args:
            msgs: List of messages to insert
        """
        ...

    @abstractmethod
    async def _insert_batch_internally(self) -> None:
        """
        Internal method to insert a batch of messages.

        Args:
            msgs: List of messages to insert
        """
        ...

    @abstractmethod
    def check_message_if_exists(self) -> bool:
        """
        Check if a message exists by ID.

        Args:
            msg_id: Message identifier

        Returns:
            True if message exists, False otherwise
        """
        ...

    @abstractmethod
    async def check_message_if_exists_async(self) -> bool:
        """
        Check if a message exists by ID asynchronously.

        Args:
            msg_id: Message identifier

        Returns:
            True if message exists, False otherwise
        """
        ...

    @abstractmethod
    def get_all_messages(self) -> List[Dict[str, Any]]:
        """
        Retrieve all messages from storage.

        Args:
            **kwargs: Optional limit, offset for pagination

        Returns:
            List of message dictionaries
        """
        ...

    @abstractmethod
    async def close_db(self) -> None:
        """Close database connection and cleanup resources."""
        ...
