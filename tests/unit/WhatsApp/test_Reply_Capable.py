"""
Unit tests for ReplyCapable class.
Tests cover replying to messages and message selection.
"""

import logging
from unittest.mock import Mock, AsyncMock

import pytest
from playwright.async_api import Page, Locator, TimeoutError as PlaywrightTimeoutError, Position

from src.Exceptions.whatsapp import ReplyCapableError
from src.WhatsApp.DerivedTypes.Message import whatsapp_message
from src.WhatsApp.humanized_operations import HumanizedOperations
from src.WhatsApp.reply_capable import ReplyCapable
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
    page.keyboard = AsyncMock()
    return page


@pytest.fixture
def mock_ui_config():
    return Mock(spec=WebSelectorConfig)


@pytest.fixture
def reply_capable_instance(mock_page, mock_logger, mock_ui_config):
    return ReplyCapable(page=mock_page, log=mock_logger, UIConfig=mock_ui_config)


@pytest.fixture
def mock_humanize():
    return Mock(spec=HumanizedOperations)


# ============================================================================
# TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_init_page_none(mock_logger, mock_ui_config):
    with pytest.raises(ValueError, match="page must not be None"):
        ReplyCapable(page=None, log=mock_logger, UIConfig=mock_ui_config)


@pytest.mark.asyncio
async def test_reply_success(reply_capable_instance, mock_humanize, mock_ui_config):
    """Test reply successfully types and sends text."""
    # Setup Mocks
    mock_msg = Mock(spec=whatsapp_message)
    reply_capable_instance._side_edge_click = AsyncMock()  # Skip real click

    mock_input_box = AsyncMock(spec=Locator)
    mock_input_box.element_handle.return_value = AsyncMock()
    mock_input_box.click = AsyncMock()
    mock_ui_config.message_box.return_value = mock_input_box

    mock_humanize.typing = AsyncMock(return_value=True)

    # Execution
    result = await reply_capable_instance.reply(
        message=mock_msg, humanize=mock_humanize, text="Hello"
    )

    # Verification
    assert result is True
    reply_capable_instance._side_edge_click.assert_called_once()
    mock_humanize.typing.assert_called_once()
    reply_capable_instance.page.keyboard.press.assert_called_with("Enter")


@pytest.mark.asyncio
async def test_reply_timeout(reply_capable_instance, mock_humanize):
    """Test reply raises error on timeout."""
    mock_msg = Mock(spec=whatsapp_message)
    reply_capable_instance._side_edge_click = AsyncMock(
        side_effect=PlaywrightTimeoutError("Timeout")
    )

    with pytest.raises(ReplyCapableError, match="reply timed out"):
        await reply_capable_instance.reply(message=mock_msg, humanize=mock_humanize, text="Hello")


@pytest.mark.asyncio
async def test_side_edge_click_success(reply_capable_instance):
    """Test _side_edge_click successfully triggers reply click."""
    mock_msg = Mock(spec=whatsapp_message)
    mock_msg.isIncoming.return_value = True

    # Setup mock UI
    mock_msg_ui = AsyncMock(spec=Locator)
    # Ensure element_handle returns the SAME mock so subsequent calls like bounding_box work
    mock_msg_ui.element_handle.return_value = mock_msg_ui
    mock_msg.message_ui = mock_msg_ui

    # Setup Bounding Box
    mock_msg_ui.bounding_box.return_value = {"x": 100, "y": 200, "width": 50, "height": 30}

    await reply_capable_instance._side_edge_click(mock_msg)

    # Verification: It calls click(click_count=2) on the element handle
    # Arguments: position={x: 10 + width*0.2 = ?}, click_count=2
    # box width=50. incoming=True -> factor 0.2 -> rel_x = 10.
    # box height=30. rel_y = 15.

    # We assert that click was called with correct parameters
    assert mock_msg_ui.click.called
    kwargs = mock_msg_ui.click.call_args.kwargs
    assert kwargs["click_count"] == 2
    assert kwargs["position"] == Position(x=10.0, y=15.0)


@pytest.mark.asyncio
async def test_side_edge_click_no_bbox(reply_capable_instance):
    """Test _side_edge_click raises error if bbox is None."""
    mock_msg = Mock(spec=whatsapp_message)
    mock_msg_ui = AsyncMock(spec=Locator)
    mock_msg_ui.element_handle.return_value = mock_msg_ui  # Return self
    mock_msg.message_ui = mock_msg_ui

    mock_msg_ui.bounding_box.return_value = None

    with pytest.raises(ReplyCapableError, match="message bounding box not available"):
        await reply_capable_instance._side_edge_click(mock_msg)
