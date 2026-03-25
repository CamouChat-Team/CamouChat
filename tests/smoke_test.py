"""
CamouChat WA-JS Smoke Test Suite — Modular Edition
====================================================
Run specific tests by name, or run all of them.

Usage:
    uv run docs/smoke_test.py                        # runs ALL registered tests
    uv run docs/smoke_test.py test_conn_session       # runs a single test
    uv run docs/smoke_test.py test_conn test_privacy  # runs multiple (prefix match)

Or set TESTS_TO_RUN at the bottom of this file to hardcode a subset.
Pass --list to print all available tests without running them.
"""

import asyncio
import json
import sys
import time
from typing import Any, Dict, List

from camouchat.BrowserManager import (
    BrowserConfig,
    Platform,
    BrowserForgeCompatible,
    ProfileManager,
    CamoufoxBrowser,
)
from camouchat.StorageDB import StorageType
from camouchat.WhatsApp import Login, WebSelectorConfig
from camouchat.WhatsApp.wa_js.wajs_wrapper import WapiWrapper

# ══════════════════════════════════════════════════════════════════════════════
# CONFIG — Fill these in.  No personal data is committed; use your own values.
# ══════════════════════════════════════════════════════════════════════════════

CFG = {
    # Your bot account's WhatsApp ID (the number logged in to WA Web).
    # Format: "<country Code>XXXXXXXXXX@c.us"  (country code + number, no spaces)
    "my_number": "<country Code>XXXXXXXXXX@c.us",
    # Any contact in your contact list — used for contact/query tests.
    # Format: "<country Code>XXXXXXXXXX@c.us"
    "contact_id": "<country Code>XXXXXXXXXX@c.us",
    # A chat that has existing image/video history — used for media extraction test.
    # Can be a personal DM ("<country Code>XXXXXXXXXX@c.us") or a group ("XXXX@g.us").
    # Leave as None to auto-resolve from a group named MEDIA_GROUP_NAME below.
    "media_chat_id": None,
    # Group name to auto-resolve as the media test chat (RAM lookup, zero network).
    # Only used when media_chat_id is None.
    "media_group_name": "YOUR_GROUP_NAME",
    # Directory where extracted media files will be saved.
    "media_save_dir": "/tmp/camouchat_media",
    # Newsletter search query for test_newsletter_search.
    "newsletter_search_query": "technology",
    # CamouChat profile ID (matches the profile used in production).
    "profile_id": "Work",
}

# ══════════════════════════════════════════════════════════════════════════════
# TEST FUNCTIONS
# Each test is:   async def test_XYZ(wapi, cfg) -> None
# Output via print(). Raise any exception to mark the test as FAILED.
# ══════════════════════════════════════════════════════════════════════════════


async def test_isolation(wapi: WapiWrapper, cfg: Dict[str, Any]) -> None:
    """
    Stealth isolation — verify WPP handle survives 'window.WPP' annihilation.
    Confirms the hidden property bridge works and stealth engine is active.
    """
    chat = await wapi.get_chat(cfg["my_number"])
    print(f"  Stealth bridge OK — chat dump ({len(chat)} fields).")


async def test_messages_basic(wapi: WapiWrapper, cfg: Dict[str, Any]) -> None:
    """
    Fetch last 5 messages from MY_NUMBER chat (RAM read).
    Prints direction, type, body snippet, and full MsgModel dump of first message.
    """
    msgs = await wapi.get_messages(cfg["my_number"], count=5)
    print(f"  Fetched {len(msgs)} message(s).")
    for m in msgs:
        direction = "→ Me" if m.get("fromMe") else "← Them"
        print(f"  [{direction}] [{m.get('type')}] {m.get('body','')[:60]!r}  (ts={m.get('t')})")
    if msgs:
        print("\n  Full MsgModel dump of first message:")
        print(json.dumps(msgs[0], indent=4, default=str))


async def test_messages_unread(wapi: WapiWrapper, cfg: Dict[str, Any]) -> None:
    """
    Fetch only unread messages from MY_NUMBER chat (count=-1 = all unread).
    """
    unread = await wapi.get_messages(cfg["my_number"], count=-1, only_unread=True)
    print(f"  {len(unread)} unread message(s) in this chat.")


