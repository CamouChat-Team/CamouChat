"""
Works on new Wa-js Based API scripts.

Wraps the CHAT API's data into a dataclass
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
        return (
            f"[{self.formattedTitle}] "
            f"Unread: {self.unreadCount or 0} | "
            f"{'Archived' if self.isArchived else 'Active'} | "
            f"{'Community' if self.isCommunity else 'Chat'}"
        )

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
