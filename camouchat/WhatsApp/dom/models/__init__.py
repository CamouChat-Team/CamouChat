"""
WhatsApp-specific data types and structures.

Concrete implementations of chat and message objects
tailored for WhatsApp Web's data model and behavior.

gives :
-Message
-Chat
"""

from .chat import Chat
from .message import Message

__all__ = ["Message", "Chat"]
