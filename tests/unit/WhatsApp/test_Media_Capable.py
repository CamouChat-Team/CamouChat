"""
Unit tests for MediaCapable class.
Tests cover menu interaction, media attachment, and file handling.
"""

import logging
from unittest.mock import Mock, AsyncMock

import pytest
from playwright.async_api import Page, Locator, FileChooser, TimeoutError as PlaywrightTimeoutError

from src.Exceptions.whatsapp import MediaCapableError
from src.Interfaces.media_capable_interface import MediaType, FileTyped
from src.WhatsApp.media_capable import MediaCapable
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
    # expect_file_chooser returns a context manager, not an awaitable itself
    # So we use Mock, and the return value effectively is the context manager
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

    # Mock Context Manager
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value.value = mock_fc_info

    # expect_file_chooser() returns this context manager
    media_capable_instance.page.expect_file_chooser.return_value = mock_cm

    # Execution
    result = await media_capable_instance.add_media(MediaType.IMAGE, file_typed)

    # Verification
    assert result is True
    media_capable_instance.menu_clicker.assert_called_once()
    mock_fc_info.set_files.assert_called_once()


@pytest.mark.asyncio
async def test_add_media_file_not_found(media_capable_instance):
    """Test add_media raises error for invalid file path."""
    media_capable_instance.menu_clicker = AsyncMock()

    media_capable_instance._getOperational = AsyncMock(
        return_value=AsyncMock(is_visible=AsyncMock(return_value=True))
    )

    # Setup CM
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = Mock(value=Mock())
    media_capable_instance.page.expect_file_chooser.return_value = mock_cm

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
