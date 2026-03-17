from __future__ import annotations

from typing import Sequence, List, Dict, Any

from camouchat.Filter.message_filter import MessageFilter
from camouchat.Interfaces.message_interface import MessageInterface
from camouchat.Interfaces.storage_interface import StorageInterface


# -----------------------------
# NoOp Filter
# -----------------------------
class NoOpMessageFilter(MessageFilter):
    """No-op filter → returns messages unchanged."""

    def __init__(self):
        # Intentionally avoided to call super() to avoid unnecessary init
        pass

    def apply(self, msgs):
        return msgs


# -----------------------------
# NoOp Storage
# -----------------------------
class NoOpStorage(StorageInterface):
    """No-op storage → disables persistence safely."""

    def __init__(self):
        # Intentionally avoided to call super() to avoid unnecessary init
        # No need to give anything to queue/log
        self.queue = None
        self.log = None

    async def init_db(self, **kwargs) -> None:
        return None

    async def create_table(self, **kwargs) -> None:
        return None

    async def start_writer(self, **kwargs) -> None:
        return None

    async def enqueue_insert(self, msgs: Sequence[MessageInterface], **kwargs) -> None:
        return None

    async def _insert_batch_internally(self, msgs: Sequence[MessageInterface], **kwargs) -> None:
        return None

    def check_message_if_exists(self, msg_id: str, **kwargs) -> bool:
        return False

    async def check_message_if_exists_async(self, msg_id: str, **kwargs) -> bool:
        return False

    def get_all_messages(self, **kwargs) -> List[Dict[str, Any]]:
        return []

    async def close_db(self, **kwargs) -> None:
        return None
