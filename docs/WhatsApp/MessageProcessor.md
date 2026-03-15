# ✉️ MessageProcessor: The Core Information Lifeline

The `MessageProcessor` acts as the grand orchestrator of your WhatsApp message flow. It extracts messages from the Web UI, optionally encrypts them to an unreadable state, filters out spam, and then seamlessly hands them off to your storage database.

Like the `ChatProcessor`, it operates securely as a **Singleton-per-Page Pattern**, preventing duplicate extractions or redundant memory usage.

---

### 🛠️ Setting up the MessageProcessor

The `MessageProcessor` touches all parts of the data cycle.

```python
from camouchat.WhatsApp import MessageProcessor
from camouchat.Encryption import KeyManager # (Optional) Let's say you pulled a key from ProfileManager!

msg_processor = MessageProcessor(
    storage_obj=my_storage,
    # ------------- This is a Required Parameter -------------
    # Your database storage instance (like SQLAlchemyStorage).

    filter_obj=my_filter,
    # ------------- This is a Required Parameter -------------
    # Your MessageFilter instance to prevent spam and rate-limit.

    chat_processor=my_chat_processor,
    # ------------- This is a Required Parameter -------------
    # Passed ChatProcessor for interacting with the raw chat UI elements.

    page=page_obj,
    # ------------- This is a Required Parameter -------------
    # The active Playwright page instance.

    log=camouchatLogger,
    # ------------- This is a Required Parameter -------------

    UIConfig=ui_config_obj,
    # ------------- This is a Required Parameter -------------

    encryption_key=profile_key  
    # ------------- Optional Parameter -------------
    # Pass an AES-256 key from ProfileManager. If provided, all body strings are wiped from RAM/Disk.
)
```

---

# --- Now let's fetch those messages ---

### 📦 Key Functions

#### 1. `Fetcher(chat, retry, *args, **kwargs)`
A robust function that queries raw elements out of a provided chat, extracts information like `data-id` and text content, performs optional AES encryption, enqueues the messages to storage, and finally runs them through your rate-limiting filter.
```python
messages = await msg_processor.Fetcher(
    chat=recent_chats[0], 
    # ------------- Required Parameter -------------
    # The target `whatsapp_chat` element you fetched earlier.
    
    retry=3
    # ------------- Required Parameter -------------
    # Attempt counts if elements aren't immediately found on the screen.
)

if messages:
    print(f"I just extracted {len(messages)} new messages from {recent_chats[0].chat_name}!")
```

#### 2. `sort_messages(msgList, incoming=True)`
Separates a mixed list of messages into exclusively "incoming" or "outgoing" directions.
```python
inbound_messages = await msg_processor.sort_messages(
    msgList=messages, 
    # ------------- Required Parameter -------------
    # The Sequence of `whatsapp_message` objects you got from Fetcher.
    
    incoming=True
    # ------------- Required Parameter -------------
    # True returns only inbound ('in') messages. 
    # False returns only outbound ('out') messages.
)

for msg in inbound_messages:
    print(f"I received: {msg.raw_data}") # Wait, this might be blank if encryption is ON!
```

---

### 🛡️ Real-time Encryption
When the `MessageProcessor` is given an `encryption_key`, it behaves fundamentally differently to protect the user's data:

1.  **AES-256-GCM**: Message bodies are encrypted instantly.
2.  **Plaintext Wiped**: `msg.raw_data` is scrubbed and erased *before* it gets sent to the storage enqueue.
3.  **Chat Names Hashed**: Identifiable names are hashed via `HMAC-SHA256` so they can be looked up in the database efficiently, without saving the real name.
4.  **Key Cleanup**: The raw encryption key is wiped from Python's memory the moment the encryptor finishes initializing.

This makes it the frontline shield of your SDK's privacy features! 🔐
