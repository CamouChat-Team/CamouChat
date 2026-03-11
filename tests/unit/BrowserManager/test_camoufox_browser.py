"""
Unit tests for CamoufoxBrowser class.
Tests browser initialization, page management, and cleanup.
"""

import logging
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

import pytest
from playwright.async_api import BrowserContext, Page

# Direct imports to avoid circular dependency
from src.BrowserManager import camoufox_browser as cb_module
from src.Exceptions import base

CamoufoxBrowser = cb_module.CamoufoxBrowser
BrowserException = base.BrowserException


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_logger():
    return Mock(spec=logging.Logger)


@pytest.fixture
def mock_browserforge():
    """Mock BrowserForgeCapable implementation."""
    # Create a mock that matches the interface
    bf = Mock()
    bf.get_fg.return_value = Mock()  # Return mock fingerprint
    return bf


@pytest.fixture
def camoufox_browser(tmp_path, mock_logger, mock_browserforge):
    """Create CamoufoxBrowser instance with required dependencies."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    fg_path = tmp_path / "fingerprint.pkl"
    fg_path.touch()

    return CamoufoxBrowser(
        cache_dir_path=cache_dir,
        fingerprint_path=fg_path,
        BrowserForge=mock_browserforge,
        log=mock_logger,
        headless=True,
    )


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================


def test_init_success(tmp_path, mock_logger, mock_browserforge):
    """Test CamoufoxBrowser initializes with all required params."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    fg_path = tmp_path / "fg.pkl"
    fg_path.touch()

    browser = CamoufoxBrowser(
        cache_dir_path=cache_dir,
        fingerprint_path=fg_path,
        BrowserForge=mock_browserforge,
        log=mock_logger,
        headless=False,
    )

    assert browser.cache_dir_path == cache_dir
    assert browser.BrowserForge == mock_browserforge
    assert browser.log == mock_logger
    assert browser.headless is False


def test_init_missing_logger(tmp_path, mock_browserforge):
    """Test CamoufoxBrowser raises error without logger."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    fg_path = tmp_path / "fg.pkl"
    fg_path.touch()

    with pytest.raises(BrowserException, match="Logger is missing"):
        CamoufoxBrowser(
            cache_dir_path=cache_dir,
            fingerprint_path=fg_path,
            BrowserForge=mock_browserforge,
            log=None,
        )


def test_init_missing_browserforge(tmp_path, mock_logger):
    """Test CamoufoxBrowser raises error without BrowserForge."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    fg_path = tmp_path / "fg.pkl"
    fg_path.touch()

    with pytest.raises(BrowserException, match="BrowserForge is missing"):
        CamoufoxBrowser(
            cache_dir_path=cache_dir, fingerprint_path=fg_path, BrowserForge=None, log=mock_logger
        )


def test_init_missing_cache_dir(tmp_path, mock_logger, mock_browserforge):
    """Test CamoufoxBrowser raises error without cache directory."""
    fg_path = tmp_path / "fg.pkl"
    fg_path.touch()

    with pytest.raises(BrowserException, match="Cache dir path is missing"):
        CamoufoxBrowser(
            cache_dir_path=None,
            fingerprint_path=fg_path,
            BrowserForge=mock_browserforge,
            log=mock_logger,
        )


