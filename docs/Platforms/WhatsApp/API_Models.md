# 📊 RAM Data Models (`*ModelAPI`)

`camouchat.WhatsApp.api.models`

With the introduction of the RAM-based extraction pipeline (`WapiSession` and `@msg_event_hook`), CamouChat now normalizes WhatsApp's complex internal React logic into cleanly typed Python Dataclasses. 

These models replace the legacy DOM scrapers which lacked WhatsApp-specific fidelity.

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
| `formattedTitle` | `str` | The exact display name or group title shown in the UI. |
| `timestamp` | `int` | The last interaction timestamp (t) of the chat. |
| `unreadCount` | `int` | Number of unread messages currently in this chat. |

### Permissions & State
| Property | Type | Description |
|----------|------|-------------|
| `isReadOnly` | `bool` | True if the group settings prevent the profile from sending messages. |
| `canSend` | `bool` | True if you are technically able to type in this chat. |
| `isArchived` | `bool` | True if the chat is currently in the archived list. |
| `isAutoMuted` | `bool` | True if the chat was auto-muted by WhatsApp due to size or settings. |
| `muteExpiration` | `int` | Unix timestamp when the chat will be unmuted. |
| `isLocked` | `bool` | True if the chat is locked with a passcode/biometrics. |
| `isTrusted` | `bool` | True if the sender is an existing contact or trusted entity. |
| `isNotSpam` | `bool` | True if the chat is marked as known and not spam. |

### Group Metadata
| Property | Type | Description |
|----------|------|-------------|
| `groupType` | `str` | Type of group (e.g., 'DEFAULT', 'ANNOUNCEMENT', 'PARENT'). |
| `isCommunity` | `bool` | True if this is a WhatsApp Community or Announcement parent. |
| `isAnnounceGrpRestrict`| `bool`| True if this is an announcements-only group restricting messages. |
| `groupSafetyChecked` | `bool` | True if WhatsApp ran a scam/safety filter on the group. |

### Mentions & Ephemeral
| Property | Type | Description |
|----------|------|-------------|
| `unreadMentionCount` | `int` | Number of times you were explicitly @mentioned and haven't read it yet. |
| `unreadMentionsOfMe` | `list` | Array of message IDs where you are explicitly mentioned but unread. |
| `ephemeralDuration` | `int` | The time (in seconds) the disappearing messages are set to. |
| `ephemeralSettingTimestamp`|`int`| Unix timestamp for when ephemeral setting was toggled. |
| `disappearingModeTrigger` | `str` | What triggered it (e.g., 'chat_settings'). |
| `disappearingModeInitiator`| `str` | Who triggered it. |

### Miscellaneous
| Property | Type | Description |
|----------|------|-------------|
| `lastChatEntryTimestamp` | `int` | Timestamp of the last time someone typed/sent to this chat. |
| `labels` | `list` | Business labels applied to the chat. |
| `proxyName` | `str` | Internal Meta proxy type identifier (`chat`, `contact`, or `msg`). |

### 🛠️ Experimental Debug Data
| Property | Type | Description |
|----------|------|-------------|
| `optional_attr_list` | `Dict` | **EXPERIMENTAL:** A catch-all dictionary containing all raw RAM attributes not mapped by the dataclass. Changes to these keys happen without warning via WhatsApp AB tests. |

---

## ✉️ `MessageModelAPI`

Represents a precisely typed WhatsApp Message payload. 

```python
from camouchat.WhatsApp.api.models import MessageModelAPI
```

### Core Properties
| Property | Type | Description |
|----------|------|-------------|
| `id_serialized` | `str` | The globally unique internal Message ID (e.g., `false_123@c.us_3EB...`). |
| `rowId` | `int` | IndexedDB row ID (useful for pagination). |
| `fromMe` | `bool` | True if the message was sent by the authenticated user. |
| `jid_From` | `str` | The `jid` of the actual sender (or Group JID). |
| `jid_To` | `str` | The `jid` of the recipient. |
| `author` | `str` | JID of the specific person who sent it (only present in group chats). |
| `pushname` | `str` | The notification name of the sender. |
| `MsgType` | `str` | The payload type (`chat`, `image`, `video`, `audio`, `document`, etc.). |
| `body` | `str` | Plaintext string of the message, or base64 thumbnail for media. |
| `caption` | `str` | Text caption attached to media. |
| `timestamp` | `int` | UNIX timestamp of when the message was sent. |
| `ack` | `int` | 0=Pending, 1=Sent, 2=Delivered, 3=Read, 4=Played. |

### Arrival & Presence Flags
| Property | Type | Description |
|----------|------|-------------|
| `isNew` | `bool` | True if the message is unread LOCALLY in the browser UI. |
| `isNewMsg` | `bool` | True if the message arrived on the wire in this live session. |
| `recvFresh` | `bool` | True if arrived real-time, False if populated from history-sync. |
| `isMdHistoryMsg` | `bool` | True if this is a message synced from multi-device history. |

### Social Flags
| Property | Type | Description |
|----------|------|-------------|
| `isStarMsg` | `bool` | True if the message is starred/favorited. |
| `isForwarded` | `bool` | True if the message has the "Forwarded" tag. |
| `forwardsCount` | `int` | Number of times this message was forwarded. |
| `hasReaction` | `bool` | True if someone reacted to this message. |

### Quoted / Reply Fields
| Property | Type | Description |
|----------|------|-------------|
| `fromQuotedMsg` | `bool` | True if this message is a reply to another message. |
| `quotedMsgId` | `str` | The serialized ID of the message being replied to. |
| `quotedMsgType` | `str` | Type of the quoted message (e.g. `image`, `chat`). |
| `quotedMsgBody` | `str` | First 120 chars of quoted message body/caption. |
| `quotedParticipant`| `str` | JID of the person who sent the original quoted message. |

### Media Fields
| Property | Type | Description |
|----------|------|-------------|
| `mimetype` | `str` | e.g., `image/jpeg`, `audio/ogg; codecs=opus`. |
| `directPath` | `str` | Decryption URL path for the Meta CDN. |
| `mediaKey` | `str` | Base64 AES encryption key for downloading and decrypting media. |
| `size` | `int` | Size of the media in bytes. |
| `isViewOnce` | `bool` | True if sent as "View Once" media. |

### Sender Identity Fields
| Property | Type | Description |
|----------|------|-------------|
| `mentionedJidList` | `List[str]` | List of JIDs explicitly tagged (`@`) in the message body. |
| `senderObj` | `Dict` | High-fidelity dictionary containing deep business profiling, verification levels, and Meta-assigned behavioral flags for the sender. |
| `senderWithDevice` | `str` | Encoded JID representing the specific Multi-Device endpoint that compiled the message (e.g. `12345:97@lid`). |

### Special Message Types
*There are heavily expanded properties for Polls, vCards, Events, and AI Chatbots. Query the dataclasses directly to see fields like `pollName`, `isQuestion`, `eventJoinLink` and `activeBotMsgStreamingInProgress` if your system processes those unique `MsgType` values.*

### 🛠️ Experimental Debug Data
| Property | Type | Description |
|----------|------|-------------|
| `optionalAttrList` | `Dict` | **EXPERIMENTAL:** Catch-all dictionary for React payload data not directly structured into the Python dataclass. Should only be accessed during debugging sessions. |