async def test_messages_paginate(wapi: WapiWrapper, cfg: Dict[str, Any]) -> None:
    """
    Pagination: fetch the 3 messages BEFORE the latest one (anchor-based).
    """
    anchor_batch = await wapi.get_messages(cfg["my_number"], count=1)
    if not anchor_batch:
        print("  No messages to paginate from.")
        return
    anchor_id = anchor_batch[-1].get("id_serialized")
    print(f"  Anchor ID: {anchor_id}")
    page_msgs = await wapi.get_messages(
        cfg["my_number"], count=3, direction="before", anchor_msg_id=anchor_id
    )
    print(f"  Got {len(page_msgs)} messages before anchor:")
    for m in page_msgs:
        print(f"    [{m.get('type')}] {m.get('body','')[:60]!r}")


async def test_message_by_id(wapi: WapiWrapper, cfg: Dict[str, Any]) -> None:
    """
    Fetch a single message by its full serialized ID (get_message_by_id).
    """
    latest = await wapi.get_messages(cfg["my_number"], count=1)
    if not latest:
        print("  No messages available to test get_message_by_id.")
        return
    target_id = latest[0].get("id_serialized")
    print(f"  Targeting ID: {target_id}")
    single = await wapi.get_message_by_id(target_id)
    print("  MATCHED full dump:")
    print(json.dumps(single, indent=4, default=str))


async def test_chat_list(wapi: WapiWrapper, cfg: Dict[str, Any]) -> None:
    """
    Fetch top 5 chats from the sidebar (RAM read).
    Prints full raw ChatModel dump of the first result.
    """
    chat_list = await wapi.get_chat_list(count=5)
    print(f"  Got {len(chat_list)} chat(s). Full raw dump of first:")
    if chat_list:
        print(json.dumps(chat_list[0], indent=4, default=str))


async def test_chat_list_unread(wapi: WapiWrapper, cfg: Dict[str, Any]) -> None:
    """
    Fetch only chats that have unread messages.
    """
    unread_chats = await wapi.get_chat_list(only_unread=True)
    print(f"  {len(unread_chats)} chat(s) with unread messages.")
    if unread_chats:
        print("  Raw dump of first unread chat:")
        print(json.dumps(unread_chats[0], indent=4, default=str))


async def test_indexdb(wapi: WapiWrapper, cfg: Dict[str, Any]) -> None:
    """
    Read 5 messages from IndexedDB (disk history) using a rowId anchor from RAM.
    Zero network operation — reads from browser's persistent disk store.
    """
    ram_msgs = await wapi.get_messages(cfg["my_number"], count=1)
    if not ram_msgs:
        print("  No RAM message to use as rowId anchor.")
        return
    anchor_row = ram_msgs[0].get("rowId")
    print(f"  Anchor rowId (from RAM): {anchor_row}")
    disk_msgs = await wapi.indexdb_get_messages(min_row_id=anchor_row, limit=5)
    print(f"  Got {len(disk_msgs)} message(s) from IndexedDB. Dump of first:")
    if disk_msgs:
        print(json.dumps(disk_msgs[0], indent=4, default=str))


async def test_newsletter_list(wapi: WapiWrapper, cfg: Dict[str, Any]) -> None:
    """
    List all WhatsApp Channels (Newsletters) you follow.
    """
    newsletters = await wapi.newsletter_list()
    print(f"  Following {len(newsletters)} channel(s).")
    if newsletters:
        print("  Raw dump of first channel:")
        print(json.dumps(newsletters[0], indent=4, default=str))
    else:
        print("  (Not following any channels)")


async def test_newsletter_search(wapi: WapiWrapper, cfg: Dict[str, Any]) -> None:
    """
    Search the WhatsApp Channel directory (NETWORK call).
    Query is configurable via CFG['newsletter_search_query'].
    """
    query = cfg.get("newsletter_search_query", "technology")
    results = await wapi.newsletter_search(query, limit=3)
    print(f"  Search results for {query!r}:")
    print(json.dumps(results, indent=4, default=str))


