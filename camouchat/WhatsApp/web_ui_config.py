"""
Helper functions to interact with various WhatsApp Web UI components using Playwright.

Conventions:
- `page`: refers to `playwright.sync_api.Page` instance.
- All other elements returned are of the type `Locator`.
- Utility functions are written to extract attributes or recognize content like images, videos, or quoted messages.
"""

import re
from logging import Logger, LoggerAdapter
from typing import Union, Optional

from playwright.async_api import ElementHandle, Locator, Page

from camouchat.Interfaces.web_ui_selector import WebUISelectorCapable


class WebSelectorConfig(WebUISelectorCapable):
    """Generic Custom Class , Different from every Platform"""

    def __init__(self, page: Page, log: Optional[Union[Logger, LoggerAdapter]] = None) -> None:
        super().__init__(page=page, log=log)
        if self.page is None:
            raise ValueError("page must not be None")

    # Todo , Adding all the new Functions from Child to here.
    def chat_list(self) -> Locator:
        """Returns the chat list grid locator on the main UI."""
        return self.page.get_by_role("grid", name=re.compile("chat list", re.I))

    def message_chat_panel(self) -> Locator:
        """Gives the message container panel"""
        return self.page.locator("div[id='main']").get_by_role("application").first

    def new_chat_chat_list_panel(self) -> Locator:
        """Return the locator for the new chat on the chat list upper panel"""
        return self.page.get_by_role("button", name=re.compile("new chat", re.I)).first

    def searchBox_chatList_panel(self) -> Locator:
        """Returns the search box on the chat list panel"""
        return self.page.get_by_role("textbox", name=re.compile("search input textbox", re.I)).first

    def message_box(self) -> Locator:
        """Message Input box on the message panel"""
        return self.page.locator("footer").get_by_role("textbox").first

    def wa_icon(self) -> Locator:
        """WhatsApp icon locator"""
        return self.page.get_by_role("heading", name="WhatsApp").first

    def chat_list_filters_ALL(self) -> Locator:
        """Return the chat list filter : ALL"""
        return self.page.locator("#all-filter")

    def chat_list_filters_Unread(self) -> Locator:
        """Return the chat list filter : Unread"""
        return self.page.locator("#unread-filter")

    def chat_list_filters_favorites(self) -> Locator:
        """Return the chat list filter : Favorites"""
        return self.page.locator("#favorites-filter")

    def chat_list_filters_groups(self) -> Locator:
        """Return the chat list filter : Groups"""
        return self.page.locator("#group-filter")

    async def total_chats(self) -> int:
        """Returns the total number of chats visible in the chat list."""
        element = self.chat_list()
        attr = await element.get_attribute("aria-rowcount")
        return int(attr) if attr else 0

    def chat_items(self) -> Optional[Locator]:
        """Returns a locator for all individual chat items (buttons) in the list."""
        row_locator = self.chat_list().get_by_role("row")
        list_locator = self.chat_list().get_by_role("listitem")
        if row_locator:
            return row_locator
        elif list_locator:
            return list_locator
        return None

    @staticmethod
    async def getChat_low_Quality_Img(chat: Union[ElementHandle, Locator]) -> str:
        """Extracts the low-quality image (thumbnail) from a chat preview item."""
        if isinstance(chat, Locator):
            chat = await chat.element_handle(timeout=1001)
            if chat is None:
                return ""

        imgs = await chat.query_selector_all("img[src]")
        if imgs:
            img_el = imgs[0]
            if await img_el.is_visible():
                src = await img_el.get_attribute("src")
                return src or ""
        return ""

    @staticmethod
    async def getChatName(chat: Union[ElementHandle, Locator]) -> str:
        """Returns the primary chat name (first span[title]) or empty string."""
        if isinstance(chat, Locator):
            chat = await chat.element_handle(timeout=1001)
            if chat is None:
                return ""

        if await WebSelectorConfig.is_community(chat):
            spans = await chat.query_selector_all("span[title]")
            if len(spans) > 1:
                return await spans[1].get_attribute("title") or ""
            return ""

        span = await chat.query_selector("span[title]")
        if span:
            return await span.get_attribute("title") or ""
        return ""

    @staticmethod
    async def is_community(chat: Union[ElementHandle, Locator]) -> bool:
        """
        If this chat item has the 'default-community-refreshed' icon,
        return True.
        """
        if isinstance(chat, Locator):
            chat = await chat.element_handle(timeout=1001)
            if chat is None:
                return False

        icon = await chat.query_selector("span[data-icon='default-community-refreshed']")
        if icon and await icon.is_visible():
            return True
        return False

    def Profile_header(self) -> Locator:
        """
        Returns the profile header button locator used to open contact details.
        Used when a chat is opened and the top bar includes profile/name/media access.
        """
        return self.page.locator("header").get_by_role(
            "button", name=re.compile("profile details", re.I)
        )

    def qr_canvas(self) -> Locator:
        """Returns the QR canvas image for login."""
        return self.page.get_by_role("img", name=re.compile(r"scan.*qr", re.I))

    def link_phone_number_button(self) -> Locator:
        """Returns the locator for 'Link with phone number' button."""
        return self.page.get_by_role("button", name=re.compile(r"log.*in.*phone number", re.I))

    def country_selector_button(self) -> Locator:
        """Returns the locator for country selection dropdown (chevron icon)."""
        return self.page.locator("button:has(span[data-icon='chevron'])")

    def country_list_items(self) -> Locator:
        """Returns the locator for country items in the list."""
        return self.page.get_by_role("listitem").locator("button")

    def phone_number_input(self) -> Locator:
        """Returns the locator for phone number input field."""
        return self.page.locator("form >> input")

    def link_code_container(self) -> Locator:
        """Returns the locator for the link code display."""
        return self.page.locator("div[data-link-code]")

    # -------------------- Sidebar Navigation -------------------- #

    def _side_Bar_chats(self) -> Locator:
        """Returns the sidebar button locator for 'Chats'."""
        return self.page.locator("header").first.get_by_role(
            "button", name=re.compile("chats", re.I)
        )

    def _side_Bar_status(self) -> Locator:
        """Returns the sidebar button locator for 'Status Updates'."""
        return self.page.locator("header").first.get_by_role(
            "button", name=re.compile("updates in status", re.I)
        )

    def _side_Bar_channels(self) -> Locator:
        """Returns the sidebar button locator for 'Channels'."""
        return self.page.locator("header").first.get_by_role(
            "button", name=re.compile("channels", re.I)
        )

    def _side_Bar_Communities(self) -> Locator:
        """Returns the sidebar button locator for 'Communities'."""
        return self.page.locator("header").first.get_by_role(
            "button", name=re.compile("communities", re.I)
        )

    # -------------------- Messages Section -------------------- #

    async def messages(self) -> Locator:
        """
        Returns a locator for all messages in the current open chat.
        Each message element has a unique `data-id` and role "row".
        """
        return self.page.locator('div[role="row"] div[data-id], div[data-id]:has(.copyable-text)')

    async def messages_incoming(self) -> Locator:
        """Filter for the personal | group chat incoming messages"""
        return self.page.locator('[role="row"] div[data-id] .message-in')

    async def messages_outgoing(self) -> Locator:
        """Filter for the personal | group chat outgoing messages"""
        return self.page.locator('[role="row"] div[data-id] .message-out')

    @staticmethod
    async def get_message_text(message_element: Union[ElementHandle, Locator]) -> str:
        """Returns the text content of a message if visible."""
        if isinstance(message_element, Locator):
            message_element = await message_element.element_handle()
            if message_element is None:
                return ""

        span = await message_element.query_selector("span[data-testid='selectable-text']")
        if not span:
            # Fallback to inner_text directly if span not found
            return await message_element.inner_text() or ""

        if await span.is_visible():
            text = await span.text_content()
            return text or ""
        return ""

    @staticmethod
    async def is_message_out(message: Union[ElementHandle, Locator]) -> bool:
        """Returns True if the message is outgoing (sent by bot)."""
        element: Union[ElementHandle, Locator, None]
        if isinstance(message, ElementHandle):
            element = await message.query_selector(".message-out")
        else:
            element = message.locator(".message-out")

        if isinstance(element, Locator):
            return await element.is_visible()
        return element is not None and await element.is_visible()

    @staticmethod
    async def get_dataID(message: Union[ElementHandle, Locator]) -> str:
        """Returns the unique data-id attribute of a message."""
        ID = await message.get_attribute("data-id")
        return ID or ""

    # -------------------- Media Send  -------------------- #
    def plus_rounded_icon(self) -> Locator:
        """
        It is a locator for the plus icon in the message box for opening menu with options like : image , videos ,documents to send
        """
        return (
            self.page.get_by_role("button")
            .locator("span[data-icon]")
            .filter(has_text=re.compile("plus-rounded", re.I))
            .first
        )

    def menu_item(self, name: str) -> Locator:
        pattern = re.compile(rf"^{re.escape(name)}", re.I)
        return self.page.get_by_role("menuitem", name=pattern)

    def document(self) -> Locator:
        return self.menu_item("document")

    def photos_videos(self) -> Locator:
        return self.menu_item("photos")

    def camera(self) -> Locator:
        return self.menu_item("camera")

    def audio(self) -> Locator:
        return self.menu_item("audio")

    def contact(self) -> Locator:
        return self.menu_item("contact")

    def poll(self) -> Locator:
        return self.menu_item("poll")

    def event(self) -> Locator:
        return self.menu_item("event")

    def new_sticker(self) -> Locator:
        return self.menu_item("new sticker")

    # -------------------- Message Type Checkers -------------------- #
    @staticmethod
    async def get_mess_pic_url(message: ElementHandle) -> str:
        """Extracts the image URL from an incoming picture message if visible."""
        img_el = await message.query_selector("img")
        if img_el:
            return await img_el.get_attribute("src") or ""
        return ""

    @staticmethod
    async def isReacted(message: Union[ElementHandle, Locator]) -> bool:
        """Check if the message is reacted or not"""
        try:
            if isinstance(message, Locator):
                message = await message.element_handle(timeout=1001)
            btn = await message.query_selector("button[aria-label*='reaction 👍']")
            return await btn.is_visible() if btn else False
        except Exception:
            return False

    async def pic_handle(self, message: ElementHandle) -> bool:
        """Checks if current message contains a picture."""
        pic = self.page.get_by_role("button", name=re.compile("open picture", re.I))
        if pic and await pic.is_visible():
            return True
        pic2 = await message.query_selector("xpath=.//img[contains(@src,'data:image/')]")
        return await pic2.is_visible() if pic2 else False

    @staticmethod
    async def isVideo(message: ElementHandle) -> bool:
        """
        Checks if current message is of type : video
        :param message: ElementHandle
        :return: bool
        """
        video = await message.query_selector(
            "xpath=.//span[@data-icon='media-play' or @data-icon='msg-video']"
        )
        return await video.is_visible() if video else False

    @staticmethod
    async def is_Voice_Message(message: ElementHandle) -> bool:
        voice = await message.query_selector(
            "xpath=.//button[contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'voice message')]"
        )
        if voice and await voice.is_visible():
            return True
        voice2 = await message.query_selector(
            "xpath=.//span[contains(translate(@data-icon,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'audio-play')]"
        )
        return await voice2.is_visible() if voice2 else False

    @staticmethod
    async def is_gif(message: ElementHandle) -> bool:
        gif_btn = await message.query_selector(
            "xpath=.//div[@role='button' and "
            "contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'play gif')]"
        )
        if gif_btn and await gif_btn.is_visible():
            return True
        gif2 = await message.query_selector(
            "xpath=.//span[contains(translate(@data-icon,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'media-gif')]"
        )
        return await gif2.is_visible() if gif2 else False

    @staticmethod
    async def is_animated_sticker(message: ElementHandle) -> bool:
        sticker = await message.query_selector(
            "xpath=.//img[contains(translate(@alt,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'animated sticker')]"
        )
        return await sticker.is_visible() if sticker else False

    @staticmethod
    async def is_plain_sticker(message: ElementHandle) -> bool:
        sticker = await message.query_selector(
            "xpath=.//img[contains(translate(@alt,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'sticker with no label')]"
        )
        return await sticker.is_visible() if sticker else False

    @staticmethod
    async def is_lottie_animation_sticker(message: ElementHandle) -> bool:
        el = await message.query_selector(
            "xpath=.//button[contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'sticker')]//img[contains(@src,'blob:')]"
        )
        return await el.is_visible() if el else False

    @staticmethod
    async def isSticker(message: ElementHandle) -> bool:
        """Returns True if any sticker type is detected using XPath."""
        return (
            await WebSelectorConfig.is_animated_sticker(message)
            or await WebSelectorConfig.is_plain_sticker(message)
            or await WebSelectorConfig.is_lottie_animation_sticker(message)
        )

    # -------------------- Quoted Message Utilities -------------------- #
    @staticmethod
    async def isQuotedText(message: ElementHandle) -> Optional[ElementHandle]:
        """
        Checks if a message is quoting another and returns the quoted-message handle.
        """
        quoted = await message.query_selector("span.quoted-mention")
        return quoted

    @staticmethod
    async def get_QuotedText_handle(message: ElementHandle) -> bool:
        """Returns True if the quoted-mention span is visible inside a quoted message."""
        quoted = await WebSelectorConfig.isQuotedText(message)
        if quoted:
            return await quoted.is_visible()
        return False

    # -- System -- #

    def startup_popup_locator(self) -> Locator:
        """Returns the startup continue popup button locator."""
        return self.page.get_by_role("button", name=re.compile("continue", re.I))

    async def popup2(self):
        """
        2nd Pop up of WhatsApp with message:
        "Your chats and calls are private"
        """
        page = self.page
        button = await page.query_selector("div[data-animate-model-popup] button:text-is('OK')")
        if button:
            try:
                if await button.is_visible():
                    await button.click()
            except Exception as e:
                self.log.error(f"[popup2] Click failed: {e}")

    # ---------------------------- Message Other Option ------------------------------ #
    """
    Options :
    --Group info 
    --select messages
    --Mute notifications
    --Disappearing messages
    --Add to favourite
    --close chat 
    --clear chat 
    --Exit group
    """

    async def group_info(self) -> Optional[ElementHandle]:
        dialog = await self.page.query_selector("div[role='dialog']")
        return await dialog.query_selector("li:has-text('group info')") if dialog else None

    async def select_messages(self) -> Optional[ElementHandle]:
        dialog = await self.page.query_selector("div[role='dialog']")
        return await dialog.query_selector("li:has-text('select messages')") if dialog else None

    async def mute_notifications(self) -> Optional[ElementHandle]:
        dialog = await self.page.query_selector("div[role='dialog']")
        return await dialog.query_selector("li:has-text('mute notifications')") if dialog else None

    async def disappearing_messages(self) -> Optional[ElementHandle]:
        dialog = await self.page.query_selector("div[role='dialog']")
        return (
            await dialog.query_selector("li:has-text('disappearing messages')") if dialog else None
        )

    async def add_to_fav(self) -> Optional[ElementHandle]:
        dialog = await self.page.query_selector("div[role='dialog']")
        return await dialog.query_selector("li:has-text('add to favourites')") if dialog else None

    async def close_chat(self) -> Optional[ElementHandle]:
        dialog = await self.page.query_selector("div[role='dialog']")
        return await dialog.query_selector("li:has-text('close chat')") if dialog else None

    async def clear_chat(self) -> Optional[ElementHandle]:
        dialog = await self.page.query_selector("div[role='dialog']")
        return await dialog.query_selector("li:has-text('clear chat')") if dialog else None
