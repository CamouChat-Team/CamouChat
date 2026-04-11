"""
Unit tests for MediaCapable class.
Tests cover menu interaction, media attachment, and file handling.
"""

import logging
from unittest.mock import Mock, AsyncMock

import pytest
from playwright.async_api import Page, Locator, FileChooser, TimeoutError as PlaywrightTimeoutError

from camouchat.Exceptions.whatsapp import MediaCapableError
from camouchat.contracts.media_capable import MediaType, FileTyped
from camouchat.WhatsApp.features.media_capable import MediaCapable
from camouchat.WhatsApp.core.web_ui_config import WebSelectorConfig

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_logger():
    return Mock(spec=logging.Logger)


@pytest.fixture
def mock_page():
    page = AsyncMock(spec=Page)
    # expect_file_chooser is NOT async itself — it returns a sync object
    # that acts as an async context manager.
    page.expect_file_chooser = Mock()
    page.keyboard = AsyncMock()
    return page


@pytest.fixture
def mock_ui_config():
    return Mock(spec=WebSelectorConfig)


@pytest.fixture
def media_capable_instance(mock_page, mock_logger, mock_ui_config):
    return MediaCapable(page=mock_page, log=mock_logger, UIConfig=mock_ui_config)


# ============================================================================
# TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_init_page_none(mock_logger, mock_ui_config):
    with pytest.raises(ValueError, match="page must not be None"):
        MediaCapable(page=None, log=mock_logger, UIConfig=mock_ui_config)


@pytest.mark.asyncio
async def test_menu_clicker_success(media_capable_instance, mock_ui_config):
    """Test menu_clicker opens the menu successfully."""
    mock_icon = AsyncMock(spec=Locator)
    mock_icon.element_handle.return_value = AsyncMock()
    mock_ui_config.plus_rounded_icon.return_value = mock_icon

    await media_capable_instance.menu_clicker()

    mock_icon.element_handle.assert_called_once()
    mock_icon.element_handle.return_value.click.assert_called_once()


@pytest.mark.asyncio
async def test_menu_clicker_timeout(media_capable_instance, mock_ui_config):
    """Test menu_clicker handles timeout and presses escape."""
    mock_icon = AsyncMock(spec=Locator)
    mock_icon.element_handle.side_effect = PlaywrightTimeoutError("Timeout")
    mock_ui_config.plus_rounded_icon.return_value = mock_icon

    with pytest.raises(MediaCapableError, match="Time out while clicking menu"):
        await media_capable_instance.menu_clicker()

    media_capable_instance.page.keyboard.press.assert_called_with("Escape", delay=0.5)


@pytest.mark.asyncio
async def test_add_media_success(media_capable_instance, mock_ui_config, tmp_path):
    """Test add_media successfully uploads a file."""
    # Create valid file
    dummy_file = tmp_path / "image.png"
    dummy_file.write_text("data")
    file_typed = FileTyped(uri=str(dummy_file), name="image.png")

    media_capable_instance.menu_clicker = AsyncMock()

    mock_target = AsyncMock(spec=Locator)
    mock_target.is_visible.return_value = True
    mock_ui_config.photos_videos.return_value = mock_target

    # Setup FileChooser mock
    mock_fc_info = Mock(spec=FileChooser)
    mock_fc_info.set_files = AsyncMock()

    # In Playwright source: `chooser = await fc.value`
    # `fc.value` is a Future-like awaitable, not a coroutine function.
    # Wrap it in a resolved Future so awaiting the attribute works.
    import asyncio as _asyncio

    async def _make_future(val):
        """Helper: return a Future already resolved with val."""
        loop = _asyncio.get_event_loop()
        fut = loop.create_future()
        fut.set_result(val)
        return fut

    class FakeFC:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        @property
        def value(self):
            loop = _asyncio.get_event_loop()
            fut = loop.create_future()
            fut.set_result(mock_fc_info)
            return fut

    media_capable_instance.page.expect_file_chooser.return_value = FakeFC()

    # Execution
    result = await media_capable_instance.add_media(MediaType.IMAGE, file_typed)

    # Verification
    assert result is True
    media_capable_instance.menu_clicker.assert_called_once()
    mock_fc_info.set_files.assert_called_once()


@pytest.mark.asyncio
async def test_add_media_file_not_found(media_capable_instance, mock_ui_config):
    """Test add_media raises error for invalid file path."""
    media_capable_instance.menu_clicker = AsyncMock()

    mock_target = AsyncMock(spec=Locator)
    mock_target.is_visible.return_value = True
    mock_ui_config.photos_videos.return_value = mock_target

    # Setup CM — value must be an awaitable attribute (Future)
    mock_fc_info2 = Mock(spec=FileChooser)
    mock_fc_info2.set_files = AsyncMock()

    import asyncio as _asyncio2

    class FakeFC2:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        @property
        def value(self):
            loop = _asyncio2.get_event_loop()
            fut = loop.create_future()
            fut.set_result(mock_fc_info2)
            return fut

    media_capable_instance.page.expect_file_chooser.return_value = FakeFC2()

    file_typed = FileTyped(uri="/invalid/path.png", name="image.png")

    with pytest.raises(MediaCapableError, match="Invalid file path"):
        await media_capable_instance.add_media(MediaType.IMAGE, file_typed)


@pytest.mark.asyncio
async def test_get_operational_locators(media_capable_instance, mock_ui_config):
    """Test _getOperational returns correct locator type."""
    # IMAGE
    await media_capable_instance._getOperational(MediaType.IMAGE)
    mock_ui_config.photos_videos.assert_called_once()
    mock_ui_config.reset_mock()

    # AUDIO
    await media_capable_instance._getOperational(MediaType.AUDIO)
    mock_ui_config.audio.assert_called_once()
    mock_ui_config.reset_mock()

    # DOCUMENT
    await media_capable_instance._getOperational(MediaType.DOCUMENT)
    mock_ui_config.document.assert_called_once()
