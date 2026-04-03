from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class MessageModelAPI:
    """
    Normalized Data Model for a WhatsApp Message.
    Parses the raw Webpack dictionary into a clean, predictable Python object.

    Attributes:
        id_serialized (str | None): Full unique ID (e.g., 'false_1234@c.us_ABCDEF').
        rowId (int | None): IndexedDB row ID (useful for pagination/anchors).
        fromMe (bool | None): True if the message was sent by the authenticated user.
        jid_From (str | None): JID of the sender (or the Group JID if received in a group).
        jid_To (str | None): JID of the recipient.
        author (str | None): JID of the specific person who sent it (ONLY present in group chats).
        pushname (str | None): The notification name of the sender.
        broadcast (bool | None): True if sent via a Broadcast List.
        MsgType (str | None): Message type: 'chat', 'image', 'video', 'ptt', 'document', 'revoked', etc.
        body (str | None): Text content, or base64 thumbnail for media.
        caption (str | None): Text caption attached to media.
        timestamp (int | None): Unix timestamp of the message.
        ack (int | None): 0=Pending, 1=Sent, 2=Delivered, 3=Read(Blue Ticks), 4=Played.
        isNew (bool | None): True if the message is unread LOCALLY in the browser UI.
        isStarMsg (bool | None): True if the message is starred/favorited.
        isForwarded (bool | None): True if the message has the "Forwarded" tag.
        forwardsCount (int | None): Number of times this message was forwarded.
        hasReaction (bool | None): True if someone reacted to this message.
        ephemeralDuration (int | None): Disappearing message duration in seconds (0 if off).
        isAvatar (bool | None): True if message is an avatar sticker.
        isVideoCallMessage (bool | None): True if the message is a call log/missed call alert.
        fromQuotedMsg (bool | None): True if this message is a reply to another message.
        isQuotedMsgAvailable (bool | None): True if the quoted message still exists in the local database.
        quotedMsgId (str | None): The serialized ID of the message being replied to.
        quotedParticipant (str | None): The JID of the person who sent the original quoted message.
        mimetype (str | None): e.g., 'image/jpeg', 'audio/ogg; codecs=opus'.
        directPath (str | None): Decryption URL path for the CDN.
        mediaKey (str | None): Base64 encryption key for downloading media.
        size (int | None): Size of the media in bytes.
        duration (int | None): Duration in seconds (for audio/video).
        isViewOnce (bool | None): True if sent as "View Once" media.
        isQuestion (bool | None): True if this is a Poll message.
        questionResponsesCount (int | None): Number of people who voted.
        readQuestionResponsesCount (int | None): Number of read question responses (if applicable).
        stickerSentTs (int | None): Original creation timestamp for stickers (used for "Recents" sorting).
        isViewed (bool | None): Local UI state: True if the bubble no longer has the green unread dot.
        vcardList (list | None): List of vCards if MsgType == "vcard" or "multi_vcard".

    If the specified field is None , its Mostly means the webpack was not successfully patched the whatsapp.
    Or the webpack ids are changed due to silent update from whatsapp.
    """

    id_serialized: str | None
    rowId: int | None
    fromMe: bool | None
    jid_From: str | None
    jid_To: str | None
    author: str | None
    pushname: str | None
    broadcast: bool | None
    MsgType: str | None
    body: str | None
    caption: str | None
    timestamp: int | None
    ack: int | None
    isNew: bool | None
    isStarMsg: bool | None
    isForwarded: bool | None
    forwardsCount: int | None
    hasReaction: bool | None
    ephemeralDuration: int | None
    isAvatar: bool | None
    isVideoCallMessage: bool | None
    fromQuotedMsg: bool | None
    isQuotedMsgAvailable: bool | None
    quotedMsgId: str | None
    quotedParticipant: str | None
    mimetype: str | None
    directPath: str | None
    mediaKey: str | None
    size: int | None
    duration: int | None
    isViewOnce: bool | None
    isQuestion: bool | None
    questionResponsesCount: int | None
    readQuestionResponsesCount: int | None
    stickerSentTs: int | None
    isViewed: bool | None
    vcardList: list | None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MessageModelAPI":
        """
        Wa_js based MessageModelAPI , creates cls Object from dict of type : MessageModelAPI.
        :param data:
        :return: MessageModelAPI
        """
        def get_val(key: str, default: Any = None):
            return data.get(key, data.get(f"__x_{key}", default))

        def safe(v):
            return v if v is not None else None

        id_obj = get_val("id") or {}

        id_serialized = get_val("id_serialized") or id_obj.get("_serialized")

        from_me = get_val("fromMe")
        if from_me is None:
            from_me = id_obj.get("fromMe", False)

        msg_ctx = get_val("msgContextInfo") or {}
        poll_opts = get_val("pollOptions") or []

        t_val = get_val("t")
        timestamp = t_val if t_val is not None else get_val("timestamp")

        size_val = get_val("size")
        size = size_val if size_val is not None else get_val("fileLength")

        return cls(
            id_serialized=id_serialized,
            rowId=safe(get_val("rowId")),
            fromMe=from_me,
            jid_From=safe(get_val("from")),
            jid_To=safe(get_val("to")),
            author=safe(get_val("author")),
            pushname=get_val("notifyName") or get_val("pushname"),
            broadcast=safe(get_val("broadcast")),
            MsgType=safe(get_val("type")),
            body=safe(get_val("body")),
            caption=safe(get_val("caption")),
            timestamp=safe(timestamp),
            ack=get_val("ack", 0),
            isNew=safe(get_val("isNew")),
            isStarMsg=safe(get_val("star")),
            isForwarded=safe(get_val("isForwarded")),
            forwardsCount=(
                get_val("forwardingScore")
                if get_val("forwardingScore") is not None
                else get_val("forwardsCount", 0)
            ),
            hasReaction=safe(get_val("hasReaction")),
            ephemeralDuration=get_val("ephemeralDuration", 0),
            isAvatar=safe(get_val("isAvatar")),
            isVideoCallMessage=safe(get_val("isVideoCall")),
            fromQuotedMsg=bool(get_val("quotedMsg")),
            isQuotedMsgAvailable=bool(get_val("quotedMsg")) and not get_val("quotedStanzaID"),
            quotedMsgId=get_val("quotedStanzaID") or msg_ctx.get("stanzaId"),
            quotedParticipant=get_val("quotedParticipant") or msg_ctx.get("participant"),
            mimetype=safe(get_val("mimetype")),
            directPath=safe(get_val("directPath")),
            mediaKey=safe(get_val("mediaKey")),
            size=safe(size),
            duration=safe(get_val("duration")),
            isViewOnce=safe(get_val("isViewOnce")),
            isQuestion=safe(get_val("isAnyQuestion")) or (get_val("type") == "poll_creation"),
            questionResponsesCount=len(poll_opts) if poll_opts else 0,
            readQuestionResponsesCount=None,
            stickerSentTs=safe(get_val("stickerSentTs")),
            isViewed=safe(get_val("viewed")),
            vcardList=get_val("vcardList") or None,
        )

    def __str__(self):
        return (
            f"[{self.timestamp}] "
            f"{'Me' if self.fromMe else self.jid_From} → {self.jid_To} | "
            f"{self.MsgType}: "
            f"{self.body or self.caption or '<media>'}"
        )

    def __repr__(self):
        return (
            f"MessageModelAPI("
            f"id='{self.id_serialized}', "
            f"type='{self.MsgType}', "
            f"fromMe={self.fromMe}, "
            f"timestamp={self.timestamp}"
            f")"
        )
