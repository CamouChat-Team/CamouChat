"""Contracts for message extraction and normalization."""

from __future__ import annotations

from typing import Generic, List, Optional, TypeVar, Protocol

from camouchat.contracts.message import MessageProtocol
from camouchat.contracts.chat import ChatProtocol
from camouchat.contracts.web_ui_selector import WebUISelectorCapable

T = TypeVar("T", bound=MessageProtocol)
U = TypeVar("U", bound=WebUISelectorCapable)


class MessageProcessorProtocol(Protocol, Generic[T, U]):
    """Base contract for message processors.

    Concrete processors decide how to source messages, which no-op dependencies
    to use, and which logger should be attached. This interface only supplies a
    common attribute shape and the required fetch operation.
    """

    ui_config: Optional[U] = None

    async def fetch_messages(
        self, chat: ChatProtocol, retry: int = 5, **kwargs
    ) -> List[T]:
        """Fetch messages from a chat with storage and filtering."""
        ...