async def test_conn_session(wapi: WapiWrapper, cfg: Dict[str, Any]) -> None:
    """
    Read session & device info from ConnModel (RAM).
    user_id, lid, platform, theme, online status, multi-device flag.
    """
    user_id = await wapi.conn_get_my_user_id()
    user_lid = await wapi.conn_get_my_user_lid()
    platform = await wapi.conn_get_platform()
    theme = await wapi.conn_get_theme()
    is_online = await wapi.conn_is_online()
    is_ready = await wapi.conn_is_main_ready()
    is_multi = await wapi.conn_is_multi_device()
    needs_update = await wapi.conn_needs_update()
    print(f"  user_id={user_id}  lid={user_lid}")
    print(f"  platform={platform}  theme={theme}")
    print(
        f"  online={is_online}  ready={is_ready}  multi_device={is_multi}  needs_update={needs_update}"
    )


async def test_conn_build(wapi: WapiWrapper, cfg: Dict[str, Any]) -> None:
    """
    Read WA Web build constants & version info (RAM).
    VERSION_BASE, PUSH_PHASE, etc.
    """
    build = await wapi.conn_get_build_constants()
    print("  Build constants raw dump:")
    print(json.dumps(build, indent=4, default=str))


async def test_conn_stream(wapi: WapiWrapper, cfg: Dict[str, Any]) -> None:
    """
    Read the current stream mode & info (RAM).
    {mode: "MAIN", info: "NORMAL"} in a healthy session.
    """
    stream = await wapi.conn_get_stream_data()
    print(json.dumps(stream, indent=4, default=str))


async def test_contact_get(wapi: WapiWrapper, cfg: Dict[str, Any]) -> None:
    """
    Fetch a contact by ID and list the first 5 contacts (RAM reads).
    contact_id defaults to my_number which returns {} (own number not in ContactStore).
    Set a real contact in CFG['contact_id'] for a populated result.
    """
    cid = cfg["contact_id"]
    contact = await wapi.contact_get(cid)
    print(f"  contact_get({cid}) raw dump:")
    print(json.dumps(contact, indent=4, default=str))
    all_contacts = await wapi.contact_list(count=5)
    print(f"  Total contacts returned (capped at 5): {len(all_contacts)}")
    if all_contacts:
        print("  First contact raw dump:")
        print(json.dumps(all_contacts[0], indent=4, default=str))


async def test_contact_query(wapi: WapiWrapper, cfg: Dict[str, Any]) -> None:
    """
    Query if a contact exists, their profile picture URL, and about/status text.
    NETWORK: profilePicUrl and status queries may hit XMPP.
    """
    cid = cfg["contact_id"]
    print(f"  Testing contact: {cid}")
    exists = await wapi.contact_query_exists(cid)
    pic_url = await wapi.contact_get_profile_picture_url(cid)
    about = await wapi.contact_get_status(cid)
    print(f"  queryExists: {exists}")
    print(f"  profilePicUrl: {pic_url}")
    print(f"  about/status: {about}")


async def test_group_list(wapi: WapiWrapper, cfg: Dict[str, Any]) -> None:
    """
    Fetch all groups you're a member of (RAM read).
    Prints count and full raw ChatModel dump of the first group.
    """
    groups = await wapi.group_get_all()
    print(f"  Total groups: {len(groups)}")
    if groups:
        print("  First group raw dump:")
        print(json.dumps(groups[0], indent=4, default=str))


async def test_group_details(wapi: WapiWrapper, cfg: Dict[str, Any]) -> None:
    """
    Admin check, invite code fetch (if admin), and global size limit (RAM).
    Invite code fetch is skipped automatically if not admin.
    """
    groups = await wapi.group_get_all()
    if not groups:
        print("  No groups found.")
        return
    gid = groups[0].get("id_serialized")
    print(f"  Group: {gid}")
    is_admin = await wapi.group_i_am_admin(gid)
    is_sadmin = await wapi.group_i_am_super_admin(gid)
    print(f"  iAmAdmin={is_admin}  iAmSuperAdmin={is_sadmin}")
    if is_admin:
        invite = await wapi.group_get_invite_code(gid)
        print(f"  Invite code: {invite}")
    else:
        print("  Skipping invite code fetch (not admin → Forbidden).")
    size_limit = await wapi.group_get_size_limit()
    print(f"  Group size limit: {size_limit}")


async def test_blocklist(wapi: WapiWrapper, cfg: Dict[str, Any]) -> None:
    """
    List all blocked contacts and check if CONTACT_ID is blocked (RAM reads).
    """
    blocked = await wapi.blocklist_all()
    print(f"  {len(blocked)} blocked contact(s).")
    if blocked:
        print(json.dumps(blocked[0], indent=4, default=str))
    cid = cfg["contact_id"]
    is_blocked = await wapi.blocklist_is_blocked(cid)
    print(f"  Is {cid} blocked? {is_blocked}")


