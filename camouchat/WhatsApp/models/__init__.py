"""
WhatsApp-specific data types and structures.

Concrete implementations of chat and message objects
tailored for WhatsApp Web's data model and behavior.
"""

from .chat import Chat
from .message import Message

__all__ = ["Message", "Chat"]
