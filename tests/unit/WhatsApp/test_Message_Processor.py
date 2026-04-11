"""
Unit tests for MessageProcessor class.
Tests cover sorting, fetching, storage interaction, and filtering of messages.
"""

import logging
from unittest.mock import Mock, AsyncMock

import pytest
from playwright.async_api import Page, Locator

from camouchat.Exceptions import MessageListEmptyError, MessageProcessorError, WhatsAppError
from camouchat.Filter.message_filter import MessageFilter
from camouchat.Interfaces.storage_interface import StorageInterface
from camouchat.WhatsApp.dom.models.chat import Chat
from camouchat.WhatsApp.dom.models import Message
from camouchat.WhatsApp.dom.managers.chat_processor import ChatProcessor
from camouchat.WhatsApp.dom.managers.message_processor import MessageProcessor
from camouchat.WhatsApp.core.web_ui_config import WebSelectorConfig

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_logger():
    return Mock(spec=logging.Logger)


@pytest.fixture
def mock_page():
    return AsyncMock(spec=Page)


@pytest.fixture
def mock_ui_config():
    return Mock(spec=WebSelectorConfig)


@pytest.fixture
def mock_chat_processor():
    cp = Mock(spec=ChatProcessor)
    cp._click_chat = AsyncMock(return_value=True)
    return cp


@pytest.fixture
def mock_storage():
    storage = AsyncMock(spec=StorageInterface)
    storage.check_message_if_exists.return_value = False
    return storage


@pytest.fixture
def mock_filter():
    f = Mock(spec=MessageFilter)
    # Default behavior: identity function
    f.apply.side_effect = lambda msgs: msgs
    return f


@pytest.fixture
def message_processor_instance(mock_page, mock_logger, mock_ui_config, mock_chat_processor):
    return MessageProcessor(
        page=mock_page,
        log=mock_logger,
        ui_config=mock_ui_config,
        chat_processor=mock_chat_processor,
        storage_obj=None,
        filter_obj=None,
    )


# ============================================================================
# TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_init_page_none(mock_logger, mock_ui_config, mock_chat_processor):
    """Test initialization fails if page is None."""
    with pytest.raises(ValueError, match="page must not be None"):
        MessageProcessor(
            page=None,
            log=mock_logger,
            ui_config=mock_ui_config,
            chat_processor=mock_chat_processor,
            storage_obj=None,
            filter_obj=None,
        )


@pytest.mark.asyncio
async def test_sort_messages_incoming():
    """Test sorting returns only incoming messages."""
    msg1 = Mock(spec=Message)
    msg1.fromMe = False
    msg2 = Mock(spec=Message)
    msg2.fromMe = True

    result = await MessageProcessor.sort_messages([msg1, msg2], incoming=True)

    assert len(result) == 1
    assert result[0] == msg1


@pytest.mark.asyncio
async def test_sort_messages_outgoing():
    """Test sorting returns only outgoing messages."""
    msg1 = Mock(spec=Message)
    msg1.fromMe = False
    msg2 = Mock(spec=Message)
    msg2.fromMe = True

    result = await MessageProcessor.sort_messages([msg1, msg2], incoming=False)

    assert len(result) == 1
    assert result[0] == msg2


@pytest.mark.asyncio
async def test_sort_messages_empty():
    """Test sorting raises error on empty list."""
    with pytest.raises(MessageListEmptyError, match="Empty list passed"):
        await MessageProcessor.sort_messages([], incoming=True)


@pytest.mark.asyncio
async def test_get_wrapped_messages_success(message_processor_instance, mock_ui_config):
    """Test _get_wrapped_Messages extracts messages correctly."""
    # Setup mocks
    mock_chat = Mock(spec=Chat)

    # Message Locator setup
    mock_all_msgs = AsyncMock(spec=Locator)
    # Configure count() to return 1 when awaited
    mock_all_msgs.count.return_value = 1
    mock_ui_config.messages.return_value = mock_all_msgs

    # Individual Message Element
    mock_msg_ui = AsyncMock(spec=Locator)
    mock_all_msgs.nth.return_value = mock_msg_ui

    # Message properties
    mock_ui_config.get_message_text.return_value = "Hello"
    mock_ui_config.get_dataID.return_value = "msg-123"

    # Direction check (incoming)
    mock_inner_locator = AsyncMock(spec=Locator)
    mock_inner_locator.count.return_value = 0
    mock_msg_ui.locator.return_value = mock_inner_locator

    mock_ui_config.isReacted = AsyncMock(return_value=False)
    mock_ui_config.pic_handle = AsyncMock(return_value=False)

    # Execution
    msgs = await message_processor_instance._get_wrapped_Messages(chat=mock_chat, retry=1)

    # Verification
    assert len(msgs) == 1
    assert msgs[0].body == "Hello"
    assert msgs[0].id_serialized == "msg-123"
    assert msgs[0].fromMe is False


