"""
WhatsApp Exception Hierarchy.

This module defines the structured exception system used by the WhatsApp
automation layer of the project. All errors raised during WhatsApp operations
inherit from `WhatsAppError`, which itself extends the global project error
base `TweakioError`.

Purpose
-------
The hierarchy provides:
- Clear separation of failure domains (chat, message, login, media, reply).
- Consistent error handling across automation layers.
- Easier debugging and targeted exception catching.
- Structured propagation of errors from low-level UI operations to higher
  orchestration layers.

Hierarchy Overview
------------------

TweakioError
└── WhatsAppError
    ├── ChatError
    │   ├── ChatClickError
    │   ├── ChatNotFoundError
    │   ├── ChatListEmptyError
    │   ├── ChatProcessorError
    │   ├── ChatUnreadError
    │   │   └── ChatMenuError
    │
    ├── MessageError
    │   ├── MessageNotFoundError
    │   ├── MessageListEmptyError
    │   └── MessageProcessorError
    │
    ├── LoginError
    │
    ├── ReplyCapableError
    │
    └── MediaCapableError
        └── MenuError

Design Notes
------------
- Base classes represent logical subsystems of WhatsApp functionality.
- Specific exceptions represent concrete UI or automation failures.
- Subclassing allows higher-level code to catch either granular or grouped
  error categories depending on the context.

Example Usage
-------------
try:
    chat.open()
except ChatNotFoundError:
    handle_missing_chat()
except ChatError:
    handle_generic_chat_issue()
except WhatsAppError:
    handle_general_whatsapp_failure()
"""

from src.Exceptions.base import TweakioError


class WhatsAppError(TweakioError):
    """Base Class for all WhatsApp Errors"""

    pass


# ----------------- Chat Errors ----------------------------------------


class ChatError(WhatsAppError):
    """Base Class for all WhatsApp Chat Errors"""

    pass


class ChatClickError(ChatError):
    """Click Chat Error"""

    pass


class ChatNotFoundError(ChatError):
    """Chat Not Found Error"""

    pass


class ChatListEmptyError(ChatError):
    """Chat List Empty Error"""

    pass


class ChatProcessorError(ChatError):
    """Chat Processing Error"""

    pass


class ChatUnreadError(ChatError):
    """Chat Unread Error"""

    pass


class ChatMenuError(ChatUnreadError):
    """Chat Menu Error when opening the chat operation menu on WEB UI for unread/read/archive etc"""

    pass


# ----------------- Message Errors ----------------------------------------


class MessageError(WhatsAppError):
    """Base Class for all WhatsApp Message Errors"""

    pass


class MessageNotFoundError(MessageError):
    """Message Not Found Error"""

    pass


class MessageListEmptyError(MessageError):
    """Message List Empty Error"""

    pass


class MessageProcessorError(MessageError):
    """Message Processor Error"""

    pass


# ----------------- Login Errors ----------------------------------------
class LoginError(WhatsAppError):
    """Base Class for all WhatsApp Login Errors"""

    pass


# ----------------- ReplyCapable Errors ----------------------------------------
class ReplyCapableError(WhatsAppError):
    """Base Class for all WhatsApp Reply Capable Errors"""

    pass


# ----------------- MediaCapable Errors ----------------------------------------
class MediaCapableError(WhatsAppError):
    """Base Class for all WhatsApp Media Capable Errors"""

    pass


class MenuError(MediaCapableError):
    """Menu Error for Media Sending"""

    pass
