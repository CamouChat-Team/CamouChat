# ✉️ MessageProcessor (Legacy)

> [!WARNING]
> **Legacy Architecture:** `MessageProcessor` relies on slow, fragile DOM scraping. For high-performance, real-time message extraction, please migrate to the new RAM-based Event Bridge. See the [Event Hooks Documentation](EventHooks.md) instead!

`camouchat.WhatsApp.message_processor`

`MessageProcessor` is the central orchestrator of the legacy message extraction pipeline. It fetches raw message elements from the WhatsApp Web DOM, optionally encrypts them with AES-256-GCM, deduplicates against the database, enqueues them for async storage, and passes them through the rate-limiting filter.

Like all WhatsApp components, it is a **Singleton-per-Page** instance.

---

## 🛠️ Constructor

```python
MessageProcessor(
    chat_processor: ChatProcessor,
    page: Page,
    ui_config: WebSelectorConfig,
    storage_obj: Optional[StorageInterface] = None,
    filter_obj: Optional[MessageFilter] = None,
    encryption_key: Optional[bytes] = None,
    log: Optional[Union[Logger, LoggerAdapter]] = None,
)
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `chat_processor` | `ChatProcessor` | ✅ Yes | Used internally to open a chat via `_click_chat()` before scraping messages. The `@ensure_chat_clicked` decorator calls this automatically. |
| `page` | `Page` | ✅ Yes | The active Playwright async page for all DOM and keyboard interactions. |
| `ui_config` | `WebSelectorConfig` | ✅ Yes | Provides all DOM selectors for message bubbles, `data-id` attributes, and text content. |
| `storage_obj` | `StorageInterface` | ❌ No | Database storage backend. Defaults to `NoOpStorage` (no persistence) if not provided. |
| `filter_obj` | `MessageFilter` | ❌ No | Rate-limiting filter. Defaults to `NoOpMessageFilter` (pass-all) if not provided. |
| `encryption_key` | `bytes` | ❌ No | Raw 32-byte AES-256 key from `ProfileManager.enable_encryption()` or `get_key()`. When provided, encrypts all message bodies and chat names **before** storage. The key is wiped from memory immediately after the encryptor is initialized. |
| `log` | `Logger \| LoggerAdapter` | ❌ No | Logger for extraction, encryption, and storage events. |

```python
import asyncio
from camouchat.WhatsApp import MessageProcessor, WebSelectorConfig
from camouchat.StorageDB import SQLAlchemyStorage
from camouchat.Filter import MessageFilter
from camouchat.camouchat_logger import camouchatLogger

queue = asyncio.Queue()
storage = SQLAlchemyStorage.from_profile(profile=profile, queue=queue, log=camouchatLogger)
msg_filter = MessageFilter(LimitTime=3600, Max_Messages_Per_Window=10, Window_Seconds=60)

# Optional: load encryption key
key = pm.get_key(Platform.WHATSAPP, "SecureBot")

msg_proc = MessageProcessor(
    chat_processor=chat_proc,
    page=page,
    ui_config=WebSelectorConfig(page=page, log=camouchatLogger),
    storage_obj=storage,
    filter_obj=msg_filter,
    encryption_key=key,     # Omit this line to disable encryption
    log=camouchatLogger,
)
```

---

## 📦 Methods

### `fetch_messages(chat, retry=5, **kwargs) → List[Message]`

The primary entrypoint. Performs the full pipeline: click chat → scrape DOM → deduplicate → encrypt (if key set) → store → filter. Returns the final list of allowed messages.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `chat` | `Chat` | ✅ Yes | The target `Chat` object from `ChatProcessor.fetch_chats()`. |
| `retry` | `int` | `5` | DOM scrape retry attempts if messages aren't immediately found. |
| `only_new` | `bool` (kwarg) | `False` | If `True`, returns only messages that were **not** already in the database (newly seen messages only). Useful for event-driven bot logic. |

```python
messages = await msg_proc.fetch_messages(chat=chats[0], retry=3)

for msg in messages:
    print(f"[{msg.direction}] {msg.raw_data}")
```

#### Pipeline Breakdown

```
       fetch_messages(chat)
              │
              ▼
   @ensure_chat_clicked          ← Calls chat_proc._click_chat() with 3 retries
              │
              ▼
   _get_wrapped_Messages()       ← Scrapes message DOM, wraps into List[Message]
              │
              ▼
   Deduplication                 ← Filters messages already in storage (check_message_if_exists_async)
              │
              ▼
   Encryption (if key set)       ← AES-256-GCM encrypt body & chat name; wipe plaintext
              │
              ▼
   storage.enqueue_insert()      ← Non-blocking async queue put (NoOp-safe)
              │
              ▼
   filter.apply()                ← Rate-limit + defer/drop (NoOp-safe)
              │
              ▼
   Returns msgList  (or only new if only_new=True)
