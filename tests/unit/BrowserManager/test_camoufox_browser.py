"""
Unit tests for CamoufoxBrowser class.
Tests browser initialization, page management, and cleanup.
"""

import logging
from unittest.mock import Mock, AsyncMock, patch

import pytest
from playwright.async_api import BrowserContext, Page


from camouchat.BrowserManager import camoufox_browser as cb_module
from camouchat.Exceptions import base

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
def mock_browser_config(mock_browserforge):
    from camouchat.BrowserManager.browser_config import BrowserConfig

    return BrowserConfig(
        platform="whatsapp",
        locale="en-US",
        enable_cache=True,
        headless=True,
        fingerprint_obj=mock_browserforge,
    )


@pytest.fixture
def mock_profile_info(tmp_path):
    from camouchat.BrowserManager.profile_info import ProfileInfo

    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(exist_ok=True)
    fg_path = tmp_path / "fingerprint.pkl"
    fg_path.touch()

    return ProfileInfo(
        profile_id="test",
        platform="whatsapp",
        version="1.0",
        created_at="now",
        last_used="now",
        profile_dir=tmp_path,
        fingerprint_path=fg_path,
        cache_dir=cache_dir,
        media_dir=tmp_path,
        media_images_dir=tmp_path,
        media_videos_dir=tmp_path,
        media_voice_dir=tmp_path,
        media_documents_dir=tmp_path,
        database_path=tmp_path / "db",
        database_url="sqlite:///test.db",
        is_active=False,
        last_active_pid=None,
        encryption={},
    )


@pytest.fixture
def camoufox_browser(mock_browser_config, mock_profile_info, mock_logger):
    """Create CamoufoxBrowser instance with required dependencies."""
    return CamoufoxBrowser(
        config=mock_browser_config,
        profile=mock_profile_info,
        log=mock_logger,
    )


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================


def test_init_success(mock_browser_config, mock_profile_info, mock_logger):
    """Test CamoufoxBrowser initializes with all required params."""
    browser = CamoufoxBrowser(
        config=mock_browser_config,
        profile=mock_profile_info,
        log=mock_logger,
    )

    assert browser.config == mock_browser_config
    assert browser.profile == mock_profile_info
    assert browser.BrowserForge == mock_browser_config.fingerprint_obj
    assert browser.log == mock_logger


def test_init_missing_logger(mock_browser_config, mock_profile_info):
    """Test CamoufoxBrowser uses default logger when log is None."""
    browser = CamoufoxBrowser(
        config=mock_browser_config,
        profile=mock_profile_info,
        log=None,
    )
    from camouchat.camouchat_logger import camouchatLogger

    assert browser.log == camouchatLogger


def test_init_missing_browserforge(mock_browser_config, mock_profile_info, mock_logger):
    """Test CamoufoxBrowser raises error without BrowserForge."""
    mock_browser_config.fingerprint_obj = None
    with pytest.raises(BrowserException, match="BrowserForge is missing"):
        CamoufoxBrowser(config=mock_browser_config, profile=mock_profile_info, log=mock_logger)


def test_init_missing_cache_dir(mock_browser_config, mock_profile_info, mock_logger):
    """Test CamoufoxBrowser raises error without cache directory."""
    mock_profile_info.cache_dir = None
    with pytest.raises(BrowserException, match="Cache dir path is missing"):
        CamoufoxBrowser(
            config=mock_browser_config,
            profile=mock_profile_info,
            log=mock_logger,
        )