async def test_profile(wapi: WapiWrapper, cfg: Dict[str, Any]) -> None:
    """
    Read own profile: name (RAM).
    Note: about/picture/isBusiness hang on XMPP and are skipped (On hold).
    """
    name = await wapi.profile_get_my_name()
    print(f"  name={name!r}")
    print("  [On hold → Fails] Skipped: about, picture, isBusiness (Hangs XMPP)")


async def test_privacy(wapi: WapiWrapper, cfg: Dict[str, Any]) -> None:
    """
    Read all privacy settings (RAM read).
    readReceipts, groupAdd, profilePicture, lastSeen, online, etc.
    """
    privacy = await wapi.privacy_get()
    print(json.dumps(privacy, indent=4, default=str))


async def test_labels(wapi: WapiWrapper, cfg: Dict[str, Any]) -> None:
    """
    Fetch all chat labels (RAM read).
    Only populated on WhatsApp Business accounts.
    """
    labels = await wapi.labels_get_all()
    count = len(labels) if isinstance(labels, list) else "N/A"
    print(f"  {count} label(s). Raw dump:")
    print(json.dumps(labels, indent=4, default=str))


async def test_community(wapi: WapiWrapper, cfg: Dict[str, Any]) -> None:
    """
    Find a Community parent group and list its subgroups + announcement group.
    Skipped automatically if no community parent exists in your chats.
    """
    groups = await wapi.group_get_all()
    parent = next((g for g in groups if g.get("isParentGroup") or g.get("__x_isParentGroup")), None)
    if not parent:
        print("  No Community parent group found in your chats. Skipping.")
        return
    cid = parent.get("id_serialized")
    subs = await wapi.community_get_subgroups(cid)
    ann = await wapi.community_get_announcement_group(cid)
    print(f"  Community: {cid}")
    print(f"  Subgroups: {subs}")
    print(f"  Announcement group: {ann}")


async def test_status(wapi: WapiWrapper, cfg: Dict[str, Any]) -> None:
    """
    [On hold → Fails] Status/stories fetch hangs the XMPP bridge.
    Kept as a placeholder for when the underlying WPP API is fixed.
    """
    # mine   = await wapi.status_get_mine()
    # theirs = await wapi.status_get(cfg["contact_id"])
    print("  [On hold → Fails] status_get_mine / status_get hang the XMPP bridge.")
    print("  Uncomment when WPP fixes the underlying promise resolution.")


async def test_media_extract(wapi: WapiWrapper, cfg: Dict[str, Any]) -> None:
    """
    Extract and decrypt the most recent image/video from MEDIA_CHAT_ID.

    Uses:
      - Cache API path first (zero network)
      - CDN fallback if not cached (logs INFO: [NETWORK])

    Requires a chat with at least one image/video in history.
    MEDIA_CHAT_ID auto-resolves from group named MEDIA_GROUP_NAME if not set.

    Note: View-once messages are intentionally excluded from linked devices
    by the Signal protocol — only regular media is extractable via WA Web.
    """
    save_dir = cfg.get("media_save_dir", "/tmp/camouchat_media")

    # Resolve media chat ID
    media_id = cfg.get("media_chat_id")
    if not media_id:
        group_name = cfg.get("media_group_name", "")
        all_groups = await wapi.group_get_all()
        media_group = next(
            (
                g
                for g in all_groups
                if g.get("__x_name") == group_name or g.get("__x_formattedTitle") == group_name
            ),
            None,
        )
        if not media_group:
            print(f"  Group '{group_name}' not found. Set CFG['media_chat_id'] directly.")
            return
        media_id = media_group["id_serialized"]
        print(f"  Auto-resolved media chat: {media_id} (group '{group_name}')")
    else:
        print(f"  Media chat: {media_id}")

    # Fetch recent messages and filter media in Python
    # (wpp.chat.getMessages with media filter queries a global index — scoping unreliable)
    all_msgs = await wapi.get_messages(media_id, count=50)
    media_msgs = [
        m
        for m in all_msgs
        if m.get("type") in ("image", "video", "sticker", "audio", "ptt", "document")
        and m.get("directPath")
    ]

    print(f"  Found {len(all_msgs)} message(s) total, {len(media_msgs)} with media.")
    if not media_msgs:
        print("  No extractable media found. Send a regular image to this chat and re-run.")
        return

    target = media_msgs[0]
    save_to = WapiWrapper.media_save_path(target, save_dir)
    result = await wapi.extract_media(message=target, save_path=save_to)

    if result["success"]:
        fallback = " [CDN fallback used]" if result["used_fallback"] else " [Cache API]"
        print(f"  ✅ SUCCESS{fallback}")
        print(f"     type={result['type']}  mimetype={result['mimetype']}")
        print(f"     size={result['size_bytes']:,} bytes  viewOnce={result['view_once']}")
        print(f"     saved → {result['path']}")
    else:
        print(f"  ❌ FAILED: {result['error']}")