```

---

### `sort_messages(msgList, incoming) → List[Message]` *(static)*

Separates a mixed-direction message list into incoming or outgoing messages.

| Parameter | Type | Description |
|-----------|------|-------------|
| `msgList` | `Sequence[Message]` | The list from `fetch_messages()`. |
| `incoming` | `bool` | `True` → only `direction == "in"` messages. `False` → only `direction == "out"`. |

```python
inbound = await MessageProcessor.sort_messages(msgList=messages, incoming=True)
outbound = await MessageProcessor.sort_messages(msgList=messages, incoming=False)

for msg in inbound:
    print(f"Received: {msg.raw_data}")
```

> [!NOTE]
> Raises `MessageListEmptyError` if `msgList` is empty.

---

## 📄 The `Message` Model

`Message` objects are returned by `fetch_messages()`. Key attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `message_id` | `str` | Unique ID derived from WhatsApp's `data-id` attribute. Used for deduplication. |
| `data_id` | `str` | Raw `data-id` DOM attribute value. |
| `raw_data` | `str` | Plaintext message body. **Blank string if encryption is enabled** (wiped before storage). |
| `direction` | `str` | `"in"` for received messages, `"out"` for sent. |
| `parent_chat` | `Chat` | The `Chat` object this message belongs to. |
| `encrypted_message` | `str \| None` | Base64-encoded AES-256-GCM ciphertext (set when encryption is active). |
| `encryption_nonce` | `str \| None` | Base64-encoded 12-byte nonce for decryption. |
| `encrypted_chat_name` | `str \| None` | Base64-encoded encrypted chat name. |
| `chat_name_nonce` | `str \| None` | Base64-encoded nonce for chat name decryption. |
| `parent_chat_name_index` | `str \| None` | HMAC-SHA256 hex digest of the chat name — used as the DB index column when encryption is enabled. |

---

## 🔐 Encryption Deep Dive

When `encryption_key` is provided at construction time:

1. **Key initialization**: `MessageEncryptor(key)` is instantiated; an HMAC key is derived via `SHA-256(key + b"chat-name-index")[:16]` for chat name indexing.
2. **Key wipe**: `del encryption_key` is called in a `finally` block — the raw key is **removed from Python's namespace** immediately after initialization.
3. **Per-message body**: Each message's `raw_data` is encrypted with a fresh random 12-byte nonce via AES-256-GCM. `msg.encrypted_message` and `msg.encryption_nonce` are populated; `msg.raw_data` is set to `""`.
4. **Chat name**: The chat name is similarly encrypted once per `fetch_messages()` call (not per message). `msg.encrypted_chat_name` + `msg.chat_name_nonce` store the ciphertext; `msg.parent_chat_name_index` stores the HMAC digest for queryable lookups.
5. **Storage**: The database receives ciphertext only — plaintext and ciphertext **never coexist in the same row**.

```python
# After storage, retrieve and decrypt all messages
key = pm.get_key(Platform.WHATSAPP, "SecureBot")
async with storage as s:
    rows = await s.get_decrypted_messages_async(key=key, limit=500)
    for row in rows:
        print(f"[{row['direction']}] {row['raw_data']}")
```

---

## 🛡️ NoOp Safety

`storage_obj` and `filter_obj` are optional. When omitted, `MessageProcessor` uses:
- `NoOpStorage` → `check_message_if_exists_async()` always returns `False` (no dedup), `enqueue_insert()` silently discards messages.
- `NoOpMessageFilter` → `apply()` returns the input list unchanged.

This means you can use `MessageProcessor` purely for DOM scraping without any storage or filtering infrastructure:

```python
msg_proc = MessageProcessor(
    chat_processor=chat_proc,
    page=page,
    ui_config=ui_config,
    # No storage_obj, no filter_obj — pure in-memory extraction
)
messages = await msg_proc.fetch_messages(chat=chats[0])
```

---

## 💡 Pro Tips

- **`only_new=True`** is the most efficient mode for event-driven bots: it returns only messages that haven't been persisted yet, so you process each message exactly once.
- **Encryption key lifecycle**: Call `pm.enable_encryption()` once per profile setup. On subsequent bot runs, call `pm.get_key()` to reload the saved key. Never hardcode the key.
- **`@ensure_chat_clicked`**: The decorator tries to open the chat up to 3 times before aborting. If your bot runs against very slow connections, increase `retry` in `fetch_messages()` rather than modifying the decorator — the decorator is purely for ensuring the chat is visually open.
