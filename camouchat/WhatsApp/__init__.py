"""
WhatsApp platform integration for CamouChat.

Provides chat processing, message handling, media operations,
and human-like interaction capabilities for WhatsApp Web automation.
"""
from camouchat.WhatsApp.api.managers.chat_api_processor import ChatApiManager
from camouchat.WhatsApp.api.managers.msg_api_processor import MessageApiManager
from camouchat.WhatsApp.core.login import Login
from camouchat.WhatsApp.features.media_capable import MediaCapable
from camouchat.WhatsApp.features.interaction_controller import InteractionController
from camouchat.WhatsApp.core.web_ui_config import WebSelectorConfig

__all__ = [
    "ChatApiManager",
    "MessageApiManager",
    "Login",
    "MediaCapable",
    "InteractionController",
    "WebSelectorConfig",
]
