"""
Abstract interfaces and protocols for camouchat components.

These interfaces define contracts that platform-specific implementations
must follow, enabling clean separation between core logic and platform integrations.

NOTE: To avoid circular dependencies, import interfaces directly from their module files:
    from camouchat.Interfaces.browser_interface import BrowserInterface
    from camouchat.Interfaces.chat_interface import ChatInterface

Do NOT import from this __init__.py file.
"""

# This file intentionally left minimal to avoid circular import issues.
# Import interfaces directly from their respective module files.

# browserforge.py
#   → imports BrowserForgeCapable from Interfaces.browserforge_capable_interface
#     → TRIGGERS Interfaces/__init__.py
#       → imports ChatProcessorInterface
#         → imports WebSelectorConfig from WhatsApp.web_ui_config
#           → TRIGGERS WhatsApp/__init__.py
#             → imports ChatProcessor
#               → imports ChatProcessorInterface (CIRCULAR)
