"""Storage Interface - Abstract base for all storage implementations."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any

from src.Interfaces.message_interface import MessageInterface


class StorageInterface(ABC):
    """
    Abstract base class for storage implementations.

    All storage backends (SQLite, PostgreSQL, MongoDB, etc.) must implement
    this interface to ensure consistent behavior across the SDK.
    """

    def __init__(self, queue: asyncio.Queue, log: logging.Logger, **kwargs) -> None:
        """
        Initialize storage with a queue for batch operations.

        Args:
            queue: Async queue for message batching
            log: Logger instance
            **kwargs: Additional implementation-specific options
        """
        self.queue = queue
        self.log = log

    @abstractmethod
    async def init_db(self, **kwargs) -> None:
        """Initialize database connection."""
        ...

    @abstractmethod
    async def create_table(self, **kwargs) -> None:
        """Create required tables/collections."""
        ...

    @abstractmethod
    async def start_writer(self, **kwargs) -> None:
        """Start background writer task for batch processing."""
        ...

    @abstractmethod
    async def enqueue_insert(self, msgs: List[MessageInterface], **kwargs) -> None:
        """
        Add messages to queue for batch insertion.

        Args:
            msgs: List of messages to insert
        """
        ...

    @abstractmethod
    async def _insert_batch_internally(self, msgs: List[MessageInterface], **kwargs) -> None:
        """
        Internal method to insert a batch of messages.

        Args:
            msgs: List of messages to insert
        """
        ...

    @abstractmethod
    def check_message_if_exists(self, msg_id: str, **kwargs) -> bool:
        """
        Check if a message exists by ID.

        Args:
            msg_id: Message identifier

        Returns:
            True if message exists, False otherwise
        """
        ...

    @abstractmethod
    async def check_message_if_exists_async(self, msg_id: str, **kwargs) -> bool:
        """
        Check if a message exists by ID asynchronously.

        Args:
            msg_id: Message identifier

        Returns:
            True if message exists, False otherwise
        """
        ...

    @abstractmethod
    def get_all_messages(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Retrieve all messages from storage.

        Args:
            **kwargs: Optional limit, offset for pagination

        Returns:
            List of message dictionaries
        """
        ...

    @abstractmethod
    async def close_db(self, **kwargs) -> None:
        """Close database connection and cleanup resources."""
        ...
