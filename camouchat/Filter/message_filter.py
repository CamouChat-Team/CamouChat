"""Independent class for Message Filtering"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from queue import Queue
from typing import List, Optional, TypeVar, Sequence

from camouchat.contracts.chat_interface import ChatInterface
from camouchat.contracts.message_interface import MessageInterface

from camouchat.Exceptions.base import MessageFilterError

T = TypeVar("T", bound=MessageInterface)


@dataclass
class State:
    """Chat State"""

    defer_since: Optional[float]
    last_seen: Optional[float]
    window_start: float = field(default_factory=time.time)
    count: int = 0

    def reset(self) -> None:
        """Reset the state"""
        self.window_start = time.time()
        self.count = 0
        self.defer_since = None
        self.last_seen = None


@dataclass
class BindData:
    """Bind Data for the Queue Filtering"""

    chat: ChatInterface
    Messages: Sequence[MessageInterface]
    seen: float


class MessageFilter:
    """
    Independent, shared Message Filter.

    function : apply
        - using temporary Queue , Map , Persists the chat with its messages.
        - Internally help setting the rate limiting
    """

    StateMap: dict[str, State] = {}
    """State Map keep the state of the multiple chats."""
    Defer_queue: Queue[BindData] = Queue()
    """Decided which one to deliver  -- defer -- drop."""

    def __init__(
        self,
        LimitTime: int = 3600,
        Max_Messages_Per_Window: int = 10,
        Window_Seconds: int = 60,
    ):
        self.LimitTime = LimitTime
        self.Max_Messages_Per_Window = Max_Messages_Per_Window
        self.Window_Seconds = Window_Seconds

    def apply(
        self,
        msgs: List[T],
    ) -> List[T]:
        """
        Applies the filter on any set of Messages.
        Filter is agnostic to message direction or type.

        uses 3 states :
            - Deliver
                If Everything passes ( spam check , LimitTime check) deliver messages.
            - Delay
                If spam detected delay the messages for next time.
            - Drop
                If delayed > LimitTime then drops the messages.

        Raises :
        - MessageFilterError if not all messages belong to 1 single-same chat
        """

        if not msgs:
            return []

        m0: MessageInterface = msgs[0]
        # Check Single-same chat or not in List[messages]
        for m in msgs:
            mi: MessageInterface = m
            if mi.from_chat != m0.from_chat:
                raise MessageFilterError("MessageFilter.apply expects messages from a single chat")

        chat = m0.from_chat
        chat_key = chat.id_serialized if not isinstance(chat, str) else chat
        assert chat_key is not None
        now = time.time()

        # Fetch/initialize per-chat state
        state = self.StateMap.setdefault(chat_key, State(None, None))

        # Reset rate window if expired
        if now - state.window_start >= self.Window_Seconds:
            state.window_start = now
            state.count = 0

        batch_size = len(msgs)

        # Hard drop: chat delayed > self.LimitTime
        defer_since = state.defer_since
        if defer_since is not None and (now - defer_since) > self.LimitTime:
            state.reset()
            return msgs

        # Rate-limit hit → delay entire batch
        if state.count + batch_size > self.Max_Messages_Per_Window:
            state.defer_since = state.defer_since or now
            self.Defer_queue.put(BindData(chat if not isinstance(chat, str) else None, msgs, now))  # type: ignore
            return []

        # Deliver
        state.count += batch_size
        state.last_seen = now
        return msgs
