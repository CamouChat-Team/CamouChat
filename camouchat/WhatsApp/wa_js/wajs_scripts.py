import json


class WAJS_Scripts:
    """
    The Vault: Raw JavaScript execution strings for Playwright injection via WapiWrapper.
    All scripts are fragments executed inside the CustomEvent bridge in WapiWrapper._evaluate_stealth.

    NOTE: `wpp` here refers to `window.__react_devtools_hook` (the hidden WPP cache).
          The bridge script sets `const wpp = window.__react_devtools_hook;` before eval.
    """

    # ─────────────────────────────────────────────
    # 1. CORE & CONNECTION
    # ─────────────────────────────────────────────

    @classmethod
    def is_authenticated(cls) -> str:
        """Check if WhatsApp session is authenticated."""
        return "wpp.conn.isAuthenticated()"

    # ─────────────────────────────────────────────
    # 2. CHAT METADATA
    # ─────────────────────────────────────────────

    @classmethod
    def list_chats(
        cls,
        count: int | None = None,
        direction: str = "after",
        only_users: bool = False,
        only_groups: bool = False,
        only_communities: bool = False,
        only_unread: bool = False,
        only_archived: bool = False,
        only_newsletter: bool = False,
        with_labels: list | None = None,
        anchor_chat_id: str | None = None,
        ignore_group_metadata: bool = True,
    ) -> str:
        """
        Fetch a list of chats from ChatStore — same ordering as the WhatsApp sidebar.
        Mirrors all WPP.chat.list() filter options.

        Args:
            count:                  Max chats to return. None = all.
            direction:              'after' (default) or 'before' relative to anchor_chat_id.
            only_users:             Only 1-on-1 personal chats.
            only_groups:            Only group chats.
            only_communities:       Only Community parent groups.
            only_unread:            Only chats with unread messages.
            only_archived:          Only archived chats.
            only_newsletter:        Only WhatsApp Channels.
            with_labels:            Filter by label names or IDs (Business accounts).
            anchor_chat_id:         @c.us or @g.us ID to paginate from.
            ignore_group_metadata:  Skip fetching group member data (faster, default True).
        """
        import json as _json

        opts: dict = {
            "direction": direction,
            "ignoreGroupMetadata": ignore_group_metadata,
        }
        if count is not None:
            opts["count"] = count
        if only_users:
            opts["onlyUsers"] = True
        if only_groups:
            opts["onlyGroups"] = True
        if only_communities:
            opts["onlyCommunities"] = True
        if only_unread:
            opts["onlyWithUnreadMessage"] = True
        if only_archived:
            opts["onlyArchived"] = True
        if only_newsletter:
            opts["onlyNewsletter"] = True
        if with_labels is not None:
            opts["withLabels"] = with_labels
        if anchor_chat_id is not None:
            opts["id"] = anchor_chat_id

        opts_js = _json.dumps(opts)

        return f"""
            wpp.chat.list({opts_js}).then(chats =>
                chats.map(chat => {{
                    // Dump all primitive properties from the ChatModel
                    const dump = {{}};
                    for (let key in chat) {{
                        const val = chat[key];
                        if (typeof val === 'string' || typeof val === 'number' || typeof val === 'boolean') {{
                            dump[key] = val;
                        }}
                    }}
                    // Resolve key nested Wid objects
                    if (chat.id)      dump['id_serialized']      = chat.id._serialized;
                    if (chat.contact) {{
                        dump['contact_name']     = chat.contact.name     ?? null;
                        dump['contact_pushname'] = chat.contact.pushname ?? null;
                    }}
                    return dump;
                }})
            )
        """

    @classmethod
    def get_chat(cls, chat_id: str) -> str:
        """
        Fetch all primitive metadata fields for a specific chat from React memory.
        Dynamically extracts all scalar properties + key nested objects.
        """
        return f"""
            (() => {{
                const chat = wpp.chat.get('{chat_id}');
                if (!chat) return {{ error: "Chat not found in Meta memory." }};

                // Dump all primitive properties from the React model
                const dump = {{}};
                for (let key in chat) {{
                    const val = chat[key];
                    if (typeof val === 'string' || typeof val === 'number' || typeof val === 'boolean') {{
                        dump[key] = val;
                    }}
                }}

                // Manually extract crucial nested objects to prevent structured-clone errors
                if (chat.id) dump["id_serialized"] = chat.id._serialized;
                if (chat.contact) {{
                    dump["contact_name"]     = chat.contact.name     ?? null;
                    dump["contact_pushname"] = chat.contact.pushname ?? null;
                }}

                return dump;
            }})()
        """

    # ─────────────────────────────────────────────
    # 3. MESSAGE FETCHING
    # ─────────────────────────────────────────────

    @classmethod
    def get_messages(
        cls,
        chat_id: str,
        count: int = 50,
        direction: str = "before",
        only_unread: bool = False,
        media: str | None = None,
        include_calls: bool = False,
        anchor_msg_id: str | None = None,
    ) -> str:
        """
        Fetch messages for a chat from React RAM.
        Returns the full raw dump of every scalar property on each MsgModel —
        same approach as get_chat() — so nothing is hidden.

        Args:
            chat_id:        The WhatsApp @c.us or @g.us ID.
            count:          Number of messages to fetch. Use -1 for all.
            direction:      'before' (default) or 'after' relative to anchor_msg_id.
            only_unread:    Only return unread messages.
            media:          Filter to 'all' | 'image' | 'document' | 'url' | None.
            include_calls:  Whether to include call_log entries in results.
            anchor_msg_id:  Optional full message ID to paginate from (e.g 'true_916..._ABCD').
        """
        opts: dict = {
            "count": count,
            "direction": direction,
            "onlyUnread": only_unread,
            "includeCallMessages": include_calls,
        }
        if media is not None:
            opts["media"] = media
        if anchor_msg_id is not None:
            opts["id"] = anchor_msg_id

        opts_js = json.dumps(opts)

        return f"""
            wpp.chat.getMessages('{chat_id}', {opts_js}).then(messages =>
                messages.map(m => {{
                    // Get the raw attributes object (MsgModel stores data in .attributes)
                    const attrs = m.attributes || m;

                    // Helper: convert a Uint8Array/ArrayBuffer to base64
                    const toB64 = (buf) => {{
                        const bytes = buf instanceof Uint8Array ? buf : new Uint8Array(buf);
                        let b64 = '';
                        const chunk = 8192;
                        for (let i = 0; i < bytes.length; i += chunk) {{
                            b64 += String.fromCharCode(...bytes.subarray(i, i + chunk));
                        }}
                        return btoa(b64);
                    }};

                    // Dynamically dump ALL primitive + binary properties
                    const dump = {{}};
                    for (let key in attrs) {{
                        const val = attrs[key];
                        if (typeof val === 'string' || typeof val === 'number' || typeof val === 'boolean') {{
                            dump[key] = val;
                        }} else if (val instanceof Uint8Array || val instanceof ArrayBuffer) {{
                            // Binary fields (e.g. mediaKey for view-once) → base64
                            dump[key] = toB64(val);
                        }}
                    }}

                    // Manually resolve nested Wid/MsgKey objects that hold key identifiers
                    if (attrs.id)     dump['id_serialized'] = attrs.id._serialized;
                    if (attrs.from)   dump['from_serialized'] = attrs.from._serialized ?? attrs.from;
                    if (attrs.to)     dump['to_serialized']   = attrs.to._serialized   ?? attrs.to;
                    if (attrs.author) dump['author_serialized'] = attrs.author._serialized ?? null;
                    if (attrs.quotedMsg?.id) dump['quotedMsgId'] = attrs.quotedMsg.id._serialized;

                    return dump;
                }})
            )
        """

    @classmethod
    def get_message_by_id(cls, msg_id: str) -> str:
        """
        Fetch a single specific message by its full serialized ID.
        Returns full raw dump of all scalar properties on the MsgModel.

        Args:
            msg_id: Full message key string e.g. 'true_916398014720@c.us_ABCDE123'
        """
        return f"""
            wpp.chat.getMessageById('{msg_id}').then(m => {{
                const attrs = m.attributes || m;
                const toB64 = (buf) => {{
                    const bytes = buf instanceof Uint8Array ? buf : new Uint8Array(buf);
                    let b64 = '';
                    const chunk = 8192;
                    for (let i = 0; i < bytes.length; i += chunk) {{
                        b64 += String.fromCharCode(...bytes.subarray(i, i + chunk));
                    }}
                    return btoa(b64);
                }};
                const dump = {{}};
                for (let key in attrs) {{
                    const val = attrs[key];
                    if (typeof val === 'string' || typeof val === 'number' || typeof val === 'boolean') {{
                        dump[key] = val;
                    }} else if (val instanceof Uint8Array || val instanceof ArrayBuffer) {{
                        dump[key] = toB64(val);
                    }}
                }}
                if (attrs.id)     dump['id_serialized'] = attrs.id._serialized;
                if (attrs.from)   dump['from_serialized'] = attrs.from._serialized ?? attrs.from;
                if (attrs.to)     dump['to_serialized']   = attrs.to._serialized   ?? attrs.to;
                if (attrs.author) dump['author_serialized'] = attrs.author._serialized ?? null;
                if (attrs.quotedMsg?.id) dump['quotedMsgId'] = attrs.quotedMsg.id._serialized;
                return dump;
            }})
        """

    # ─────────────────────────────────────────────
    # 4. ACTIONS — TIER 3 FALLBACKS
    # ─────────────────────────────────────────────

    @classmethod
    def send_text_message(cls, chat_id: str, message: str) -> str:
        """Pure api text send — no UI interaction required."""
        safe_msg = json.dumps(message)
        return f"wpp.chat.sendTextMessage('{chat_id}', {safe_msg})"

    @classmethod
    def mark_is_read(cls, chat_id: str) -> str:
        """Force-mark a chat as read at the api level."""
        return f"wpp.chat.markIsRead('{chat_id}')"

    # ─────────────────────────────────────────────
    # 5. INDEXDB — DISK HISTORY
    # ─────────────────────────────────────────────

    @classmethod
    def indexdb_get_messages(
        cls,
        min_row_id: int,
        limit: int = 50,
    ) -> str:
        """
        Fetch messages from browser disk storage (IndexedDB) across ALL chats sequentially.

        Args:
            min_row_id: The lower bound integer rowId.
            limit: Number of records to return.
        """
        return f"""
            wpp.indexdb.getMessagesFromRowId({{
                minRowId: {min_row_id},
                limit: {limit}
            }}).then(messages =>
                messages.map(m => {{
                    const attrs = m.attributes || m;
                    const dump = {{}};
                    for (let key in attrs) {{
                        const val = attrs[key];
                        if (typeof val === 'string' || typeof val === 'number' || typeof val === 'boolean') {{
                            dump[key] = val;
                        }}
                    }}
                    if (attrs.id)     dump['id_serialized']     = attrs.id._serialized;
                    if (attrs.from)   dump['from_serialized']   = attrs.from._serialized ?? attrs.from;
                    if (attrs.to)     dump['to_serialized']     = attrs.to._serialized   ?? attrs.to;
                    if (attrs.author) dump['author_serialized'] = attrs.author._serialized ?? null;
                    if (attrs.quotedMsg?.id) dump['quotedMsgId'] = attrs.quotedMsg.id._serialized;
                    return dump;
                }})
            )
        """

    # ─────────────────────────────────────────────
    # 6. NEWSLETTER (CHANNELS)
    # ─────────────────────────────────────────────

    @classmethod
    def newsletter_list(cls) -> str:
        """
        Fetch all newsletters (WhatsApp Channels) you follow.
        Returns the raw list via chat.list({onlyNewsletter: true}).
        """
        return """
            wpp.chat.list({ onlyNewsletter: true, ignoreGroupMetadata: true }).then(chats =>
                chats.map(chat => {
                    const dump = {};
                    for (let key in chat) {
                        const val = chat[key];
                        if (typeof val === 'string' || typeof val === 'number' || typeof val === 'boolean') {
                            dump[key] = val;
                        }
                    }
                    if (chat.id) dump['id_serialized'] = chat.id._serialized;
                    return dump;
                })
            )
        """

    @classmethod
    def newsletter_search(cls, query: str, limit: int = 20) -> str:
        """
        Search for newsletters in the WhatsApp Channel directory.

        Args:
            query: Search term (e.g. 'technology', 'news').
            limit: Max results to return.
        """
        safe_q = json.dumps(query)
        return f"wpp.newsletter.search({safe_q}, {{ limit: {limit} }})"

    @classmethod
    def newsletter_follow(cls, newsletter_id: str) -> str:
        """
        Follow / subscribe to a newsletter channel.

        Args:
            newsletter_id: The @newsletter JID e.g. '120363xxxxx@newsletter'.
        """
        return f"wpp.newsletter.follow('{newsletter_id}')"

    @classmethod
    def newsletter_unfollow(cls, newsletter_id: str) -> str:
        """
        Unfollow / unsubscribe from a newsletter channel.

        Args:
            newsletter_id: The @newsletter JID e.g. '120363xxxxx@newsletter'.
        """
        return f"wpp.newsletter.unfollow('{newsletter_id}')"

    @classmethod
    def newsletter_mute(cls, newsletter_id: str) -> str:
        """Mute notifications for a newsletter."""
        return f"wpp.newsletter.mute('{newsletter_id}')"

    @classmethod
    def newsletter_unmute(cls, newsletter_id: str) -> str:
        """Unmute notifications for a newsletter."""
        # unmute reuses unfollow then re-follow — WPP exposes it via mute toggle
        return f"wpp.newsletter.mute('{newsletter_id}', false)"

    # ─────────────────────────────────────────────
    # 5. EVENT LISTENER SETUP — THE PUSH PIPELINE
    # ─────────────────────────────────────────────

    @classmethod
    def setup_new_message_listener(cls, python_alias: str) -> str:
        """
        Sets up the zero-poll message push bridge.
        Binds WPP's `chat.new_message` event to the Playwright-exposed Python callback.
        Sends the full raw MsgModel dump — no fields filtered out.
        """
        return f"""(() => {{
            const wpp = window.__react_devtools_hook;
            if (!wpp || window._camou_has_listener) return false;

            wpp.on('chat.new_message', async (msg) => {{
                const attrs = msg.attributes || msg;

                // Full raw dump — same as get_messages()
                const dump = {{}};
                for (let key in attrs) {{
                    const val = attrs[key];
                    if (typeof val === 'string' || typeof val === 'number' || typeof val === 'boolean') {{
                        dump[key] = val;
                    }}
                }}
                if (attrs.id)     dump['id_serialized']     = attrs.id._serialized;
                if (attrs.from)   dump['from_serialized']   = attrs.from._serialized ?? attrs.from;
                if (attrs.to)     dump['to_serialized']     = attrs.to._serialized   ?? attrs.to;
                if (attrs.author) dump['author_serialized'] = attrs.author._serialized ?? null;
                if (attrs.quotedMsg?.id) dump['quotedMsgId'] = attrs.quotedMsg.id._serialized;

                window.{python_alias}(dump);
            }});

            window._camou_has_listener = true;
            return true;
        }})()"""

    # ═══════════════════════════════════════════════════════════
    # READ-LEVEL — DATA & INTROSPECTION
    # ═══════════════════════════════════════════════════════════

    # ─────────────────────────────────────────────
    # 7. CONN — Session & Device Info (READ)
    # ─────────────────────────────────────────────

    @classmethod
    def conn_get_my_user_id(cls) -> str:
        """Your own phone number @c.us ID string."""
        return "Promise.resolve(wpp.conn.getMyUserId()?._serialized ?? wpp.conn.getMyUserId())"

    @classmethod
    def conn_get_my_user_lid(cls) -> str:
        """Your device LID @lid string."""
        return "Promise.resolve(wpp.conn.getMyUserLid()?._serialized ?? wpp.conn.getMyUserLid())"

    @classmethod
    def conn_get_my_user_wid(cls) -> str:
        """Full Wid object for your own account (serialized)."""
        return "Promise.resolve(wpp.conn.getMyUserWid()?._serialized ?? null)"

    @classmethod
    def conn_get_my_device_id(cls) -> str:
        """Current linked device integer ID."""
        return "wpp.conn.getMyDeviceId()"

    @classmethod
    def conn_is_online(cls) -> str:
        """Whether the session is currently connected."""
        return "wpp.conn.isOnline()"

    @classmethod
    def conn_is_multi_device(cls) -> str:
        """Whether multi-device mode is active."""
        return "wpp.conn.isMultiDevice()"

    @classmethod
    def conn_is_idle(cls) -> str:
        """Whether the session is currently idle."""
        return "wpp.conn.isIdle()"

    @classmethod
    def conn_is_main_ready(cls) -> str:
        """Whether WhatsApp Web has fully loaded and is ready."""
        return "wpp.conn.isMainReady()"

    @classmethod
    def conn_get_platform(cls) -> str:
        """Platform string e.g. 'web', 'smbi', 'smba'."""
        return "Promise.resolve(wpp.conn.getPlatform())"

    @classmethod
    def conn_get_theme(cls) -> str:
        """Current UI theme — 'default' (light) or 'dark'."""
        return "wpp.conn.getTheme()"

    @classmethod
    def conn_get_stream_data(cls) -> str:
        """Raw WebSocket connection stream metadata."""
        return "wpp.conn.getStreamData()"

    @classmethod
    def conn_get_build_constants(cls) -> str:
        """WhatsApp Web version, build hash, and release channel metadata."""
        return "wpp.conn.getBuildConstants()"

    @classmethod
    def conn_get_ab_props(cls) -> str:
        """Active A/B test feature flags for this session."""
        return "wpp.conn.getABProps()"

    @classmethod
    def conn_get_auto_download_settings(cls) -> str:
        """Current media auto-download configuration."""
        return "wpp.conn.getAutoDownloadSettings()"

    @classmethod
    def conn_get_history_sync_progress(cls) -> str:
        """History sync progress when linking a new device."""
        return "wpp.conn.getHistorySyncProgress()"

    @classmethod
    def conn_needs_update(cls) -> str:
        """Whether WhatsApp Web requires an update to continue."""
        return "wpp.conn.needsUpdate()"

    # ─────────────────────────────────────────────
    # 8. CONTACT (READ)
    # ─────────────────────────────────────────────

    @classmethod
    def contact_get(cls, contact_id: str) -> str:
        """Full raw contact model from ContactStore."""
        return f"""
            Promise.resolve((() => {{
                const c = wpp.contact.get('{contact_id}');
                if (!c) return null;
                const dump = {{}};
                for (let key in c) {{
                    const val = c[key];
                    if (typeof val === 'string' || typeof val === 'number' || typeof val === 'boolean') {{
                        dump[key] = val;
                    }}
                }}
                if (c.id) dump['id_serialized'] = c.id._serialized;
                return dump;
            }})())
        """

    @classmethod
    def contact_list(cls, count: int = 20) -> str:
        """Contacts in your address book. Limited to `count` to avoid JS timeout on large books."""
        return f"""
            (async () => {{
                const all = await wpp.contact.list();
                return all.slice(0, {count}).map(c => {{
                    const dump = {{}};
                    for (let key in c) {{
                        const val = c[key];
                        if (typeof val === 'string' || typeof val === 'number' || typeof val === 'boolean') {{
                            dump[key] = val;
                        }}
                    }}
                    if (c.id) dump['id_serialized'] = c.id._serialized;
                    return dump;
                }});
            }})()
        """

    @classmethod
    def contact_query_exists(cls, contact_id: str) -> str:
        """Check if a phone number has a WhatsApp account."""
        return f"wpp.contact.queryExists('{contact_id}')"

    @classmethod
    def contact_get_profile_picture_url(cls, contact_id: str) -> str:
        """Get a contact's current profile picture URL."""
        return f"wpp.contact.getProfilePictureUrl('{contact_id}')"

    @classmethod
    def contact_get_status(cls, contact_id: str) -> str:
        """Get a contact's About/Status text."""
        return f"wpp.contact.getStatus('{contact_id}')"

    @classmethod
    def contact_get_business_profile(cls, contact_id: str) -> str:
        """Get the WhatsApp Business profile data for a contact."""
        return f"wpp.contact.getBusinessProfile('{contact_id}')"

    @classmethod
    def contact_get_common_groups(cls, contact_id: str) -> str:
        """List of groups shared between you and a contact."""
        return f"wpp.contact.getCommonGroups('{contact_id}')"

    # ─────────────────────────────────────────────
    # 9. GROUP (READ)
    # ─────────────────────────────────────────────

    @classmethod
    def group_get_all(cls) -> str:
        """All group chats in ChatStore as raw dumps."""
        return """
            wpp.group.getAllGroups().then(groups =>
                groups.map(g => {
                    const dump = {};
                    for (let key in g) {
                        const val = g[key];
                        if (typeof val === 'string' || typeof val === 'number' || typeof val === 'boolean') {
                            dump[key] = val;
                        }
                    }
                    if (g.id) dump['id_serialized'] = g.id._serialized;
                    return dump;
                })
            )
        """

    @classmethod
    def group_get_participants(cls, group_id: str) -> str:
        """Full participant list of a group."""
        return f"wpp.group.getParticipants('{group_id}')"

    @classmethod
    def group_get_invite_code(cls, group_id: str) -> str:
        """Get the invite link code for a group."""
        return f"wpp.group.getInviteCode('{group_id}')"

    @classmethod
    def group_get_info_from_invite_code(cls, invite_code: str) -> str:
        """Preview group metadata before joining via invite link."""
        return f"wpp.group.getGroupInfoFromInviteCode('{invite_code}')"

    @classmethod
    def group_get_membership_requests(cls, group_id: str) -> str:
        """Pending join requests for a group."""
        return f"wpp.group.getMembershipRequests('{group_id}')"

    @classmethod
    def group_get_past_participants(cls, group_id: str) -> str:
        """Members who have left or been removed from the group."""
        return f"wpp.group.getPastParticipants('{group_id}')"

    @classmethod
    def group_i_am_admin(cls, group_id: str) -> str:
        """Check if you are an admin in this group."""
        return f"wpp.group.iAmAdmin('{group_id}')"

    @classmethod
    def group_i_am_super_admin(cls, group_id: str) -> str:
        """Check if you are the super-admin (creator) of this group."""
        return f"wpp.group.iAmSuperAdmin('{group_id}')"

    @classmethod
    def group_get_size_limit(cls) -> str:
        """Maximum participants allowed in a group."""
        return "Promise.resolve(wpp.group.getGroupSizeLimit())"

    # ─────────────────────────────────────────────
    # 10. BLOCKLIST (READ)
    # ─────────────────────────────────────────────

    @classmethod
    def blocklist_all(cls) -> str:
        """All blocked contacts as raw dumps."""
        return """
            Promise.resolve((() => {
                const contacts = Array.from(wpp.blocklist.all() || []);
                return contacts.map(c => {
                    const dump = {};
                    for (let key in c) {
                        const val = c[key];
                        if (typeof val === 'string' || typeof val === 'number' || typeof val === 'boolean') {
                            dump[key] = val;
                        }
                    }
                    if (c.id) dump['id_serialized'] = c.id._serialized;
                    return dump;
                });
            })())
        """

    @classmethod
    def blocklist_is_blocked(cls, contact_id: str) -> str:
        """Check if a specific contact is blocked."""
        return f"wpp.blocklist.isBlocked('{contact_id}')"

    # ─────────────────────────────────────────────
    # 11. STATUS / STORIES (READ)
    # ─────────────────────────────────────────────

    @classmethod
    def status_get(cls, contact_id: str) -> str:
        """Get a contact's WhatsApp Status (Story) entries. Returns empty list if none or blocked."""
        return f"""
            Promise.race([
                wpp.status.get('{contact_id}'),
                new Promise(resolve => setTimeout(() => resolve([]), 3000))
            ])
        """

    @classmethod
    def status_get_mine(cls) -> str:
        """Get your own active Status stories."""
        return """
            Promise.race([
                wpp.status.getMyStatus(),
                new Promise(resolve => setTimeout(() => resolve([]), 3000))
            ])
        """

    # ─────────────────────────────────────────────
    # 12. PROFILE (READ)
    # ─────────────────────────────────────────────

    @classmethod
    def profile_get_my_name(cls) -> str:
        """Your own WhatsApp display name."""
        return "wpp.profile.getMyProfileName()"

    @classmethod
    def profile_get_my_status(cls) -> str:
        """Your own About text."""
        return "wpp.profile.getMyStatus()"

    @classmethod
    def profile_get_my_picture(cls) -> str:
        """Your own profile picture URL."""
        return "wpp.profile.getMyProfilePicture()"

    @classmethod
    def profile_is_business(cls) -> str:
        """Whether this is a WhatsApp Business account."""
        return "Promise.resolve(wpp.profile.isBusiness())"

    # ─────────────────────────────────────────────
    # 13. PRIVACY (READ)
    # ─────────────────────────────────────────────

    @classmethod
    def privacy_get(cls) -> str:
        """Read all privacy settings as a raw object."""
        return "wpp.privacy.get()"

    # ─────────────────────────────────────────────
    # 14. LABELS (READ) — Business accounts only
    # ─────────────────────────────────────────────

    @classmethod
    def labels_get_all(cls) -> str:
        """All saved chat labels."""
        return "wpp.labels.getAllLabels()"

    @classmethod
    def labels_get_by_id(cls, label_id: str) -> str:
        """Get a specific label by its ID."""
        return f"wpp.labels.getLabelById('{label_id}')"

    # ─────────────────────────────────────────────
    # 15. COMMUNITY (READ)
    # ─────────────────────────────────────────────

    @classmethod
    def community_get_subgroups(cls, community_id: str) -> str:
        """Child group chats of a Community."""
        return f"wpp.community.getSubgroups('{community_id}')"

    @classmethod
    def community_get_participants(cls, community_id: str) -> str:
        """All members across a Community."""
        return f"wpp.community.getParticipants('{community_id}')"

    @classmethod
    def community_get_announcement_group(cls, community_id: str) -> str:
        """The admin broadcast/announcement group of a Community."""
        return f"wpp.community.getAnnouncementGroup('{community_id}')"

    # ═══════════════════════════════════════════════════════════
    # ACTION-LEVEL — MUTATIONS & INTERACTIONS (OPTIONAL / TIER 3)
    # ═══════════════════════════════════════════════════════════

    # ─────────────────────────────────────────────
    # CONN (ACTIONS)
    # ─────────────────────────────────────────────

    @classmethod
    def conn_logout(cls) -> str:
        """Terminate the WhatsApp session."""
        return "wpp.conn.logout()"

    @classmethod
    def conn_mark_available(cls) -> str:
        """Appear as online/available."""
        return "wpp.conn.markAvailable()"

    @classmethod
    def conn_set_keep_alive(cls, enabled: bool = True) -> str:
        """Prevent the session from going idle."""
        val = "true" if enabled else "false"
        return f"wpp.conn.setKeepAlive({val})"

    @classmethod
    def conn_refresh_qr(cls) -> str:
        """Force a fresh QR code."""
        return "wpp.conn.refreshQR()"

    @classmethod
    def conn_set_theme(cls, theme: str) -> str:
        """Set UI theme. Values: 'default' | 'dark'."""
        return f"wpp.conn.setTheme('{theme}')"

    # ─────────────────────────────────────────────
    # CONTACT (ACTIONS)
    # ─────────────────────────────────────────────

    @classmethod
    def contact_subscribe_presence(cls, contact_id: str) -> str:
        """Start receiving presence events for a contact."""
        return f"wpp.contact.subscribePresence('{contact_id}')"

    @classmethod
    def contact_unsubscribe_presence(cls, contact_id: str) -> str:
        """Stop receiving presence events for a contact."""
        return f"wpp.contact.unsubscribePresence('{contact_id}')"

    @classmethod
    def contact_save(cls, contact_id: str, name: str) -> str:
        """Save or update a contact's display name."""
        safe_name = json.dumps(name)
        return f"wpp.contact.save('{contact_id}', {safe_name})"

    @classmethod
    def contact_remove(cls, contact_id: str) -> str:
        """Delete a contact from your address book."""
        return f"wpp.contact.remove('{contact_id}')"

    @classmethod
    def contact_report(cls, contact_id: str) -> str:
        """Report a contact to Meta."""
        return f"wpp.contact.reportContact('{contact_id}')"

    # ─────────────────────────────────────────────
    # GROUP (ACTIONS)
    # ─────────────────────────────────────────────

    @classmethod
    def group_create(cls, name: str, participants: list) -> str:
        """Create a new group chat."""
        safe_name = json.dumps(name)
        safe_parts = json.dumps(participants)
        return f"wpp.group.create({safe_name}, {safe_parts})"

    @classmethod
    def group_add_participants(cls, group_id: str, participants: list) -> str:
        """Add members to a group."""
        safe_parts = json.dumps(participants)
        return f"wpp.group.addParticipants('{group_id}', {safe_parts})"

    @classmethod
    def group_remove_participants(cls, group_id: str, participants: list) -> str:
        """Remove members from a group."""
        safe_parts = json.dumps(participants)
        return f"wpp.group.removeParticipants('{group_id}', {safe_parts})"

    @classmethod
    def group_promote_participants(cls, group_id: str, participants: list) -> str:
        """Promote members to admin."""
        safe_parts = json.dumps(participants)
        return f"wpp.group.promoteParticipants('{group_id}', {safe_parts})"

    @classmethod
    def group_demote_participants(cls, group_id: str, participants: list) -> str:
        """Remove admin from members."""
        safe_parts = json.dumps(participants)
        return f"wpp.group.demoteParticipants('{group_id}', {safe_parts})"

    @classmethod
    def group_leave(cls, group_id: str) -> str:
        """Leave a group chat."""
        return f"wpp.group.leave('{group_id}')"

    @classmethod
    def group_join(cls, invite_code: str) -> str:
        """Join a group via invite link code."""
        return f"wpp.group.join('{invite_code}')"

    @classmethod
    def group_set_subject(cls, group_id: str, name: str) -> str:
        """Rename a group."""
        safe_name = json.dumps(name)
        return f"wpp.group.setSubject('{group_id}', {safe_name})"

    @classmethod
    def group_set_description(cls, group_id: str, text: str) -> str:
        """Set the group description."""
        safe_text = json.dumps(text)
        return f"wpp.group.setDescription('{group_id}', {safe_text})"

    @classmethod
    def group_revoke_invite_code(cls, group_id: str) -> str:
        """Revoke the current invite link."""
        return f"wpp.group.revokeInviteCode('{group_id}')"

    @classmethod
    def group_approve_membership(cls, group_id: str, participants: list) -> str:
        """Approve pending join requests."""
        safe_parts = json.dumps(participants)
        return f"wpp.group.approve('{group_id}', {safe_parts})"

    @classmethod
    def group_reject_membership(cls, group_id: str, participants: list) -> str:
        """Reject pending join requests."""
        safe_parts = json.dumps(participants)
        return f"wpp.group.reject('{group_id}', {safe_parts})"

    # ─────────────────────────────────────────────
    # BLOCKLIST (ACTIONS)
    # ─────────────────────────────────────────────

    @classmethod
    def blocklist_block(cls, contact_id: str) -> str:
        """Block a contact."""
        return f"wpp.blocklist.blockContact('{contact_id}')"

    @classmethod
    def blocklist_unblock(cls, contact_id: str) -> str:
        """Unblock a contact."""
        return f"wpp.blocklist.unblockContact('{contact_id}')"

    # ─────────────────────────────────────────────
    # STATUS (ACTIONS)
    # ─────────────────────────────────────────────

    @classmethod
    def status_send_text(cls, text: str, bg_color: str | None = None) -> str:
        """Post a text Status story. bg_color is optional hex color."""
        safe_text = json.dumps(text)
        opts = json.dumps({"backgroundColor": bg_color} if bg_color else {})
        return f"wpp.status.sendTextStatus({safe_text}, {opts})"

    @classmethod
    def status_send_read(cls, msg_id: str) -> str:
        """Mark a Status story as viewed."""
        return f"wpp.status.sendReadStatus('{msg_id}')"

    @classmethod
    def status_remove(cls, msg_id: str) -> str:
        """Delete one of your own Status stories."""
        return f"wpp.status.remove('{msg_id}')"

    # ─────────────────────────────────────────────
    # PROFILE (ACTIONS)
    # ─────────────────────────────────────────────

    @classmethod
    def profile_set_my_name(cls, name: str) -> str:
        """Change your WhatsApp display name."""
        safe_name = json.dumps(name)
        return f"wpp.profile.setMyProfileName({safe_name})"

    @classmethod
    def profile_set_my_status(cls, text: str) -> str:
        """Change your About text."""
        safe_text = json.dumps(text)
        return f"wpp.profile.setMyStatus({safe_text})"

    @classmethod
    def profile_remove_my_picture(cls) -> str:
        """Remove your profile picture."""
        return "wpp.profile.removeMyProfilePicture()"

    # ─────────────────────────────────────────────
    # PRIVACY (ACTIONS)
    # ─────────────────────────────────────────────

    @classmethod
    def privacy_set_last_seen(cls, value: str) -> str:
        """Who can see Last Seen. Values: 'all'|'contacts'|'contact_blacklist'|'none'."""
        return f"wpp.privacy.setLastSeen('{value}')"

    @classmethod
    def privacy_set_online(cls, value: str) -> str:
        """Who can see Online status. Values: 'all'|'match_last_seen'."""
        return f"wpp.privacy.setOnline('{value}')"

    @classmethod
    def privacy_set_profile_pic(cls, value: str) -> str:
        """Who can see your profile picture."""
        return f"wpp.privacy.setProfilePic('{value}')"

    @classmethod
    def privacy_set_read_receipts(cls, value: str) -> str:
        """Enable/disable blue ticks. Values: 'all'|'none'."""
        return f"wpp.privacy.setReadReceipts('{value}')"

    @classmethod
    def privacy_set_add_group(cls, value: str) -> str:
        """Who can add you to groups."""
        return f"wpp.privacy.setAddGroup('{value}')"

    @classmethod
    def privacy_set_status(cls, value: str) -> str:
        """Who can see your Status stories."""
        return f"wpp.privacy.setStatus('{value}')"

    # ─────────────────────────────────────────────
    # LABELS (ACTIONS) — Business accounts only
    # ─────────────────────────────────────────────

    @classmethod
    def labels_add_new(cls, name: str, color: int | None = None) -> str:
        """Create a new label."""
        safe_name = json.dumps(name)
        opts = json.dumps({"color": color} if color is not None else {})
        return f"wpp.labels.addNewLabel({safe_name}, {opts})"

    @classmethod
    def labels_delete(cls, label_id: str) -> str:
        """Delete a label."""
        return f"wpp.labels.deleteLabel('{label_id}')"

    @classmethod
    def labels_apply(cls, chat_id: str, label_ids: list) -> str:
        """Apply labels to a chat."""
        safe_ids = json.dumps(label_ids)
        return f"wpp.labels.addOrRemoveLabels('{chat_id}', {safe_ids})"

    # ─────────────────────────────────────────────
    # CALL (ACTIONS)
    # ─────────────────────────────────────────────

    @classmethod
    def call_offer(cls, contact_id: str, is_video: bool = False) -> str:
        """Initiate a voice or video call."""
        opts = json.dumps({"isVideo": is_video})
        return f"wpp.call.offer('{contact_id}', {opts})"

    @classmethod
    def call_accept(cls, call_id: str) -> str:
        """Accept an incoming call."""
        return f"wpp.call.accept('{call_id}')"

    @classmethod
    def call_reject(cls, call_id: str) -> str:
        """Reject an incoming call."""
        return f"wpp.call.reject('{call_id}')"

    @classmethod
    def call_end(cls, call_id: str) -> str:
        """End an active call."""
        return f"wpp.call.end('{call_id}')"

    # ─────────────────────────────────────────────
    # COMMUNITY (ACTIONS)
    # ─────────────────────────────────────────────

    @classmethod
    def community_create(cls, name: str, group_ids: list) -> str:
        """Create a new Community with existing groups."""
        safe_name = json.dumps(name)
        safe_ids = json.dumps(group_ids)
        return f"wpp.community.create({safe_name}, {safe_ids})"

    @classmethod
    def community_deactivate(cls, community_id: str) -> str:
        """Deactivate / close a Community."""
        return f"wpp.community.deactivate('{community_id}')"

    @classmethod
    def community_add_subgroups(cls, community_id: str, group_ids: list) -> str:
        """Add groups to an existing Community."""
        safe_ids = json.dumps(group_ids)
        return f"wpp.community.addSubgroups('{community_id}', {safe_ids})"

    @classmethod
    def community_remove_subgroups(cls, community_id: str, group_ids: list) -> str:
        """Remove groups from a Community."""
        safe_ids = json.dumps(group_ids)
        return f"wpp.community.removeSubgroups('{community_id}', {safe_ids})"

    # ─────────────────────────────────────────────
    # MEDIA DECRYPTION
    # ─────────────────────────────────────────────

    @classmethod
    def decrypt_media(cls, direct_path: str, media_key_b64: str, media_type: str) -> str:
        """
        Decrypt a WhatsApp media blob from the browser Cache api using the embedded mediaKey.
        Type: RAM (Cache api) — Zero network cost if WA has already pre-downloaded the blob.

        How it works:
            1. Looks up the encrypted blob in WA's internal Cache api by CDN URL.
            2. Derives IV + cipherKey via HKDF-SHA256 (WhatsApp media key spec).
            3. Decrypts via AES-256-CBC, strips the trailing 10-byte MAC.
            4. Returns the raw decrypted bytes as base64 for Python transfer.

        Args:
            direct_path:   msg['directPath']  — e.g. "/v/t62.7117-24/..."
            media_key_b64: msg['mediaKey']    — base64-encoded 32-byte AES root key
            media_type:    msg['type']        — 'image'|'video'|'audio'|'ptt'|'document'|'sticker'

        Returns:
            base64 string of decrypted media bytes, or null if not yet cached.

        Raw MsgModel fields needed:
            directPath, mediaKey, type, mimetype, encFilehash, filehash
        """
        safe_path = json.dumps(direct_path)
        safe_key = json.dumps(media_key_b64)
        safe_type = json.dumps(media_type)
        return f"""
            (async () => {{
                try {{
                    // 1. Locate the encrypted blob in WA's Cache api
                    const cdnUrl = 'https://mmg.whatsapp.net' + {safe_path};
                    const cacheNames = await caches.keys();
                    let encBytes = null;
                    for (const name of cacheNames) {{
                        const c = await caches.open(name);
                        const resp = await c.match(cdnUrl);
                        if (resp) {{
                            encBytes = new Uint8Array(await resp.arrayBuffer());
                            break;
                        }}
                    }}
                    if (!encBytes) return null; // Not yet cached — trigger fallback in Python

                    // 2. HKDF-SHA256 key derivation (WhatsApp media encryption spec)
                    const infoMap = {{
                        'image':    'WhatsApp Image Keys',
                        'video':    'WhatsApp Video Keys',
                        'audio':    'WhatsApp Audio Keys',
                        'ptt':      'WhatsApp Audio Keys',
                        'document': 'WhatsApp Document Keys',
                        'sticker':  'WhatsApp Image Keys'
                    }};
                    const rawKey = Uint8Array.from(atob({safe_key}), c => c.charCodeAt(0));
                    const keyMaterial = await crypto.subtle.importKey(
                        'raw', rawKey, 'HKDF', false, ['deriveBits']
                    );
                    const infoStr = infoMap[{safe_type}] || 'WhatsApp Image Keys';
                    const info    = new TextEncoder().encode(infoStr);
                    const derived = new Uint8Array(await crypto.subtle.deriveBits(
                        {{ name: 'HKDF', hash: 'SHA-256', salt: new Uint8Array(32), info }},
                        keyMaterial,
                        112 * 8  // 112 bytes total
                    ));

                    // 3. AES-256-CBC decrypt — strip last 10 bytes (truncated MAC)
                    const iv        = derived.slice(0, 16);
                    const cipherKey = derived.slice(16, 48);
                    const aesKey = await crypto.subtle.importKey(
                        'raw', cipherKey, {{ name: 'AES-CBC' }}, false, ['decrypt']
                    );
                    const decrypted = await crypto.subtle.decrypt(
                        {{ name: 'AES-CBC', iv }},
                        aesKey,
                        encBytes.slice(0, -10)
                    );

                    // 4. Encode as base64 for zero-copy Python transfer
                    const bytes  = new Uint8Array(decrypted);
                    const chunk  = 8192;
                    let b64 = '';
                    for (let i = 0; i < bytes.length; i += chunk) {{
                        b64 += String.fromCharCode(...bytes.subarray(i, i + chunk));
                    }}
                    return btoa(b64);
                }} catch(e) {{
                    return {{ error: e.toString() }};
                }}
            }})()
        """

    @classmethod
    def download_media(cls, msg_id: str) -> str:
        """
        Fallback: Download + decrypt media via wa-js's internal downloader.
        Type: NETWORK — Makes one HTTPS request to Meta's CDN. Use only when
        decrypt_media() returns null (blob not yet cached).

        Args:
            msg_id: Full serialized message ID — msg['id_serialized']

        Returns:
            base64 string of decrypted media bytes.

        Raw MsgModel fields needed:
            id_serialized
        """
        safe_id = json.dumps(msg_id)
        return f"""
            (async () => {{
                try {{
                    const blob = await wpp.chat.downloadMedia({safe_id});
                    if (!blob) return null;
                    const buf   = await blob.arrayBuffer();
                    const bytes = new Uint8Array(buf);
                    const chunk = 8192;
                    let b64 = '';
                    for (let i = 0; i < bytes.length; i += chunk) {{
                        b64 += String.fromCharCode(...bytes.subarray(i, i + chunk));
                    }}
                    return btoa(b64);
                }} catch(e) {{
                    return {{ error: e.toString() }};
                }}
            }})()
        """
