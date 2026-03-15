# 💬 ChatProcessor: Your Chat Coordinator

The `ChatProcessor` is responsible for fetching, interacting with, and managing WhatsApp chats from the Web UI sidebar.

It is implemented using a **Singleton-per-Page Pattern**, meaning no matter how many times you try to instantiate it for the same `Page`, you get the exact same instance back. This prevents redundant operations and saves memory!

---

### 🛠️ Setting up the ChatProcessor

To initialize the `ChatProcessor`, you need to provide your Playwright `page`, a `logger`, and the `WebSelectorConfig`.

```python
from camouchat.WhatsApp import ChatProcessor

c_processor = ChatProcessor(
    page=page_obj,
    # ------------- This is a Required Parameter -------------
    # The active browser page instance.

    log=camouchatLogger,
    # ------------- This is a Required Parameter -------------
    # This logs details & Metrics.

    UIConfig=ui_config_obj
    # ------------- This is a Required Parameter -------------
    # Instance of WebSelectorConfig to map the UI elements.
)
```

# --- Let's see what we can do with this ChatProcessor ---

### 📦 Key Functions

#### 1. `fetch_chats(limit=5, retry=5)`
Extracts chat elements from the sidebar and returns them as `whatsapp_chat` objects.
```python
recent_chats = await c_processor.fetch_chats(
    limit=10, 
    # ------------- Optional Parameter -------------
    # How many chats you want to fetch. Defaults to 5.
    
    retry=5
    # ------------- Optional Parameter -------------
    # Retries if the DOM hasn't rendered them yet.
)

for chat in recent_chats:
    print(f"I found a chat: {chat.chat_name}")
```

#### 2. `is_unread(chat)`
Checks if a given chat has an unread message badge (the green circle with a number).
```python
unread_status = await c_processor.is_unread(recent_chats[0])
# Returns 1 if unread, 0 if it's already read.

if unread_status == 1:
    print("Ooo, you have unread messages in this chat!")
```

#### 3. `do_unread(chat)`
Marks a given chat as unread by right-clicking it and selecting the "Mark as unread" option from the context menu.
```python
# To keep a chat marked as unread after you've processed it:
success = await c_processor.do_unread(recent_chats[0])
# Returns True if it successfully marked it.
```

---

### 🛡️ Why the Singleton Pattern?
If your automation code loops or you accidentally create the `ChatProcessor` multiple times, you could overload the UI or cause memory leaks. By tying the instance strictly to the active `Page` (via `weakref`), the SDK automatically protects you. Once the page is closed, the Processor cleans itself up automatically! 🧹
