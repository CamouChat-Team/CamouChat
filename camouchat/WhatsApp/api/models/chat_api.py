"""
Works on new Wa-js Based api scripts.

Wraps the CHAT api's data into a dataclass
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ChatModelAPI:
    """
    Normalized Data Model for a WhatsApp Chat.

    Attributes:
        id_serialized (str): The unique serialized JID (WhatsApp ID) of the chat.
        unreadCount (int | None): Number of unread messages currently in this chat.
        isAutoMuted (bool | None): True if the chat was auto-muted by WhatsApp due to size or settings.
        timestamp (int | None): The last interaction timestamp (t) of the chat.
        isArchived (bool | None): True if the chat is currently in the archived list.
        isLocked (bool | None): True if the chat is locked with a passcode/biometrics.
        isNotSpam (bool | None): True if the chat is marked as known and not spam.
        disappearingModeTrigger (str | None): How the disappearing mode was triggered (e.g., 'chat_settings').
        disappearingModeInitiator (str | None): Who initiated the disappearing mode (e.g., 'chat').
        unreadMentionCount (int | None): Number of times you were explicitly @mentioned and haven't read it yet.
        lastChatEntryTimestamp (int | None): Timestamp of the last time someone typed/sent something to this chat.
        isOpened (bool | None): True if you have physically opened this chat in the UI session.
        isReadOnly (bool | None): True if you are not allowed to send messages (e.g., Announcements group).
        isTrusted (bool | None): True if the sender is an existing contact or trusted entity.
        formattedTitle (str | None): The display name or group title shown in the UI.
        groupSafetyChecked (bool | None): Internal flag: True if WhatsApp ran a scam/safety filter on the group.
        canSend (bool | None): True if you are technically able to type in this chat.
        proxyName (str | None): Internal Meta proxy type identifier (chat, contact, or msg).
        isCommunity (bool | None): Derived property: True if this is a WhatsApp Community or Announcement parent.


    If the specified field is None , its Mostly means the webpack was not successfully patched the whatsapp.
    Or the webpack ids are changed due to silent update from whatsapp.
    """

    id_serialized: str | None
    unreadCount: int | None
    isAutoMuted: bool | None
    timestamp: int | None
    isArchived: bool | None
    isLocked: bool | None
    isNotSpam: bool | None
    disappearingModeTrigger: str | None
    disappearingModeInitiator: str | None
    unreadMentionCount: int | None
    lastChatEntryTimestamp: int | None
    isOpened: bool | None
    isReadOnly: bool | None
    isTrusted: bool | None
    formattedTitle: str | None
    groupSafetyChecked: bool | None
    canSend: bool | None
    proxyName: str | None
    isCommunity: bool | None

    @classmethod
    def from_dict(cls, data: dict) -> "ChatModelAPI":
        """
        Returns cls object from the dict entered.
        :param data:
        :return: ChatModelAPI
        """

        def get_val(key: str, default: Any = None):
            return data.get(key, data.get(f"__x_{key}", default))

        def safe(v):
            return v if v is not None else None

        id_data = data.get("id") or {}

        is_parent = get_val("isParentGroup", False)
        group_type = get_val("groupType", "DEFAULT")
        is_comm = (is_parent is True) or (group_type == "ANNOUNCEMENT")

        t_val = get_val("t")
        timestamp = t_val if t_val is not None else get_val("timestamp")

        return cls(
            id_serialized=get_val("id_serialized") or id_data.get("_serialized"),
            unreadCount=safe(get_val("unreadCount")),
            isAutoMuted=safe(get_val("isAutoMuted")),
            timestamp=safe(timestamp),
            isArchived=safe(get_val("archive")),
            isLocked=safe(get_val("isLocked")),
            isNotSpam=safe(get_val("notSpam")),
            disappearingModeTrigger=safe(get_val("disappearingModeTrigger")),
            disappearingModeInitiator=safe(get_val("disappearingModeInitiator")),
            unreadMentionCount=safe(get_val("unreadMentionCount")),
            lastChatEntryTimestamp=safe(get_val("lastChatEntryTimestamp")),
            isOpened=safe(get_val("hasOpened")),
            isReadOnly=safe(get_val("isReadOnly")),
            isTrusted=safe(get_val("trusted")),
            formattedTitle=get_val("formattedTitle") or get_val("name"),
            groupSafetyChecked=safe(get_val("groupSafetyChecked")),
            canSend=safe(get_val("canSend")),
            proxyName=safe(get_val("proxyName")),
            isCommunity=is_comm,
        )

    def __str__(self):
        lines = [
            "─── ChatModelAPI ──────────────────────────────────",
            f"  id          : {self.id_serialized}",
            f"  title       : {self.formattedTitle or '(empty name)'}",
            f"  type        : {'Community' if self.isCommunity else 'Chat'}",
            f"  timestamp   : {self.timestamp}",
            f"  unread      : {self.unreadCount or 0}  (@mentions: {self.unreadMentionCount or 0})",
            f"  status      : {'Archived' if self.isArchived else 'Active'}",
        ]

        flags = []
        if self.isReadOnly:
            flags.append("read-only")
        if self.isLocked:
            flags.append("locked")
        if self.isAutoMuted:
            flags.append("auto-muted")
        if self.isTrusted is False:
            flags.append("untrusted(not-in-contacts)")
        if self.isNotSpam is False:
            flags.append("spam-flagged")
        if self.canSend is False:
            flags.append("cannot-send")
        if self.isOpened:
            flags.append("opened")

        if flags:
            lines.append(f"  flags       : {', '.join(flags)}")
        
        if self.disappearingModeTrigger:
            lines.append(f"  ephemeral   : initiator={self.disappearingModeInitiator} trigger={self.disappearingModeTrigger}")

        lines.append("───────────────────────────────────────────────────")
        return "\n".join(lines)

    def __repr__(self):
        return (
            f"ChatModelAPI("
            f"id='{self.id_serialized}', "
            f"title='{self.formattedTitle}', "
            f"unread={self.unreadCount}, "
            f"archived={self.isArchived}, "
            f"community={self.isCommunity}"
            f")"
        )
        
    def to_dict(self, include_none: bool = False) -> dict:
        """
        Export this ChatModelAPI as a flat Python dict.
        """
        raw = {
            "id_serialized": self.id_serialized,
            "unreadCount": self.unreadCount,
            "isAutoMuted": self.isAutoMuted,
            "timestamp": self.timestamp,
            "isArchived": self.isArchived,
            "isLocked": self.isLocked,
            "isNotSpam": self.isNotSpam,
            "disappearingModeTrigger": self.disappearingModeTrigger,
            "disappearingModeInitiator": self.disappearingModeInitiator,
            "unreadMentionCount": self.unreadMentionCount,
            "lastChatEntryTimestamp": self.lastChatEntryTimestamp,
            "isOpened": self.isOpened,
            "isReadOnly": self.isReadOnly,
            "isTrusted": self.isTrusted,
            "formattedTitle": self.formattedTitle,
            "groupSafetyChecked": self.groupSafetyChecked,
            "canSend": self.canSend,
            "proxyName": self.proxyName,
            "isCommunity": self.isCommunity,
        }
        if include_none:
            return raw
        return {k: v for k, v in raw.items() if v is not None}