def test_init_missing_fingerprint_path(mock_browser_config, mock_profile_info, mock_logger):
    """Test CamoufoxBrowser raises error without fingerprint path."""
    mock_profile_info.fingerprint_path = None
    with pytest.raises(BrowserException, match="Fingerprint path is missing"):
        CamoufoxBrowser(
            config=mock_browser_config,
            profile=mock_profile_info,
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

    with patch(
        "camouchat.BrowserManager.camoufox_browser.AsyncCamoufox", return_value=mock_camoufox
    ):
        with patch("camouchat.BrowserManager.camoufox_browser.launch_options", return_value={}):
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

    with patch(
        "camouchat.BrowserManager.camoufox_browser.AsyncCamoufox", return_value=mock_camoufox
    ):
        with patch("camouchat.BrowserManager.camoufox_browser.launch_options", return_value={}):
            result = await camoufox_browser.__GetBrowser__()

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

    async def mock_aenter(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            import camoufox.exceptions

            raise camoufox.exceptions.InvalidIP("IP check failed")
        return mock_context

    mock_camoufox = AsyncMock()
    mock_camoufox.__aenter__ = mock_aenter

    with patch(
        "camouchat.BrowserManager.camoufox_browser.AsyncCamoufox", return_value=mock_camoufox
    ):
        with patch("camouchat.BrowserManager.camoufox_browser.launch_options", return_value={}):
            result = await camoufox_browser.__GetBrowser__()

            assert result == mock_context
            assert call_count == 2
            mock_logger.warning.assert_called()


@pytest.mark.asyncio
async def test_GetBrowser_max_retries(camoufox_browser, mock_browserforge):
    """Test __GetBrowser__ stops after max retries."""
    mock_browserforge.get_fg.return_value = Mock()

    async def mock_aenter(*args, **kwargs):
        import camoufox.exceptions

        raise camoufox.exceptions.InvalidIP("IP check failed")

    mock_camoufox = AsyncMock()
    mock_camoufox.__aenter__ = mock_aenter

    with patch(
        "camouchat.BrowserManager.camoufox_browser.AsyncCamoufox", return_value=mock_camoufox
    ):
        with patch("camouchat.BrowserManager.camoufox_browser.launch_options", return_value={}):
            with pytest.raises(BrowserException, match="Max Camoufox IP retry"):
                await camoufox_browser.__GetBrowser__(tries=5)


@pytest.mark.asyncio
async def test_GetBrowser_other_exception(camoufox_browser, mock_browserforge):
    """Test __GetBrowser__ raises BrowserException on other errors."""
    mock_browserforge.get_fg.return_value = Mock()

    with patch(
        "camouchat.BrowserManager.camoufox_browser.AsyncCamoufox",
        side_effect=Exception("Unknown error"),
    ):
        with pytest.raises(BrowserException, match="Failed to launch Camoufox"):
            await camoufox_browser.__GetBrowser__()


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

    result = await camoufox_browser.get_page(platform="whatsnew")

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

    result = await camoufox_browser.get_page(platform="whatsnew")

    assert result == mock_new_page
    mock_context.new_page.assert_called_once()


@pytest.mark.asyncio
async def test_get_page_initializes_browser(camoufox_browser):
    """Test get_page initializes browser if not already initialized."""
    mock_context = AsyncMock(spec=BrowserContext)
    mock_page = AsyncMock(spec=Page)
    mock_context.pages = []
    mock_context.new_page.return_value = mock_page

    with patch.object(camoufox_browser, "get_instance", return_value=mock_context):
        result = await camoufox_browser.get_page(platform="whatsnew")

        assert result == mock_page


@pytest.mark.asyncio
async def test_get_page_error(camoufox_browser):
    """Test get_page raises BrowserException on failure."""
    mock_context = AsyncMock(spec=BrowserContext)
    mock_context.pages = []
    mock_context.new_page.side_effect = Exception("Page creation failed")

    camoufox_browser.browser = mock_context

    with pytest.raises(BrowserException, match="Could not create a new page"):
        await camoufox_browser.get_page(platform="whatsnew")


# ============================================================================
# CLOSE BROWSER TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_close_browser_success(camoufox_browser):
    """Test close_browser successfully closes browser context."""
    mock_context = AsyncMock(spec=BrowserContext)
    camoufox_browser.browser = mock_context
    pid = 12345
    CamoufoxBrowser.Map[pid] = mock_context

    result = await CamoufoxBrowser.close_browser_by_pid(pid)

    assert result is True
    mock_context.__aexit__.assert_called_once()
    assert pid not in CamoufoxBrowser.Map


@pytest.mark.asyncio
async def test_close_browser_already_closed(camoufox_browser):
    """Test close_browser returns True if browser already None."""
    result = await CamoufoxBrowser.close_browser_by_pid(99999)

    assert result is True


@pytest.mark.asyncio
async def test_close_browser_error(camoufox_browser, mock_logger):
    """Test close_browser handles exceptions gracefully."""
    mock_context = AsyncMock(spec=BrowserContext)
    mock_context.__aexit__.side_effect = Exception("Close failed")

    pid = 12346
    CamoufoxBrowser.Map[pid] = mock_context
    camoufox_browser.browser = mock_context

    result = await CamoufoxBrowser.close_browser_by_pid(pid)

    assert result is False
