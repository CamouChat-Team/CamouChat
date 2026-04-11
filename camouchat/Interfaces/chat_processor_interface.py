"""Contracts for chat discovery and chat activation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Sequence

from camouchat.contracts.chat_interface import ChatInterface


class ChatProcessorInterface(ABC):
    """Base contract for components that list chats and activate a chat.

    Implementations own platform-specific state such as selectors, browser
    pages, bridge clients, and logger defaults. The interface only captures the
    behavior expected by callers.
    """

    capabilities: Dict[str, bool]

    @abstractmethod
    async def fetch_chats(self) -> Sequence[ChatInterface]:
        """Fetch available chats from the UI."""
        ...

    @abstractmethod
    async def _click_chat(self) -> bool:
        """Click to open a chat."""
        ...
