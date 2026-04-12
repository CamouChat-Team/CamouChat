from typing import List, Dict, Any, Protocol, Sequence
from .message import MessageProtocol


class StorageProtocol(Protocol):
    """Base contract for storage implementations.

    All storage backends (SQLite, PostgreSQL, MongoDB, etc.) must implement
    this interface to provide consistent batching, lookup, retrieval, and
    cleanup behavior. Concrete classes own logger defaults and backend-specific
    configuration.
    """

    async def init_db(self, **kwargs) -> None:
        """Initialize database connection."""
        ...

    async def create_table(self, **kwargs) -> None:
        """Create required tables/collections."""
        ...

    async def start_writer(self, **kwargs) -> None:
        """Start background writer task for batch processing."""
        ...

    async def enqueue_insert(self, msgs: Sequence[MessageProtocol], **kwargs) -> None:
        """Add messages to queue for batch insertion."""
        ...

    async def _insert_batch_internally(self, msgs: Sequence[MessageProtocol], **kwargs) -> None:
        """Internal method to insert a batch of messages."""
        ...

    def check_message_if_exists(self, msg_id: str, **kwargs) -> bool:
        """Check if a message exists by ID."""
        ...

    async def check_message_if_exists_async(self, msg_id: str, **kwargs) -> bool:
        """Check if a message exists by ID asynchronously."""
        ...

    def get_all_messages(self, **kwargs) -> List[Dict[str, Any]]:
        """Retrieve all messages from storage."""
        ...

    async def close_db(self, **kwargs) -> None:
        """Close database connection and cleanup resources."""
        ...