def test_init_missing_fingerprint_path(tmp_path, mock_logger, mock_browserforge):
    """Test CamoufoxBrowser raises error without fingerprint path."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    with pytest.raises(BrowserException, match="Fingerprint path is missing"):
        CamoufoxBrowser(
            cache_dir_path=cache_dir,
            fingerprint_path=None,
            BrowserForge=mock_browserforge,
            log=mock_logger,
        )


# ============================================================================
# GET INSTANCE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_getInstance_creates_browser(camoufox_browser, mock_browserforge):
    """Test getInstance creates browser on first call."""
    mock_context = AsyncMock(spec=BrowserContext)
    mock_fingerprint = Mock()
    mock_browserforge.get_fg.return_value = mock_fingerprint

    # Mock AsyncCamoufox to avoid actual browser launch
    mock_camoufox = AsyncMock()
    mock_camoufox.__aenter__.return_value = mock_context

    with patch("src.BrowserManager.camoufox_browser.AsyncCamoufox", return_value=mock_camoufox):
        with patch("src.BrowserManager.camoufox_browser.launch_options", return_value={}):
            result = await camoufox_browser.get_instance()

            assert result == mock_context
            assert camoufox_browser.browser == mock_context
            mock_browserforge.get_fg.assert_called_once()


@pytest.mark.asyncio
async def test_getInstance_reuses_existing(camoufox_browser):
    """Test getInstance returns existing browser without recreating."""
    mock_context = AsyncMock(spec=BrowserContext)
    camoufox_browser.browser = mock_context

    result = await camoufox_browser.get_instance()

    assert result == mock_context


# ============================================================================
# GET BROWSER TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_GetBrowser_success(camoufox_browser, mock_browserforge):
    """Test __GetBrowser__ successfully launches Camoufox."""
    mock_context = AsyncMock(spec=BrowserContext)
    mock_fingerprint = Mock()
    mock_browserforge.get_fg.return_value = mock_fingerprint

    # Mock AsyncCamoufox
    mock_camoufox = AsyncMock()
    mock_camoufox.__aenter__.return_value = mock_context

    with patch("src.BrowserManager.camoufox_browser.AsyncCamoufox", return_value=mock_camoufox):
        with patch("src.BrowserManager.camoufox_browser.launch_options", return_value={}):
            result = await camoufox_browser._CamoufoxBrowser__GetBrowser__()

            assert result == mock_context
            mock_browserforge.get_fg.assert_called_once()


@pytest.mark.asyncio
async def test_GetBrowser_retries_on_invalid_ip(camoufox_browser, mock_browserforge, mock_logger):
    """Test __GetBrowser__ retries on Camoufox InvalidIP error."""
    mock_context = AsyncMock(spec=BrowserContext)
    mock_fingerprint = Mock()
    mock_browserforge.get_fg.return_value = mock_fingerprint

    # First call raises InvalidIP, second succeeds
    call_count = 0

    async def mock_aenter():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            import camoufox.exceptions

            raise camoufox.exceptions.InvalidIP("IP check failed")
        return mock_context

    mock_camoufox = AsyncMock()
    mock_camoufox.__aenter__ = mock_aenter

    with patch("src.BrowserManager.camoufox_browser.AsyncCamoufox", return_value=mock_camoufox):
        with patch("src.BrowserManager.camoufox_browser.launch_options", return_value={}):
            result = await camoufox_browser._CamoufoxBrowser__GetBrowser__()

            assert result == mock_context
            assert call_count == 2
            mock_logger.warning.assert_called()


@pytest.mark.asyncio
async def test_GetBrowser_max_retries(camoufox_browser, mock_browserforge):
    """Test __GetBrowser__ stops after max retries."""
    mock_browserforge.get_fg.return_value = Mock()

    async def mock_aenter():
        import camoufox.exceptions

        raise camoufox.exceptions.InvalidIP("IP check failed")

    mock_camoufox = AsyncMock()
    mock_camoufox.__aenter__ = mock_aenter

    with patch("src.BrowserManager.camoufox_browser.AsyncCamoufox", return_value=mock_camoufox):
        with patch("src.BrowserManager.camoufox_browser.launch_options", return_value={}):
            with pytest.raises(BrowserException, match="Max Camoufox IP retry"):
                await camoufox_browser._CamoufoxBrowser__GetBrowser__(tries=5)


@pytest.mark.asyncio
async def test_GetBrowser_other_exception(camoufox_browser, mock_browserforge):
    """Test __GetBrowser__ raises BrowserException on other errors."""
    mock_browserforge.get_fg.return_value = Mock()

    with patch(
        "src.BrowserManager.camoufox_browser.AsyncCamoufox", side_effect=Exception("Unknown error")
    ):
        with pytest.raises(BrowserException, match="Failed to launch Camoufox"):
            await camoufox_browser._CamoufoxBrowser__GetBrowser__()


# ============================================================================
# GET PAGE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_get_page_reuses_blank_page(camoufox_browser):
    """Test get_page returns existing blank page if available."""
    mock_page = AsyncMock(spec=Page)
    mock_page.url = "about:blank"
    mock_page.is_closed.return_value = False

    mock_context = AsyncMock(spec=BrowserContext)
    mock_context.pages = [mock_page]

    camoufox_browser.browser = mock_context

    result = await camoufox_browser.get_page()

    assert result == mock_page
    mock_context.new_page.assert_not_called()


@pytest.mark.asyncio
async def test_get_page_creates_new(camoufox_browser):
    """Test get_page creates new page if no blank page exists."""
    mock_existing_page = AsyncMock(spec=Page)
    mock_existing_page.url = "https://example.com"

    mock_new_page = AsyncMock(spec=Page)

    mock_context = AsyncMock(spec=BrowserContext)
    mock_context.pages = [mock_existing_page]
    mock_context.new_page.return_value = mock_new_page

    camoufox_browser.browser = mock_context

    result = await camoufox_browser.get_page()

    assert result == mock_new_page
    mock_context.new_page.assert_called_once()


@pytest.mark.asyncio
async def test_get_page_initializes_browser(camoufox_browser):
    """Test get_page initializes browser if not already initialized."""
    mock_context = AsyncMock(spec=BrowserContext)
    mock_page = AsyncMock(spec=Page)
    mock_context.pages = []
    mock_context.new_page.return_value = mock_page

    with patch.object(camoufox_browser, "getInstance", return_value=mock_context):
        result = await camoufox_browser.get_page()

        assert result == mock_page


@pytest.mark.asyncio
async def test_get_page_error(camoufox_browser):
    """Test get_page raises BrowserException on failure."""
    mock_context = AsyncMock(spec=BrowserContext)
    mock_context.pages = []
    mock_context.new_page.side_effect = Exception("Page creation failed")

    camoufox_browser.browser = mock_context

    with pytest.raises(BrowserException, match="Could not create a new page"):
        await camoufox_browser.get_page()


# ============================================================================
# CLOSE BROWSER TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_close_browser_success(camoufox_browser):
    """Test close_browser successfully closes browser context."""
    mock_context = AsyncMock(spec=BrowserContext)
    camoufox_browser.browser = mock_context

    result = await camoufox_browser.close_browser()

    assert result is True
    mock_context.__aexit__.assert_called_once()
    assert camoufox_browser.browser is None


@pytest.mark.asyncio
async def test_close_browser_already_closed(camoufox_browser):
    """Test close_browser returns True if browser already None."""
    camoufox_browser.browser = None

    result = await camoufox_browser.close_browser()

    assert result is True


@pytest.mark.asyncio
async def test_close_browser_error(camoufox_browser, mock_logger):
    """Test close_browser handles exceptions gracefully."""
    mock_context = AsyncMock(spec=BrowserContext)
    mock_context.__aexit__.side_effect = Exception("Close failed")

    camoufox_browser.browser = mock_context

    result = await camoufox_browser.close_browser()

    assert result is False
    mock_logger.error.assert_called()
