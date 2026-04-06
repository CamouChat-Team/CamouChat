# WPP (wa-js) Global API Hierarchy

Token-optimized reference for `window.WPP` injected by `wa-js`.
Root object: `WPP` (exposed to `window` context after `wppconnect-wa.js` injection).

## 1. Core State & Lifecycle
- `WPP.isReady`: `boolean` - True when Webpack hijack is complete.
- `WPP.isInjected`: `boolean` - True when script is loaded.
- `WPP.config`: `Object` - Internal `wa-js` configuration.
- `WPP.webpack`: `Object` - Low-level module hunter (finds internal React chunks).

## 2. Event System
- `WPP.on(event, callback)`: Bind listener (e.g., `chat.new_message`, `conn.stream_mode_changed`).
- `WPP.off(event, callback)`: Unbind listener.

## 3. Connection (`WPP.conn`)
- `isAuthenticated()`: `boolean` - Check QR/login status.
- `logout()`: `void` - Disconnect session.
- `getMyUserId()`: `string` - Returns self `@c.us` ID.
- `getStreamData()`: `Object` - Current network/sync state.

## 4. Chat (`WPP.chat`)
- `get(chatId)`: `Object` - Full metadata for a chat (unread count, mute state).
- `sendTextMessage(chatId, text, [opts])`: `Promise<Object>` - Send a silent, API-level text.
- `sendFileMessage(chatId, file, [opts])`: `Promise<Object>` - Send media (image/video/doc).
- `getMessages(chatId, {count})`: `Array<Object>` - Retrieve recent messages from RAM.
- `deleteMessage(chatId, msgId, [opts])`: `Promise` - Delete for me/everyone.
- `markIsRead(chatId)`: `Promise` - Trigger blue ticks/read receipts.
- `canMute(chatId)` / `mute(chatId)`: `boolean` / `Promise` - Mute operations.

## 5. Contact (`WPP.contact`)
- `get(contactId)`: `Object` - Profile data (Name, pushname, profile pic URL).
- `getAllContacts()`: `Array<Object>` - List of all cached contacts.
- `isMyContact(contactId)`: `boolean` - True if saved in address book.
- `getStatus(contactId)`: `string` - Fetch the "about" text.

## 6. Group (`WPP.group`)
- `create(name, participants)`: `Promise<Object>` - Make a new group.
- `addParticipants(groupId, participants)`: `Promise` - Add users.
- `removeParticipants(groupId, participants)`: `Promise` - Kick users.
- `promoteParticipants(groupId, participants)`: `Promise` - Make admin.
- `demoteParticipants(groupId, participants)`: `Promise` - Remove admin.
- `getGroupInfoFromInviteCode(code)`: `Promise<Object>` - Resolve invite link.

## 7. Blocklist (`WPP.blocklist`)
- `blockContact(id)`: `Promise` - Block user.
- `unblockContact(id)`: `Promise` - Unblock user.
- `isBlocked(id)`: `boolean` - Check block status.

## 8. Raw Internal Stores (`WPP.whatsapp`)
Direct access to WhatsApp Web's internal React collections. Use when wrappers fail.
- `WPP.whatsapp.ChatStore`: `Collection` - All chats in active memory.
- `WPP.whatsapp.MsgStore`: `Collection` - All loaded messages.
- `WPP.whatsapp.ContactStore`: `Collection` - All loaded contacts.

## 9. Local Disk Storage (`WPP.indexdb`)
Bypasses React memory and directly queries browser's IndexedDB. Used exclusively for historically archived data without crashing React RAM.
- `getMessagesFromRowId({minRowId: number, limit: number})`: `Promise<Array>` - Fetch thousands of old messages sequentially.

## 10. Status/Stories (`WPP.status`)
- `getMyStatus()`: `Promise` - Get own stories.
- `sendTextStatus(text)`: `Promise` - Post a text story.
- `sendImageStatus(file)`: `Promise` - Post an image story.

## 11. Profile Management (`WPP.profile`)
- `setMyProfilePicture(url/file)`: `Promise` - Update avatar.
- `setMyStatus(text)`: `Promise` - Update "About" text.
- `setMyProfileName(name)`: `Promise` - Update pushname.

## 12. Voice/Video Calls (`WPP.call`)
- `acceptCall(callId)`: `Promise` - Accept incoming call.
- `rejectCall(callId)`: `Promise` - Reject incoming call.
- `endCall(callId)`: `Promise` - Hang up.

## 13. Business API (`WPP.catalog`, `WPP.order`, `WPP.labels`)
- `labels.getAllLabels()`: `Promise` - Fetch all business labels (e.g. "New Order").
- `labels.addOrRemoveLabels(chatIds, labels)`: `Promise` - Tag chats.
- `catalog.getProducts(contactId)`: `Promise` - View store products.
- `order.getOrder(orderId)`: `Promise` - Get purchase details.

## 14. Communities & Channels (`WPP.community`, `WPP.newsletter`)
- `community.getCommunityInfo()`: `Promise` - Parent group details.
- `newsletter.get()`: `Promise` - Channel details.
- `newsletter.subscribe()`: `Promise` - Join WhatsApp Channel.

## 15. Privacy (`WPP.privacy`)
- `setReadReceipts(boolean)`: `Promise` - Toggle blue ticks.
- `setLastSeen(string)`: `Promise` - Toggle last seen visibility.

## LLM Prompts / Integration Notes
- **Playwright Execution:** `await page.evaluate("() => WPP.chat.get('123@c.us')")`
- **ID Formats:** Users = `[number]@c.us`, Groups = `[number]-[timestamp]@g.us`.
- **Initialization Guard:** Always verify `await page.wait_for_function("() => window.WPP?.isReady")` before API calls.
- **Stealth / Anti-Ban Requirement (Try-Catch):** NEVER execute raw APIs via Playwright without a `try-catch` wrapper. If an execution fails and throws an uncaught JS error, WhatsApp web telemetry catches the stack trace and flags the account for botting.
  *Example (Always run something like this):*
  ```javascript
  async () => {
    try {
      const res = await WPP.chat.sendTextMessage('123@c.us', 'Hello');
      return { status: 'success', data: res };
    } catch (err) {
      return { status: 'error', message: err.toString() };
    }
  }
  ```
