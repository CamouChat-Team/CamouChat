"""
WhatsApp-specific data types and structures.

Concrete implementations of chat and message objects
tailored for WhatsApp Web's data model and behavior.
"""

from .Chat import whatsapp_chat
from .Message import whatsapp_message

__all__ = ["whatsapp_message", "whatsapp_chat"]
