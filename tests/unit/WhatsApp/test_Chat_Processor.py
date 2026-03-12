"""
Unit tests for ChatProcessor class.
Tests cover initializing, fetching chats, clicking chats, and checking unread status.
"""

import logging
from unittest.mock import Mock, AsyncMock

import pytest
from playwright.async_api import (
    Page,
    Locator,
    ElementHandle,
    TimeoutError as PlaywrightTimeoutError,
)

from src.Exceptions import ChatNotFoundError, ChatClickError, ChatProcessorError, ChatUnreadError
from src.WhatsApp.DerivedTypes.Chat import whatsapp_chat
from src.WhatsApp.chat_processor import ChatProcessor
from src.WhatsApp.web_ui_config import WebSelectorConfig

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_logger():
    return Mock(spec=logging.Logger)


@pytest.fixture
def mock_page():
    page = AsyncMock(spec=Page)
    page.wait_for_timeout = AsyncMock()
    return page


@pytest.fixture
def mock_ui_config():
    return Mock(spec=WebSelectorConfig)


@pytest.fixture
def chat_processor_instance(mock_page, mock_logger, mock_ui_config):
    return ChatProcessor(page=mock_page, log=mock_logger, UIConfig=mock_ui_config)


# ============================================================================
# TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_init_page_none(mock_logger, mock_ui_config):
    """Test initialization fails if page is None."""
    with pytest.raises(ValueError, match="page must not be None"):
        ChatProcessor(page=None, log=mock_logger, UIConfig=mock_ui_config)


@pytest.mark.asyncio
async def test_fetch_chats_success(chat_processor_instance, mock_ui_config):
    """Test fetch_chats returns a list of whatsapp_chat objects."""
    # Setup mocks
    mock_locator = AsyncMock(spec=Locator)
    mock_locator.count.return_value = 2
    mock_element_0 = AsyncMock(spec=ElementHandle)
    mock_element_1 = AsyncMock(spec=ElementHandle)
    mock_locator.nth.side_effect = lambda i: [mock_element_0, mock_element_1][i]

    # Configure UIConfig
    mock_ui_config.chat_items.return_value = mock_locator
    mock_ui_config.getChatName = AsyncMock(side_effect=["Chat A", "Chat B"])

    # Execution
    chats = await chat_processor_instance.fetch_chats(limit=5, retry=1)

    # Verification
    assert len(chats) == 2
    assert chats[0].chat_name == "Chat A"
    assert chats[1].chat_name == "Chat B"
    assert isinstance(chats[0], whatsapp_chat)


@pytest.mark.asyncio
async def test_fetch_chats_empty(chat_processor_instance, mock_ui_config):
    """Test fetch_chats raises error when no chats found."""
    mock_locator = AsyncMock(spec=Locator)
    mock_locator.count.return_value = 0
    mock_ui_config.chat_items.return_value = mock_locator

    # Expect ChatProcessorError because ChatNotFoundError is caught and re-raised wrapped
    with pytest.raises(ChatProcessorError, match="Failed to extract chat"):
        await chat_processor_instance.fetch_chats(limit=5, retry=1)


@pytest.mark.asyncio
async def test_click_chat_success(chat_processor_instance):
    """Test successful chat click."""
    # Setup mock chat
    mock_chat = Mock(spec=whatsapp_chat)
    mock_ui = AsyncMock(spec=Locator)
    mock_element = AsyncMock(spec=ElementHandle)

    mock_chat.chat_ui = mock_ui
    mock_ui.element_handle.return_value = mock_element

    # For Locator check branch
    mock_chat.chat_ui = mock_ui

    # Execution
    result = await chat_processor_instance._click_chat(chat=mock_chat)

    # Verification
    assert result is True
    # Verify element_handle called for Locator
    mock_ui.element_handle.assert_called_once()
    mock_element.click.assert_called_once()


@pytest.mark.asyncio
async def test_click_chat_none(chat_processor_instance):
    """Test _click_chat raises proper error when chat is None."""
    # Expect ChatClickError because ChatNotFoundError gets wrapped
    with pytest.raises(ChatClickError, match="Error in click the given chat"):
        await chat_processor_instance._click_chat(chat=None)


@pytest.mark.asyncio
async def test_click_chat_retry_fails(chat_processor_instance):
    """Test _click_chat handles element handle failure."""
    mock_chat = Mock(spec=whatsapp_chat)
    mock_ui = AsyncMock(spec=Locator)
    # element_handle returns None
    mock_ui.element_handle.return_value = None
    mock_chat.chat_ui = mock_ui

    with pytest.raises(ChatClickError, match="Error in click the given chat"):
        await chat_processor_instance._click_chat(chat=mock_chat)


