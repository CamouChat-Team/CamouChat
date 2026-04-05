from dataclasses import dataclass
from typing import Any, Dict, List, Optional


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
        MsgType (str | None): Message type: 'chat','image','video','ptt','document','revoked', etc.
        body (str | None): Text content, or base64 thumbnail for media.
        caption (str | None): Text caption attached to media.
        timestamp (int | None): Unix timestamp of the message.
        ack (int | None): 0=Pending, 1=Sent, 2=Delivered, 3=Read(Blue Ticks), 4=Played.

        # ── Presence / arrival flags ──────────────────────────────────────────
        isNew (bool | None): True if the message is unread LOCALLY in the browser UI.
        isNewMsg (bool | None): True if the message arrived on the wire in this session
                                (distinct from isNew which is the UI unread dot).
        recvFresh (bool | None): True when the message arrived in real-time, False when
                                 it was replayed from history-sync on reconnect.
        isMdHistoryMsg (bool | None): True if this is a message that was synced from history
                                      (multi-device history sync), not a live wire message.

        # ── Social flags ─────────────────────────────────────────────────────
        isStarMsg (bool | None): True if the message is starred/favorited.
        isForwarded (bool | None): True if the message has the "Forwarded" tag.
        forwardsCount (int | None): Number of times this message was forwarded.
        hasReaction (bool | None): True if someone reacted to this message.
        pendingDeleteForMe (bool | None): True if a "Delete for me" operation is in flight.

        # ── Disappearing / ephemeral ──────────────────────────────────────────
        ephemeralDuration (int | None): Disappearing message duration in seconds (0 if off).
        disappearingModeInitiator (str | None): Who triggered disappearing mode ('chat', 'admin', etc.).
        disappearingModeTrigger (str | None): What triggered it ('chat_settings', 'admin', etc.).

        # ── Special message type flags ────────────────────────────────────────
        isAvatar (bool | None): True if message is an avatar sticker.
        isVideoCallMessage (bool | None): True if the message is a call log/missed call alert.
        isDynamicReplyButtonsMsg (bool | None): True if message has WA Business dynamic reply buttons.
        isCarouselCard (bool | None): True if message is a WA Business carousel card.
        activeBotMsgStreamingInProgress (bool | None): True while a WA AI/bot reply is being streamed.

        # ── Quoted / reply fields ─────────────────────────────────────────────
        fromQuotedMsg (bool | None): True if this message is a reply to another message.
        isQuotedMsgAvailable (bool | None): True if the quoted message still exists in local DB.
        quotedMsgId (str | None): The serialized ID of the message being replied to.
        quotedMsgType (str | None): Type of the quoted message (e.g. 'image', 'chat').
        quotedMsgBody (str | None): First 120 chars of quoted message body/caption.
        quotedParticipant (str | None): JID of the person who sent the original quoted message.
        quotedRemoteJid (str | None): Chat JID where the quoted message lives.

        # ── Media fields ──────────────────────────────────────────────────────
        mimetype (str | None): e.g., 'image/jpeg', 'audio/ogg; codecs=opus'.
        directPath (str | None): Decryption URL path for the CDN.
        mediaKey (str | None): Base64 encryption key for downloading media.
        size (int | None): Size of the media in bytes.
        duration (int | None): Duration in seconds (for audio/video).
        isViewOnce (bool | None): True if sent as "View Once" media.

        # ── Poll fields ───────────────────────────────────────────────────────
        isQuestion (bool | None): True if this is a Poll message.
        pollName (str | None): The question / title text of the poll.
        pollType (str | None): 'POLL' or 'QUIZ' etc.
        pollContentType (str | None): 'TEXT' or 'IMAGE' etc.
        pollSelectableOptionsCount (int | None): Max number of options a voter may select (0 = unlimited).
        questionResponsesCount (int | None): Number of people who voted (from wire field).
        readQuestionResponsesCount (int | None): Read question responses count (internal WA field).

        # ── Event fields ──────────────────────────────────────────────────────
        eventName (str | None): Title of the event (type='event_creation').
        eventDescription (str | None): Body/description of the event.
        eventJoinLink (str | None): WhatsApp call or external join URL.
        eventStartTime (int | None): Unix timestamp of the event start.
        eventEndTime (int | None): Unix timestamp of the event end.
        isEventCanceled (bool | None): True if the event was subsequently canceled.
        eventIsScheduledCall (bool | None): True if the event is a scheduled WA call.

        # ── vCard fields ──────────────────────────────────────────────────────
        vcardFormattedName (str | None): Human-readable resolved display name from the vCard
                                         (FN field). Much cleaner than parsing vcardList.
        vcardList (list | None): Raw vCard payloads if MsgType == 'vcard' / 'multi_vcard'.

        # ── Misc ──────────────────────────────────────────────────────────────
        stickerSentTs (int | None): Original creation timestamp for stickers.
        isViewed (bool | None): Local UI state: True if the bubble no longer has the unread dot.

    Note:
        If a field is None it most likely means the webpack patch did not expose that property,
        or WhatsApp silently changed internal key names in a recent update.
    """

    # ── Identity ──────────────────────────────────────────────────────────────
    id_serialized: Optional[str]
    rowId: Optional[int]
    fromMe: Optional[bool]
    jid_From: Optional[str]
    jid_To: Optional[str]
    author: Optional[str]
    pushname: Optional[str]
    broadcast: Optional[bool]
    MsgType: Optional[str]
    body: Optional[str]
    caption: Optional[str]
    timestamp: Optional[int]
    ack: Optional[int]

    # ── Presence / arrival flags ──────────────────────────────────────────────
    isNew: Optional[bool]
    isNewMsg: Optional[bool]
    recvFresh: Optional[bool]
    isMdHistoryMsg: Optional[bool]

    # ── Social flags ──────────────────────────────────────────────────────────
    isStarMsg: Optional[bool]
    isForwarded: Optional[bool]
    forwardsCount: Optional[int]
    hasReaction: Optional[bool]
    pendingDeleteForMe: Optional[bool]

    # ── Disappearing / ephemeral ──────────────────────────────────────────────
    ephemeralDuration: Optional[int]
    disappearingModeInitiator: Optional[str]
    disappearingModeTrigger: Optional[str]

    # ── Special message type flags ────────────────────────────────────────────
    isAvatar: Optional[bool]
    isVideoCallMessage: Optional[bool]
    isDynamicReplyButtonsMsg: Optional[bool]
    isCarouselCard: Optional[bool]
    activeBotMsgStreamingInProgress: Optional[bool]

    # ── Quoted / reply fields ─────────────────────────────────────────────────
    fromQuotedMsg: Optional[bool]
    isQuotedMsgAvailable: Optional[bool]
    quotedMsgId: Optional[str]
    quotedMsgType: Optional[str]
    quotedMsgBody: Optional[str]
    quotedParticipant: Optional[str]
    quotedRemoteJid: Optional[str]

    # ── Mentions ──────────────────────────────────────────────────────────────
    mentionedJidList: Optional[List[str]]

    # ── Media fields ──────────────────────────────────────────────────────────
    mimetype: Optional[str]
    directPath: Optional[str]
    mediaKey: Optional[str]
    size: Optional[int]
    duration: Optional[int]
    isViewOnce: Optional[bool]

    # ── Poll fields ───────────────────────────────────────────────────────────
    isQuestion: Optional[bool]
    pollName: Optional[str]
    pollType: Optional[str]
    pollContentType: Optional[str]
    pollSelectableOptionsCount: Optional[int]
    questionResponsesCount: Optional[int]
    readQuestionResponsesCount: Optional[int]

    # ── Event fields ──────────────────────────────────────────────────────────
    eventName: Optional[str]
    eventDescription: Optional[str]
    eventJoinLink: Optional[str]
    eventStartTime: Optional[int]
    eventEndTime: Optional[int]
    isEventCanceled: Optional[bool]
    eventIsScheduledCall: Optional[bool]

    # ── vCard fields ──────────────────────────────────────────────────────────
    vcardFormattedName: Optional[str]
    vcardList: Optional[List[Any]]

    # ── Misc ──────────────────────────────────────────────────────────────────
    stickerSentTs: Optional[int]
    isViewed: Optional[bool]

    # ─────────────────────────────────────────────────────────────────────────

    _MEDIA_THUMB_TYPES: frozenset = frozenset(
        {
            "image",
            "video",
            "sticker",
            "document",
            "audio",
            "ptt",
            "gif",
            "product",
            "order",
        }
    )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MessageModelAPI":
        """
        Build MessageModelAPI from the raw dict returned by WAJS_Scripts.get_message_by_id().

        Key mapping (JS dump → Python field):
          id_serialized      → id_serialized
          from_serialized    → jid_From   (WID._serialized pre-extracted by JS)
          to_serialized      → jid_To     (WID._serialized pre-extracted by JS)
          author_serialized  → author     (group messages only)
          t                  → timestamp  (Unix seconds)
          type               → MsgType
          body               → body
          notifyName         → pushname
          star               → isStarMsg
          isForwarded        → isForwarded
          forwardingScore    → forwardsCount
          viewed             → isViewed
          isVideoCall        → isVideoCallMessage

        Bug-fixes vs prior version:
          [BUG-1] ciphertext type is NO LONGER clobbered to 'viewonce'. A ciphertext-arriving
                  message is simply tagged isViewOnce=False and left for the WA re-fire to
                  deliver the real decrypted type. Only explicitly marked view-once messages
                  (isViewOnce==True in the raw payload) set that flag.
          [BUG-2] questionResponsesCount now reads the wire field 'questionResponsesCount'
                  directly, not len(pollOptions) which counted candidate options, not voters.
        """

        def g(key: str, default: Any = None) -> Any:
            # Check plain key, then __x_ prefixed (WPP Backbone accessor pattern)
            return data.get(key, data.get(f"__x_{key}", default))

        # ── timestamp ─────────────────────────────────────────────────────────
        t_val = g("t")
        timestamp = t_val if t_val is not None else g("timestamp")

        # ── media size ────────────────────────────────────────────────────────
        size_val = g("size")
        size = size_val if size_val is not None else g("fileLength")

        question_responses = g("questionResponsesCount", 0)

        # ── Poll type detection ───────────────────────────────────────────────
        is_poll = g("type") == "poll_creation"
        is_question = g("isAnyQuestion") or is_poll

        return cls(
            # ── Identity ──────────────────────────────────────────────────────
            id_serialized=g("id_serialized"),
            rowId=g("rowId"),
            fromMe=g("fromMe"),
            jid_From=g("from_serialized"),
            jid_To=g("to_serialized"),
            author=g("author_serialized"),
            pushname=g("notifyName") or g("pushname"),
            broadcast=g("broadcast"),
            MsgType=g("type"),
            body=g("body"),
            caption=g("caption"),
            timestamp=timestamp,
            ack=g("ack", 0),
            # ── Presence / arrival flags ───────────────────────────────────────
            isNew=g("isNew"),
            isNewMsg=g("isNewMsg"),
            recvFresh=g("recvFresh"),
            isMdHistoryMsg=g("isMdHistoryMsg"),
            # ── Social flags ───────────────────────────────────────────────────
            isStarMsg=g("star"),
            isForwarded=g("isForwarded"),
            forwardsCount=(
                g("forwardingScore") if g("forwardingScore") is not None else g("forwardsCount", 0)
            ),
            hasReaction=g("hasReaction"),
            pendingDeleteForMe=g("pendingDeleteForMe"),
            # ── Disappearing / ephemeral ───────────────────────────────────────
            ephemeralDuration=g("ephemeralDuration", 0),
            disappearingModeInitiator=g("disappearingModeInitiator"),
            disappearingModeTrigger=g("disappearingModeTrigger"),
            # ── Special message type flags ─────────────────────────────────────
            isAvatar=g("isAvatar"),
            isVideoCallMessage=g("isVideoCall"),
            isDynamicReplyButtonsMsg=g("isDynamicReplyButtonsMsg"),
            isCarouselCard=g("isCarouselCard"),
            activeBotMsgStreamingInProgress=g("activeBotMsgStreamingInProgress"),
            # ── Quoted / reply ─────────────────────────────────────────────────
            fromQuotedMsg=bool(g("quotedMsg") or g("quotedMsgId") or g("quotedStanzaID")),
            isQuotedMsgAvailable=bool(g("quotedMsg")),
            quotedMsgId=g("quotedMsgId") or g("quotedStanzaID"),
            quotedMsgType=g("quotedMsgType"),
            quotedMsgBody=g("quotedMsgBody"),
            quotedParticipant=g("quotedParticipant"),
            quotedRemoteJid=g("quotedRemoteJid"),
            
            # ── Mentions ───────────────────────────────────────────────────────
            mentionedJidList=g("mentionedJidList") or None,

            # ── Media ──────────────────────────────────────────────────────────
            mimetype=g("mimetype"),
            directPath=g("directPath"),
            mediaKey=g("mediaKey"),
            size=size,
            duration=g("duration"),
            isViewOnce=g("isViewOnce", False),
            # ── Poll ───────────────────────────────────────────────────────────
            isQuestion=is_question,
            pollName=g("pollName"),
            pollType=g("pollType"),
            pollContentType=g("pollContentType"),
            pollSelectableOptionsCount=g("pollSelectableOptionsCount"),
            questionResponsesCount=question_responses,
            readQuestionResponsesCount=g("readQuestionResponsesCount"),
            # ── Event ──────────────────────────────────────────────────────────
            eventName=g("eventName"),
            eventDescription=g("eventDescription"),
            eventJoinLink=g("eventJoinLink"),
            eventStartTime=g("eventStartTime"),
            eventEndTime=g("eventEndTime"),
            isEventCanceled=g("isEventCanceled"),
            eventIsScheduledCall=g("eventIsScheduledCall"),
            # ── vCard ──────────────────────────────────────────────────────────
            vcardFormattedName=g("vcardFormattedName"),
            vcardList=g("vcardList") or None,
            # ── Misc ───────────────────────────────────────────────────────────
            stickerSentTs=g("stickerSentTs"),
            isViewed=g("viewed"),
        )

    def __str__(self) -> str:
        lines = [
            "─── MessageModelAPI ───────────────────────────────",
            f"  id          : {self.id_serialized}",
            f"  type        : {self.MsgType}",
            f"  from        : {'Me' if self.fromMe else self.jid_From}",
            f"  to          : {self.jid_To}",
        ]

        if self.author:
            lines.append(f"  author      : {self.author}  (group sender)")
        if self.pushname:
            lines.append(f"  pushname    : {self.pushname}")

        lines.append(f"  timestamp   : {self.timestamp}")
        lines.append(f"  ack         : {self.ack}  (0=pending 1=sent 2=delivered 3=read 4=played)")

        # ── Body / caption ────────────────────────────────────────────────────
        if self.body:
            body = self.body
            if self.MsgType == "vcard":
                # vCard body is raw VCF text — show first 3 lines cleanly
                preview = "\n         ".join(body.splitlines()[:3])
                body_display = preview + ("…[vCard]" if len(body) > 120 else "")
            elif self.MsgType in self._MEDIA_THUMB_TYPES and len(body) > 100:
                # Only media types carry a base64 JPEG thumbnail in `body`.
                # A long body on a chat/text message is just normal long text.
                body_display = f"{body[:40]}…[thumbnail b64, {len(body)} chars]"
            elif len(body) > 200:
                # Long plain-text body — truncate with ellipsis, no misleading label
                body_display = f"{body[:200]}…"
            else:
                body_display = body
            lines.append(f"  body        : {body_display}")
        if self.caption:
            lines.append(f"  caption     : {self.caption}")

        # ── Flags — only non-default / True ones ──────────────────────────────
        flags = []
        if self.fromMe:
            flags.append("fromMe")
        if self.isForwarded:
            flags.append(f"forwarded×{self.forwardsCount}")
        if self.hasReaction:
            flags.append("hasReaction")
        if self.isStarMsg:
            flags.append("starred")
        if self.broadcast:
            flags.append("broadcast")
        if self.isViewOnce:
            flags.append("viewOnce")
        if self.isVideoCallMessage:
            flags.append("callLog")
        if self.isQuestion:
            flags.append(f"poll({self.questionResponsesCount} votes)")
        if self.ephemeralDuration:
            flags.append(f"ephemeral={self.ephemeralDuration}s")
        if self.isDynamicReplyButtonsMsg:
            flags.append("dynamicReplyButtons")
        if self.isCarouselCard:
            flags.append("carouselCard")
        if self.activeBotMsgStreamingInProgress:
            flags.append("botStreaming")
        if self.pendingDeleteForMe:
            flags.append("pendingDelete")
        if self.MsgType == "ciphertext":
            flags.append("⚠ ciphertext(pending-decrypt)")
        if flags:
            lines.append(f"  flags       : {', '.join(flags)}")

        # ── Arrival / sync info ───────────────────────────────────────────────
        arrival_flags = []
        if self.isNewMsg:
            arrival_flags.append("wire-new")
        if self.recvFresh:
            arrival_flags.append("recvFresh")
        if self.isMdHistoryMsg:
            arrival_flags.append("history-sync")
        if arrival_flags:
            lines.append(f"  arrival     : {', '.join(arrival_flags)}")

        # ── Ephemeral detail ──────────────────────────────────────────────────
        if self.disappearingModeInitiator or self.disappearingModeTrigger:
            lines.append(
                f"  ephemeral   : initiator={self.disappearingModeInitiator}"
                f"  trigger={self.disappearingModeTrigger}"
            )

        # ── Quoted message ────────────────────────────────────────────────────
        if self.fromQuotedMsg:
            lines.append(f"  ↩ quotedId   : {self.quotedMsgId}")
            if self.quotedMsgType:
                lines.append(f"  ↩ quotedType : {self.quotedMsgType}")
            if self.quotedMsgBody:
                lines.append(
                    f"  ↩ quotedBody : {self.quotedMsgBody[:80]}"
                    f"{'…' if len(self.quotedMsgBody or '') > 80 else ''}"
                )
            if self.quotedParticipant:
                lines.append(f"  ↩ quotedFrom : {self.quotedParticipant}")
            if self.quotedRemoteJid:
                lines.append(f"  ↩ quotedChat : {self.quotedRemoteJid}")

        # ── Mentions ──────────────────────────────────────────────────────────
        if self.mentionedJidList:
            mentions = self.mentionedJidList
            lines.append(f"  mentions    : {len(mentions)} user(s)")
            if len(mentions) <= 3:
                lines.append(f"                {', '.join(mentions)}")
            else:
                lines.append(f"                {', '.join(mentions[:3])} (+{len(mentions)-3} more)")

        # ── Media ─────────────────────────────────────────────────────────────
        if self.mimetype:
            lines.append(f"  mimetype    : {self.mimetype}")
        if self.size:
            sz = self.size
            if sz >= 1_048_576:
                size_str = f"{sz / 1_048_576:.2f} MB"
            elif sz >= 1024:
                size_str = f"{sz / 1024:.1f} KB"
            else:
                size_str = f"{sz} bytes"
            lines.append(f"  size        : {size_str}")
        if self.duration:
            lines.append(f"  duration    : {self.duration}s")

        # ── Poll detail ───────────────────────────────────────────────────────
        if self.isQuestion:
            if self.pollName:
                lines.append(f"  pollName    : {self.pollName}")
            if self.pollType:
                lines.append(f"  pollType    : {self.pollType}  content={self.pollContentType}")
            if self.pollSelectableOptionsCount is not None:
                sel = self.pollSelectableOptionsCount
                lines.append(f"  pollSelect  : {sel if sel else 'unlimited'} option(s) per voter")

        # ── Event detail ──────────────────────────────────────────────────────
        if self.MsgType == "event_creation":
            if self.eventName:
                lines.append(f"  eventName   : {self.eventName}")
            if self.eventDescription:
                desc = self.eventDescription
                lines.append(f"  eventDesc   : {desc[:80]}{'…' if len(desc) > 80 else ''}")
            if self.eventStartTime:
                lines.append(f"  eventTime   : {self.eventStartTime} → {self.eventEndTime}")
            if self.eventJoinLink:
                lines.append(f"  eventLink   : {self.eventJoinLink}")
            if self.isEventCanceled:
                lines.append("  ⚠ EVENT CANCELED")
            if self.eventIsScheduledCall:
                lines.append("  eventKind   : scheduled call")

        # ── vCard detail ──────────────────────────────────────────────────────
        if self.MsgType in ("vcard", "multi_vcard"):
            if self.vcardFormattedName:
                lines.append(f"  vcardName   : {self.vcardFormattedName}")
            if self.vcardList:
                lines.append(f"  vcardCount  : {len(self.vcardList)} contact(s)")

        lines.append("───────────────────────────────────────────────────")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"MessageModelAPI("
            f"id='{self.id_serialized}', "
            f"type='{self.MsgType}', "
            f"fromMe={self.fromMe}, "
            f"timestamp={self.timestamp}"
            f")"
        )

    def to_dict(self, include_none: bool = False) -> Dict[str, Any]:
        """
        Export this MessageModelAPI as a flat Python dict.

        Useful for:
        - JSON serialization  → json.dumps(msg.to_dict())
        - Structured logging  → logger.info("msg", extra=msg.to_dict())
        - Custom DB storage   → db.insert(msg.to_dict())
        - Forwarding to APIs  → requests.post(url, json=msg.to_dict())
        - Equality comparison → msg_a.to_dict() == msg_b.to_dict()

        Args:
            include_none: If False (default), keys whose value is None are
                          omitted to keep the output compact. Set to True to
                          get a fixed-schema dict with every field present.

        Returns:
            Dict[str, Any] — all fields, grouped logically.
        """
        raw: Dict[str, Any] = {
            # ── Identity ──────────────────────────────────────────────────────
            "id_serialized": self.id_serialized,
            "rowId": self.rowId,
            "fromMe": self.fromMe,
            "jid_From": self.jid_From,
            "jid_To": self.jid_To,
            "author": self.author,
            "pushname": self.pushname,
            "broadcast": self.broadcast,
            "MsgType": self.MsgType,
            "body": self.body,
            "caption": self.caption,
            "timestamp": self.timestamp,
            "ack": self.ack,
            # ── Presence / arrival ────────────────────────────────────────────
            "isNew": self.isNew,
            "isNewMsg": self.isNewMsg,
            "recvFresh": self.recvFresh,
            "isMdHistoryMsg": self.isMdHistoryMsg,
            # ── Social flags ──────────────────────────────────────────────────
            "isStarMsg": self.isStarMsg,
            "isForwarded": self.isForwarded,
            "forwardsCount": self.forwardsCount,
            "hasReaction": self.hasReaction,
            "pendingDeleteForMe": self.pendingDeleteForMe,
            # ── Disappearing / ephemeral ──────────────────────────────────────
            "ephemeralDuration": self.ephemeralDuration,
            "disappearingModeInitiator": self.disappearingModeInitiator,
            "disappearingModeTrigger": self.disappearingModeTrigger,
            # ── Special type flags ────────────────────────────────────────────
            "isAvatar": self.isAvatar,
            "isVideoCallMessage": self.isVideoCallMessage,
            "isDynamicReplyButtonsMsg": self.isDynamicReplyButtonsMsg,
            "isCarouselCard": self.isCarouselCard,
            "activeBotMsgStreamingInProgress": self.activeBotMsgStreamingInProgress,
            # ── Quoted / reply ────────────────────────────────────────────────
            "fromQuotedMsg": self.fromQuotedMsg,
            "isQuotedMsgAvailable": self.isQuotedMsgAvailable,
            "quotedMsgId": self.quotedMsgId,
            "quotedMsgType": self.quotedMsgType,
            "quotedMsgBody": self.quotedMsgBody,
            "quotedParticipant": self.quotedParticipant,
            "quotedRemoteJid": self.quotedRemoteJid,
            # ── Mentions ──────────────────────────────────────────────────────
            "mentionedJidList": self.mentionedJidList,
            # ── Media ─────────────────────────────────────────────────────────
            "mimetype": self.mimetype,
            "directPath": self.directPath,
            "mediaKey": self.mediaKey,
            "size": self.size,
            "duration": self.duration,
            "isViewOnce": self.isViewOnce,
            # ── Poll ──────────────────────────────────────────────────────────
            "isQuestion": self.isQuestion,
            "pollName": self.pollName,
            "pollType": self.pollType,
            "pollContentType": self.pollContentType,
            "pollSelectableOptionsCount": self.pollSelectableOptionsCount,
            "questionResponsesCount": self.questionResponsesCount,
            "readQuestionResponsesCount": self.readQuestionResponsesCount,
            # ── Event ─────────────────────────────────────────────────────────
            "eventName": self.eventName,
            "eventDescription": self.eventDescription,
            "eventJoinLink": self.eventJoinLink,
            "eventStartTime": self.eventStartTime,
            "eventEndTime": self.eventEndTime,
            "isEventCanceled": self.isEventCanceled,
            "eventIsScheduledCall": self.eventIsScheduledCall,
            # ── vCard ─────────────────────────────────────────────────────────
            "vcardFormattedName": self.vcardFormattedName,
            "vcardList": self.vcardList,
            # ── Misc ──────────────────────────────────────────────────────────
            "stickerSentTs": self.stickerSentTs,
            "isViewed": self.isViewed,
        }
        if include_none:
            return raw
        return {k: v for k, v in raw.items() if v is not None}
