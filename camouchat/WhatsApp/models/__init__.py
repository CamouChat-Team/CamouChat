"""
WhatsApp-specific data types and structures.

Concrete implementations of chat and message objects
tailored for WhatsApp Web's data model and behavior.

gives :
-Message  ( Old)
-Chat  ( Old )
-MessageModelAPI ( new )
-ChatModelAPI ( new )
"""

from .chat import Chat
from .message import Message
from .message_api import MessageModelAPI
from .chat_api import ChatModelAPI

__all__ = ["Message", "Chat", "MessageModelAPI", "ChatModelAPI"]
