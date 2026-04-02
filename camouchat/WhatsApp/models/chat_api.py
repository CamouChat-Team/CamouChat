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
        Creates a ChatModelAPI from the raw dictionary returned by WA-JS.
        Handles the '__x_' prefixes automatically.
        """

        def get_val(key: str, default: Any = None):
            return data.get(key, data.get(f"__x_{key}", default))

        is_parent = get_val("isParentGroup", False)
        group_type = get_val("groupType", "DEFAULT")
        is_comm = (is_parent is True) | (group_type == "ANNOUNCEMENT")

        return cls(
            id_serialized=get_val("id_serialized") or data.get("id", {}).get("_serialized") or None,
            unreadCount=get_val("unreadCount") or None,
            isAutoMuted=get_val("isAutoMuted") or None,
            timestamp=get_val("t") or get_val("timestamp") or None,
            isArchived=get_val("archive") or None,
            isLocked=get_val("isLocked") or None,
            isNotSpam=get_val("notSpam") or None,
            disappearingModeTrigger=get_val("disappearingModeTrigger") or None,
            disappearingModeInitiator=get_val("disappearingModeInitiator") or None,
            unreadMentionCount=get_val("unreadMentionCount") or None,
            lastChatEntryTimestamp=get_val("lastChatEntryTimestamp") or None,
            isOpened=get_val("hasOpened") or None,
            isReadOnly=get_val("isReadOnly") or None,
            isTrusted=get_val("trusted") or None,
            formattedTitle=get_val("formattedTitle") or get_val("name") or None,
            groupSafetyChecked=get_val("groupSafetyChecked") or None,
            canSend=get_val("canSend") or None,
            proxyName=get_val("proxyName") or None,
            isCommunity=is_comm,
        )