@pytest.mark.asyncio
async def test_is_unread_count(chat_processor_instance):
    """Test is_unread returns 1 when numeric badge exists."""
    mock_chat = Mock(spec=whatsapp_chat)
    mock_ui = AsyncMock(spec=Locator)
    mock_element = AsyncMock(spec=ElementHandle)

    mock_chat.chat_ui = mock_ui
    mock_ui.element_handle.return_value = mock_element

    # Mock badge chain
    mock_badge = AsyncMock(spec=ElementHandle)
    mock_span = AsyncMock(spec=ElementHandle)
    mock_span.inner_text.return_value = "5"

    mock_element.query_selector.side_effect = lambda s: mock_badge if "unread" in s else None
    mock_badge.query_selector.return_value = mock_span

    # Execution
    result = await chat_processor_instance.is_unread(chat=mock_chat)

    # Verification
    assert result == 1


@pytest.mark.asyncio
async def test_is_unread_no_badge(chat_processor_instance):
    """Test is_unread returns 0 when no badge found."""
    mock_chat = Mock(spec=whatsapp_chat)
    mock_ui = AsyncMock(spec=Locator)
    mock_element = AsyncMock(spec=ElementHandle)

    mock_chat.chat_ui = mock_ui
    mock_ui.element_handle.return_value = mock_element

    # query_selector returns None (no badge)
    mock_element.query_selector.return_value = None

    result = await chat_processor_instance.is_unread(chat=mock_chat)
    assert result == 0


@pytest.mark.asyncio
async def test_do_unread_success(chat_processor_instance, mock_page):
    """Test do_unread successfully marks chat as unread."""
    mock_chat = Mock(spec=whatsapp_chat)
    mock_ui = AsyncMock(spec=Locator)
    mock_element = AsyncMock(spec=ElementHandle)

    mock_chat.chat_ui = mock_ui
    mock_ui.element_handle.return_value = mock_element

    # Mock context menu
    mock_menu = AsyncMock(spec=ElementHandle)
    mock_unread_option = AsyncMock(spec=ElementHandle)

    mock_page.query_selector.side_effect = lambda sel: mock_menu if "application" in sel else None
    mock_menu.query_selector.side_effect = lambda sel: (
        mock_unread_option if "mark.*as.*unread" in str(sel) else None
    )

    # Execution
    result = await chat_processor_instance.do_unread(chat=mock_chat)

    # Verification
    assert result is True
    mock_element.click.assert_called_with(button="right")
    mock_unread_option.click.assert_called_once()


@pytest.mark.asyncio
async def test_do_unread_not_found(chat_processor_instance):
    """Test do_unread raises error when chat is None."""
    with pytest.raises(ChatNotFoundError, match="none passed"):
        await chat_processor_instance.do_unread(chat=None)


@pytest.mark.asyncio
async def test_do_unread_already_unread(chat_processor_instance, mock_page, mock_logger):
    """Test do_unread when chat is already unread (option not found, but 'read' is found)."""
    mock_chat = Mock(spec=whatsapp_chat)
    mock_ui = AsyncMock(spec=Locator)
    mock_element = AsyncMock(spec=ElementHandle)

    mock_chat.chat_ui = mock_ui
    mock_ui.element_handle.return_value = mock_element

    mock_menu = AsyncMock(spec=ElementHandle)
    mock_read_option = AsyncMock(spec=ElementHandle)  # "Mark as read" exists

    mock_page.query_selector.side_effect = lambda sel: mock_menu if "application" in sel else None

    # Logic: First query for "mark.*as.*unread" returns None.
    # Second query for "mark.*as.*read" returns mock_read_option.
    def menu_query_side_effect(selector):
        if "mark.*as.*unread" in str(selector):
            return None
        if "mark.*as.*read" in str(selector):
            return mock_read_option
        return None

    mock_menu.query_selector.side_effect = menu_query_side_effect

    await chat_processor_instance.do_unread(chat=mock_chat)

    mock_logger.info.assert_called_with("whatsApp chat loader / [do_unread] Chat already unread")


@pytest.mark.asyncio
async def test_do_unread_option_missing(chat_processor_instance, mock_page, mock_logger):
    """Test do_unread when neither option is found."""
    mock_chat = Mock(spec=whatsapp_chat)
    mock_ui = AsyncMock(spec=Locator)
    mock_element = AsyncMock(spec=ElementHandle)
    mock_chat.chat_ui = mock_ui
    mock_ui.element_handle.return_value = mock_element

    mock_menu = AsyncMock(spec=ElementHandle)
    mock_page.query_selector.return_value = mock_menu
    mock_menu.query_selector.return_value = None  # No options found

    await chat_processor_instance.do_unread(chat=mock_chat)

    mock_logger.info.assert_called_with(
        "whatsApp chat loader / [do_unread] Context menu option not found ❌"
    )


@pytest.mark.asyncio
async def test_do_unread_timeout(chat_processor_instance, mock_page):
    """Test do_unread raises ChatUnreadError on timeout."""
    mock_chat = Mock(spec=whatsapp_chat)
    mock_ui = AsyncMock(spec=Locator)
    mock_element = AsyncMock(spec=ElementHandle)
    mock_chat.chat_ui = mock_ui
    mock_ui.element_handle.return_value = mock_element

    mock_element.click.side_effect = PlaywrightTimeoutError("Timeout")

    with pytest.raises(ChatUnreadError, match="Timeout while checking unread badge"):
        await chat_processor_instance.do_unread(chat=mock_chat)