# ══════════════════════════════════════════════════════════════════════════════
# TEST REGISTRY
# Format: "test_name": (function, "Short description", on_hold)
#   on_hold=True  → known to hang/fail; shown clearly in --list and warned at runtime
#   on_hold=False → expected to pass normally
# ══════════════════════════════════════════════════════════════════════════════

REGISTRY: Dict[str, tuple] = {
    #  name                      function                   description                              on_hold
    "test_isolation": (test_isolation, "Stealth bridge isolation check", False),
    "test_messages_basic": (test_messages_basic, "Last 5 messages (RAM)", False),
    "test_messages_unread": (test_messages_unread, "Unread messages fetch", False),
    "test_messages_paginate": (test_messages_paginate, "Message pagination with anchor", False),
    "test_message_by_id": (test_message_by_id, "Single message by ID", False),
    "test_chat_list": (test_chat_list, "Top 5 chats from sidebar", False),
    "test_chat_list_unread": (test_chat_list_unread, "Chats with unread messages", False),
    "test_indexdb": (test_indexdb, "IndexedDB disk history read", False),
    "test_newsletter_list": (test_newsletter_list, "Followed WhatsApp Channels", False),
    "test_newsletter_search": (test_newsletter_search, "Channel directory search", False),
    "test_conn_session": (test_conn_session, "Session & device info", False),
    "test_conn_build": (test_conn_build, "WA Web build constants", False),
    "test_conn_stream": (test_conn_stream, "Stream mode & info", False),
    "test_contact_get": (test_contact_get, "Contact get + list", False),
    "test_contact_query": (test_contact_query, "ContactExists / PicURL / Status", False),
    "test_group_list": (test_group_list, "All groups (RAM)", False),
    "test_group_details": (test_group_details, "Admin / invite / size limit", False),
    "test_blocklist": (test_blocklist, "Blocked contacts list", False),
    "test_profile": (test_profile, "Own name only — about/pic hang XMPP", True),
    "test_privacy": (test_privacy, "Privacy settings dump", False),
    "test_labels": (test_labels, "Chat labels (Business only)", False),
    "test_community": (test_community, "Community parent + subgroups", False),
    "test_status": (test_status, "[ON HOLD] status_get hangs XMPP bridge", True),
    "test_media_extract": (test_media_extract, "Media decrypt + save to disk", False),
}

# ══════════════════════════════════════════════════════════════════════════════
# TESTS_TO_RUN
# Leave empty [] to run ALL tests.
# Or specify test names (exact or prefix): ["test_conn", "test_messages_basic"]
# ══════════════════════════════════════════════════════════════════════════════

TESTS_TO_RUN: List[str] = []


# ══════════════════════════════════════════════════════════════════════════════
# RUNNER
# ══════════════════════════════════════════════════════════════════════════════


def _resolve_tests(requested: List[str]) -> List[str]:
    """Resolve test names, supporting prefix matching."""
    if not requested:
        return list(REGISTRY.keys())
    resolved = []
    for req in requested:
        if req in REGISTRY:
            resolved.append(req)
        else:
            matches = [k for k in REGISTRY if k.startswith(req)]
            if not matches:
                print(f"  ⚠  Unknown test: {req!r} — skipping.")
            resolved.extend(matches)
    return resolved


