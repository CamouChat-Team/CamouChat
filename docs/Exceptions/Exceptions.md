# ⚠️ Exceptions

`camouchat.Exceptions`

CamouChat uses a structured, hierarchical exception system. Every error raised by the SDK is a subclass of `CamouChatError`, giving you the ability to catch errors at any level of granularity — from a specific leaf error like `ChatClickError` to the global `CamouChatError`.

---

## 🌳 Full Exception Hierarchy

```text
CamouChatError  (base.py)
│
├── BrowserException           # Browser launch, fingerprint, or Camoufox failures
├── ElementNotFoundError       # DOM element not found during interaction
├── HumanizedOperationError    # Humanized typing/typing-fallback failure
├── MessageFilterError         # MessageFilter.apply() received mixed-chat messages
├── StorageError               # DB init, schema creation, or insert failure
│
└── WhatsAppError  (whatsapp.py)           # Base for all WhatsApp platform errors
    │
    ├── ChatError                          # Base for chat-level failures
    │   ├── ChatClickError                 # _click_chat() failed after retries
    │   ├── ChatNotFoundError              # Sidebar has no chats / None passed
    │   ├── ChatListEmptyError             # Chat list is empty
    │   ├── ChatProcessorError             # General ChatProcessor extraction failure
    │   └── ChatUnreadError                # is_unread() / do_unread() failure
    │       └── ChatMenuError              # Context menu not found in do_unread()
    │
    ├── MessageError                       # Base for message-level failures
    │   ├── MessageNotFoundError           # No messages found in the DOM
    │   ├── MessageListEmptyError          # Empty list passed to sort_messages()
    │   └── MessageProcessorError          # General MessageProcessor extraction failure
    │
    ├── LoginError                         # Any WhatsApp login flow failure
    │
    ├── InteractionControllerError                  # Any reply interaction failure
    │
    └── MediaCapableError                  # Any media upload failure
        └── MenuError                      # Attachment menu not found or timed out
```

---

## 📂 Module Locations

| Module | File | Contains |
|--------|------|----------|
| `camouchat.Exceptions.base` | `Exceptions/base.py` | `CamouChatError`, `BrowserException`, `ElementNotFoundError`, `HumanizedOperationError`, `MessageFilterError`, `StorageError` |
| `camouchat.Exceptions.whatsapp` | `Exceptions/whatsapp.py` | Entire `WhatsAppError` subtree |
| `camouchat.Exceptions` | `Exceptions/__init__.py` | Re-exports all exceptions for convenience |

---

## 🎯 Catching Exceptions: From Specific to Broad

```python
from camouchat.Exceptions.whatsapp import (
    ChatClickError,
    ChatNotFoundError,
    ChatError,
    WhatsAppError,
)
from camouchat.Exceptions.base import CamouChatError

try:
    chats = await chat_proc.fetch_chats(limit=5)
    await reply_handler.reply(message=msg, humanize=humanizer, text="Hello!")

except ChatClickError as e:
    # Very specific — CDP click failed after 20 retries
    print(f"Could not click chat: {e}")

except ChatError as e:
    # Any chat-level error (click, not-found, unread, etc.)
    print(f"Chat operation failed: {e}")

except WhatsAppError as e:
    # Any WhatsApp-specific error across all modules
    print(f"WhatsApp error: {e}")

except CamouChatError as e:
    # Catch-all for any SDK-level error
    print(f"CamouChat SDK error: {e}")
```

---

## 📋 Exception Reference

### Base Exceptions (`Exceptions/base.py`)

| Exception | Raised By | When |
|-----------|-----------|------|
| `CamouChatError` | (base) | Never raised directly — catch-all base. |
| `BrowserException` | `CamoufoxBrowser`, `BrowserForgeCompatible` | Browser launch failure, invalid fingerprint path, screen detection failure. |
| `ElementNotFoundError` | `HumanInteractionController` | `typing()` called with no `source` element. |
| `HumanizedOperationError` | `HumanInteractionController` | Both `typing()` and `_Instant_fill()` failed. |
| `MessageFilterError` | `MessageFilter.apply()` | Messages from multiple chats mixed in a single `apply()` call. |
| `StorageError` | `SQLAlchemyStorage` | DB engine init failed, table creation failed, or batch insert error. |

### WhatsApp Exceptions (`Exceptions/whatsapp.py`)

| Exception | Raised By | When |
|-----------|-----------|------|
| `WhatsAppError` | (base) | Never raised directly. |
| `ChatError` | (base) | Never raised directly. |
| `ChatClickError` | `ChatProcessor._click_chat()` | CDP mouse click failed after 20 retries. |
| `ChatNotFoundError` | `ChatProcessor.fetch_chats()`, `_click_chat()` | No chat rows in DOM, or `None` passed. |
| `ChatListEmptyError` | `ChatProcessor` | Chat list structure not found. |
| `ChatProcessorError` | `ChatProcessor._get_Wrapped_Chat()` | Extraction failed after all retries. |
| `ChatUnreadError` | `ChatProcessor.is_unread()`, `do_unread()` | DOM interaction failure on unread badge. |
| `ChatMenuError` | `ChatProcessor.do_unread()` | Context menu (`role=application`) not found. |
| `MessageError` | (base) | Never raised directly. |
| `MessageNotFoundError` | `MessageProcessor._get_wrapped_Messages()` | Zero message elements in the DOM. |
| `MessageListEmptyError` | `MessageProcessor.sort_messages()` | Empty list passed. |
| `MessageProcessorError` | `MessageProcessor._get_wrapped_Messages()` | Extraction failed after all retries. |
| `LoginError` | `Login.login()`, `Login.is_login_successful()` | Any login flow failure (timeout, bad method, missing country, etc.). |
| `InteractionControllerError` | `InteractionController.reply()`, `_side_edge_click()` | Missing `data_id`, DOM not found after 20 retries, or reply timeout. |
| `MediaCapableError` | `MediaCapable.add_media()`, `menu_clicker()` | Invalid file path, menu/attachment timeout. |
| `MenuError` | `MediaCapable.menu_clicker()` | The `+` attachment icon locator returned `None`. |

---

## 💡 Design Philosophy

- **Hierarchy by subsystem**: Errors are organized by which module raises them (Chat, Message, Login, Media, Reply), not by error severity. This lets you catch exactly the subset of errors you care about.
- **Specific over generic**: Always catch the most specific exception first, then broaden. Catching `CamouChatError` everywhere will mask bugs — catch `ChatNotFoundError` when you know you're operating on chat lists.
- **No silent swallowing**: The SDK never catches `CamouChatError` internally (except in top-level retry loops). All errors propagate fully to your calling code.
