"""
Unit tests for ReplyCapable class.
Tests cover replying to messages and message selection.
"""

import logging
from unittest.mock import Mock, AsyncMock, patch

import pytest
from playwright.async_api import Page, Locator, TimeoutError as PlaywrightTimeoutError

from camouchat.Exceptions.whatsapp import ReplyCapableError
from camouchat.WhatsApp.models.message import Message
from camouchat.WhatsApp.human_interaction_controller import HumanInteractionController
from camouchat.WhatsApp.reply_capable import ReplyCapable
from camouchat.WhatsApp.web_ui_config import WebSelectorConfig

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
    page.mouse = Mock()
    page.mouse.click = AsyncMock()
    page.evaluate = AsyncMock()
    page.wait_for_timeout = AsyncMock()
    return page


@pytest.fixture
def mock_ui_config():
    return Mock(spec=WebSelectorConfig)


@pytest.fixture
def reply_capable_instance(mock_page, mock_logger, mock_ui_config):
    return ReplyCapable(page=mock_page, log=mock_logger, ui_config=mock_ui_config)


@pytest.fixture
def mock_humanize():
    return Mock(spec=HumanInteractionController)


# ============================================================================
# TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_init_page_none(mock_logger, mock_ui_config):
    with pytest.raises(ValueError, match="page must not be None"):
        ReplyCapable(page=None, log=mock_logger, ui_config=mock_ui_config)


@pytest.mark.asyncio
async def test_reply_success(reply_capable_instance, mock_humanize, mock_ui_config):
    """Test reply successfully types and sends text."""
    # Setup Mocks
    mock_msg = Mock(spec=Message)
    mock_msg.id_serialized = "test-id"
    mock_msg.fromMe = False
    reply_capable_instance.quote_only = AsyncMock()  # Skip real click

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
    reply_capable_instance.quote_only.assert_called_once()
    mock_humanize.typing.assert_called_once()
    reply_capable_instance.page.keyboard.press.assert_called_with("Enter")


@pytest.mark.asyncio
async def test_reply_timeout(reply_capable_instance, mock_humanize):
    """Test reply raises error on timeout."""
    mock_msg = Mock(spec=Message)
    mock_msg.id_serialized = "test-id"
    reply_capable_instance.quote_only = AsyncMock(side_effect=PlaywrightTimeoutError("Timeout"))

    with pytest.raises(ReplyCapableError, match="reply timed out"):
        await reply_capable_instance.reply(message=mock_msg, humanize=mock_humanize, text="Hello")


@pytest.mark.asyncio
async def test_side_edge_click_success(reply_capable_instance, mock_page):
    """Test quote_only successfully triggers reply click."""
    mock_msg = Mock(spec=Message)
    mock_msg.id_serialized = "test-id"
    mock_msg.fromMe = False

    mock_page.evaluate.return_value = {"x": 100, "y": 200, "width": 50, "height": 30}

    await reply_capable_instance.quote_only(mock_msg)

    assert mock_page.mouse.click.called
    kwargs = mock_page.mouse.click.call_args.kwargs
    assert kwargs["click_count"] == 2
    assert kwargs["x"] == 110.0
    assert kwargs["y"] == 215.0


@pytest.mark.asyncio
async def test_side_edge_click_no_bbox(reply_capable_instance, mock_page):
    """Test quote_only raises error if bbox is None."""
    mock_msg = Mock(spec=Message)
    mock_msg.id_serialized = "test-id"
    mock_msg.fromMe = False

    mock_page.evaluate.return_value = None

    with patch("asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(ReplyCapableError, match="side_edge_click failed after"):
            await reply_capable_instance.quote_only(mock_msg)
