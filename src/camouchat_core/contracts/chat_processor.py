"""Contracts for chat discovery and chat activation."""

from __future__ import annotations

from typing import Dict, Sequence, Protocol

from .chat import ChatProtocol


class ChatProcessorProtocol(Protocol):
    """Base contract for components that list chats and activate a chat.

    Implementations own platform-specific state such as selectors, browser
    pages, bridge clients, and logger defaults. The interface only captures the
    behavior expected by callers.
    """

    capabilities: Dict[str, bool]

    async def fetch_chats(self, **kwargs) -> Sequence[ChatProtocol]:
        """Fetch available chats from the UI."""
        ...

    async def _click_chat(self, chat: ChatProtocol | None = None, **kwargs) -> bool:
        """Click to open a chat."""
        ...