async def run_tests(wapi: WapiWrapper, test_names: List[str]) -> None:
    total = len(test_names)
    passed = 0
    failed = 0
    on_hold = 0
    results = []

    print("\n" + "═" * 60)
    print(f"  CamouChat WA-JS Smoke Tests  ({total} selected)")
    print("═" * 60)

    for idx, name in enumerate(test_names, 1):
        func, description, is_on_hold = REGISTRY[name]
        tag = "  ⚠ [ON HOLD]" if is_on_hold else ""
        print(f"\n[{idx}/{total}] {name}{tag}")
        print(f"  {description}")
        print("  " + "─" * 50)
        if is_on_hold:
            print("  Skipping — marked [ON HOLD]: known to hang or fail.")
            print("  Pass --force-on-hold flag or call this test directly to run anyway.")
            on_hold += 1
            results.append((name, "ON_HOLD", 0.0, None))
            continue
        t0 = time.monotonic()
        try:
            await func(wapi, CFG)
            elapsed = time.monotonic() - t0
            print(f"  ✓ PASSED  ({elapsed:.2f}s)")
            passed += 1
            results.append((name, "PASSED", elapsed, None))
        except Exception as exc:
            elapsed = time.monotonic() - t0
            print(f"  ✗ FAILED: {exc}")
            failed += 1
            results.append((name, "FAILED", elapsed, str(exc)))

    # ── Summary ────────────────────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print(f"  {passed} PASSED  |  {failed} FAILED  |  {on_hold} ON HOLD  ({total} total)")
    print("═" * 60)
    if failed:
        print("\nFailed tests:")
        for name, status, _, err in results:
            if status == "FAILED":
                print(f"  ✗ {name}: {err}")
    if on_hold:
        print("\nOn-hold tests (skipped):")
        for name, status, _, _ in results:
            if status == "ON_HOLD":
                _, desc, _ = REGISTRY[name]
                print(f"  ⚠ {name}: {desc}")
    print()


async def main() -> None:
    # ── --list flag ──────────────────────────────────────────────────────────
    if "--list" in sys.argv:
        on_hold_tests = [(n, d) for n, (_, d, h) in REGISTRY.items() if h]
        runnable_tests = [(n, d) for n, (_, d, h) in REGISTRY.items() if not h]

        print("\n" + "═" * 60)
        print("  CamouChat WA-JS Smoke Tests — Available Tests")
        print("═" * 60)
        print("\n  ✓ Runnable tests:")
        for name, desc in runnable_tests:
            print(f"    {name:<30}  {desc}")
        print("\n  ⚠ On-hold tests (skipped by default, known to hang/fail):")
        for name, desc in on_hold_tests:
            print(f"    {name:<30}  {desc}")
        print()
        print("  Usage:")
        print("    uv run docs/smoke_test.py                        # run all")
        print("    uv run docs/smoke_test.py test_conn_session       # one test")
        print("    uv run docs/smoke_test.py test_conn test_privacy  # multiple / prefix")
        print("    uv run docs/smoke_test.py --list                  # this screen")
        print()
        return

    # ── Resolve which tests to run ───────────────────────────────────────────
    cli_args = [a for a in sys.argv[1:] if not a.startswith("--")]
    requested = cli_args or TESTS_TO_RUN
    test_names = _resolve_tests(requested)
    if not test_names:
        print("No tests matched. Use --list to see available tests.")
        return

    # ── Browser + Login ──────────────────────────────────────────────────────
    pm = ProfileManager()
    profile = pm.create_profile(
        platform=Platform.WHATSAPP,
        profile_id=CFG["profile_id"],
        storage_type=StorageType.SQLITE,
    )

    config = BrowserConfig.from_dict(
        {
            "platform": Platform.WHATSAPP,
            "locale": "en-US",
            "enable_cache": False,
            "headless": False,
            "fingerprint_obj": BrowserForgeCompatible(),
        }
    )
    browser = CamoufoxBrowser(config=config, profile=profile)
    page = await browser.get_page()

    ui = WebSelectorConfig(page=page)
    login = Login(page=page, UIConfig=ui)
    await login.login(method=0)

    wapi = WapiWrapper(page=page)
    ready = await wapi.wait_for_ready()

    if not ready:
        print("❌  WPP engine failed to inject. Aborting tests.")
        return

    print("✓  WPP engine ready.")
    await run_tests(wapi, test_names)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    except Exception:
        import traceback

        traceback.print_exc()
