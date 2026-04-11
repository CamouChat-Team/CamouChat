"""
Unit tests for WebSelectorConfig class.
Tests cover locator construction and static helper methods.
"""

import re
from unittest.mock import Mock, AsyncMock

import pytest
from playwright.async_api import Page, Locator, ElementHandle

from camouchat.WhatsApp.core.web_ui_config import WebSelectorConfig

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_page():
    return AsyncMock(spec=Page)


@pytest.fixture
def mock_logger():
    import logging

    return Mock(spec=logging.Logger)


@pytest.fixture
def config_instance(mock_page, mock_logger):
    return WebSelectorConfig(page=mock_page, log=mock_logger)


# ============================================================================
# TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_init_page_none(mock_logger):
    with pytest.raises(ValueError, match="page must not be None"):
        WebSelectorConfig(page=None, log=mock_logger)


@pytest.mark.asyncio
async def test_chat_list_locator(config_instance):
    """Test chat_list return correct locator."""
    config_instance.chat_list()
    config_instance.page.get_by_role.assert_called()
    args, kwargs = config_instance.page.get_by_role.call_args
    assert args[0] == "grid"
    assert "chat list" in str(kwargs["name"].pattern)


@pytest.mark.asyncio
async def test_total_chats(config_instance):
    """Test total_chats returns integer from ari-rowcount."""
    mock_grid = AsyncMock(spec=Locator)
    mock_grid.get_attribute.return_value = "10"
    config_instance.chat_list = Mock(return_value=mock_grid)

    count = await config_instance.total_chats()
    assert count == 10


@pytest.mark.asyncio
async def test_get_message_text_selectable(config_instance):
    """Test get_message_text extracts text from span."""
    mock_element = AsyncMock(spec=ElementHandle)
    mock_span = AsyncMock(spec=ElementHandle)

    mock_element.query_selector.return_value = mock_span
    mock_span.is_visible.return_value = True
    mock_span.text_content.return_value = "Hello World"

    text = await WebSelectorConfig.get_message_text(mock_element)
    assert text == "Hello World"


@pytest.mark.asyncio
async def test_get_message_text_fallback(config_instance):
    """Test get_message_text fallback to inner_text."""
    mock_element = AsyncMock(spec=ElementHandle)
    # query_selector returns None for the span
    mock_element.query_selector.return_value = None
    mock_element.inner_text.return_value = "Fallback Text"

    text = await WebSelectorConfig.get_message_text(mock_element)

    assert text == "Fallback Text"
    mock_element.inner_text.assert_called_once()


@pytest.mark.asyncio
async def test_is_message_out_element_handle(config_instance):
    """Test is_message_out with ElementHandle."""
    mock_msg = AsyncMock(spec=ElementHandle)
    mock_out_el = AsyncMock(spec=ElementHandle)
    mock_out_el.is_visible.return_value = True
    mock_msg.query_selector.return_value = mock_out_el

    result = await WebSelectorConfig.is_message_out(mock_msg)
    assert result is True


@pytest.mark.asyncio
async def test_is_message_out_locator(config_instance):
    """Test is_message_out with Locator."""
    mock_msg = Mock(spec=Locator)
    mock_out_loc = AsyncMock(spec=Locator)
    mock_out_loc.is_visible.return_value = True
    mock_msg.locator.return_value = mock_out_loc

    result = await WebSelectorConfig.is_message_out(mock_msg)
    assert result is True


@pytest.mark.asyncio
async def test_link_phone_number_button(config_instance):
    config_instance.link_phone_number_button()
    config_instance.page.get_by_role.assert_called_with(
        "button", name=re.compile(r"log.*in.*phone number", re.I)
    )


@pytest.mark.asyncio
async def test_country_selector_button(config_instance):
    config_instance.country_selector_button()
    config_instance.page.locator.assert_called_with("button:has(span[data-icon='chevron'])")


@pytest.mark.asyncio
async def test_country_list_items(config_instance):
    mock_listitem = AsyncMock(spec=Locator)
    config_instance.page.get_by_role.return_value = mock_listitem
    config_instance.country_list_items()
    config_instance.page.get_by_role.assert_called_with("listitem")
    mock_listitem.locator.assert_called_with("button")


@pytest.mark.asyncio
async def test_phone_number_input(config_instance):
    config_instance.phone_number_input()
    config_instance.page.locator.assert_called_with("form >> input")


@pytest.mark.asyncio
async def test_link_code_container(config_instance):
    config_instance.link_code_container()
    config_instance.page.locator.assert_called_with("div[data-link-code]")
