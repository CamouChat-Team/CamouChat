# 📊 RAM Data Models (`*ModelAPI`)

`camouchat.WhatsApp.api.models`

With the introduction of the RAM-based extraction pipeline (`WapiSession` and `@msg_event_hook`), CamouChat now normalizes WhatsApp's complex internal React logic into cleanly typed Python Dataclasses. 

These models replace the legacy `Message` and `Chat` objects which lacked WhatsApp-specific fidelity.

---

## 👤 `ChatModelAPI`

Represents a strictly typed WhatsApp Chat thread.

```python
from camouchat.WhatsApp.api.models import ChatModelAPI
```

### Core Properties
| Property | Type | Description |
|----------|------|-------------|
| `id_serialized` | `str` | The technical chat `jid` (e.g. `123456@c.us`). |
| `name` | `str` | The display name or phone number. |
| `unreadCount` | `int` | Number of unread messages currently in the thread. |
| `isReadOnly` | `bool` | True if the group settings prevent the profile from sending messages. |
| `isGroup` | `bool` | True if this chat is a WhatsApp Group. |
| `muteExpiration` | `int` | UNIX timestamp for when the mute expires (0 if not muted). |
| `ephemeralDuration` | `int` | Current disappearing messages duration in seconds. |

### Extended Metadata
| Property | Type | Description |
|----------|------|-------------|
| `optional_attr_list` | `Dict` | A catch-all dictionary containing all raw RAM attributes (labels, pinned status, etc.) not currently explicitly mapped by the Python dataclass. |

---

## ✉️ `MessageModelAPI`

Represents a precisely typed WhatsApp Message payload. 

```python
from camouchat.WhatsApp.api.models import MessageModelAPI
```

### Core Properties
| Property | Type | Description |
|----------|------|-------------|
| `id_serialized` | `str` | The globally unique internal Message ID (e.g., `false_123@c.us_3EB0...`). |
| `jid_From` | `str` | The `jid` of the actual sender. |
| `body` | `str` | The plaintext string of the message. |
| `MsgType` | `str` | The payload type (`chat`, `image`, `video`, `audio`, `document`, `poll_creation`). |
| `timestamp` | `int` | UNIX timestamp of when the message was sent. |
| `isGroupMsg` | `bool` | True if this message arrived inside a group. |

### Specialized Metadata
| Property | Type | Description |
|----------|------|-------------|
| `mentionedJidList` | `List[str]` | A list of strings containing the JIDs of users tagged/mentioned by the sender in the message block. |
| `optionalAttrList` | `Dict` | Extra React payload data (mediaKeys, directPaths, forward scores). |

> [!TIP]
> **Media Decryption**: When `MsgType` is an image or video, check `msg.optionalAttrList` to access `mediaKey` and `directPath`. These variables are critical for downloading encrypted media files from the WhatsApp CDN without triggering the UI.