@pytest.mark.asyncio
async def test_get_wrapped_messages_exception(message_processor_instance, mock_ui_config):
    """Test _get_wrapped_Messages wraps WhatsAppError into MessageProcessorError."""
    mock_chat = Mock(spec=Chat)
    mock_ui_config.messages.side_effect = WhatsAppError("UI Error")

    with pytest.raises(MessageProcessorError, match="Failed to wrap messages"):
        await message_processor_instance._get_wrapped_Messages(chat=mock_chat, retry=1)


@pytest.mark.asyncio
async def test_fetcher_with_storage_deduplication(
    mock_page, mock_logger, mock_ui_config, mock_chat_processor, mock_storage
):
    """Test Fetcher stores only new messages."""
    processor = MessageProcessor(
        page=mock_page,
        log=mock_logger,
        ui_config=mock_ui_config,
        chat_processor=mock_chat_processor,
        storage_obj=mock_storage,
        filter_obj=None,
    )

    # Mock wrapped messages
    msg1 = Mock(spec=Message)
    msg1.id_serialized = "msg-1"
    msg2 = Mock(spec=Message)
    msg2.id_serialized = "msg-2"

    processor._get_wrapped_Messages = AsyncMock(return_value=[msg1, msg2])

    # Mock storage existence check: msg-1 exists, msg-2 is new
    mock_storage.check_message_if_exists_async.side_effect = lambda msg_id: msg_id == "msg-1"

    # Execution
    await processor.fetch_messages(chat=Mock(), retry=1)

    # Verification
    # Should only enqueue msg-2
    mock_storage.enqueue_insert.assert_called_once()
    _, kwargs = mock_storage.enqueue_insert.call_args
    assert len(kwargs["msgs"]) == 1
    assert kwargs["msgs"][0].id_serialized == "msg-2"


@pytest.mark.asyncio
async def test_fetcher_with_filter(
    mock_page, mock_logger, mock_ui_config, mock_chat_processor, mock_filter
):
    """Test Fetcher applies filter correctly."""
    processor = MessageProcessor(
        page=mock_page,
        log=mock_logger,
        ui_config=mock_ui_config,
        chat_processor=mock_chat_processor,
        storage_obj=None,
        filter_obj=mock_filter,
    )

    msg1 = Mock(spec=Message)
    msg1.id_serialized = "msg-1"
    processor._get_wrapped_Messages = AsyncMock(return_value=[msg1])

    mock_filter.apply.side_effect = None  # Clear default lambda
    mock_filter.apply.return_value = [msg1]

    # Execution
    result = await processor.fetch_messages(chat=Mock(), retry=1)

    # Verification
    assert result == [msg1]
    mock_filter.apply.assert_called_once()


@pytest.mark.asyncio
async def test_fetcher_empty_after_filter(
    mock_page, mock_logger, mock_ui_config, mock_chat_processor, mock_filter
):
    """Test Fetcher handles empty list after filtering."""
    processor = MessageProcessor(
        page=mock_page,
        log=mock_logger,
        ui_config=mock_ui_config,
        chat_processor=mock_chat_processor,
        storage_obj=None,
        filter_obj=mock_filter,
    )

    msg1 = Mock(spec=Message)
    msg1.id_serialized = "msg-1"
    processor._get_wrapped_Messages = AsyncMock(return_value=[msg1])

    mock_filter.apply.side_effect = None  # Clear default lambda
    mock_filter.apply.return_value = []  # Filter removes everything

    result = await processor.fetch_messages(chat=Mock(), retry=1)
    assert result == []


@pytest.mark.asyncio
async def test_fetcher_click_chat_failure(
    mock_page, mock_logger, mock_ui_config, mock_chat_processor
):
    """Test Fetcher raises error if click chat fails."""
    mock_chat_processor._click_chat.return_value = False  # Click fails

    processor = MessageProcessor(
        page=mock_page,
        log=mock_logger,
        ui_config=mock_ui_config,
        chat_processor=mock_chat_processor,
        storage_obj=None,
        filter_obj=None,
    )

    # Expect generic Exception from decorator
    with pytest.raises(Exception, match="Chat click failed"):
        await processor.fetch_messages(chat=Mock(), retry=1)


@pytest.mark.asyncio
async def test_get_wrapped_messages_no_data_id(
    message_processor_instance, mock_ui_config, mock_logger
):
    """Test _get_wrapped_Messages skips messages with no data ID."""
    mock_chat = Mock(spec=Chat)
    mock_all_msgs = AsyncMock(spec=Locator)
    mock_all_msgs.count.return_value = 1
    mock_ui_config.messages.return_value = mock_all_msgs

    mock_msg_ui = AsyncMock(spec=Locator)
    mock_all_msgs.nth.return_value = mock_msg_ui

    mock_ui_config.get_message_text.return_value = "Skip me"
    # data_id returns None consistently
    mock_ui_config.get_dataID.return_value = None

    msgs = await message_processor_instance._get_wrapped_Messages(chat=mock_chat, retry=1)

    # Should be empty list
    assert msgs == []
    # Log should indicate skipping
    mock_logger.debug.assert_any_call("Skipping message (missing data_id).")
