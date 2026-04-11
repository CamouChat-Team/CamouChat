"""Contracts for message extraction and normalization."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar

from camouchat.contracts.message_interface import MessageInterface
from camouchat.contracts.web_ui_selector import WebUISelectorCapable

T = TypeVar("T", bound=MessageInterface)
U = TypeVar("U", bound=WebUISelectorCapable)


class MessageProcessorInterface(ABC, Generic[T, U]):
    """Base contract for message processors.

    Concrete processors decide how to source messages, which no-op dependencies
    to use, and which logger should be attached. This interface only supplies a
    common attribute shape and the required fetch operation.
    """

    ui_config: Optional[U] = None

    @abstractmethod
    async def fetch_messages(self) -> List[T]:
        """Fetch messages from a chat with storage and filtering."""
        ...
