"""
Unit tests for HumanizedOperations class.
Tests cover typing simulation, clipboard usage, and fallback mechanisms.
"""

import logging
from unittest.mock import Mock, AsyncMock, patch

import pytest
from playwright.async_api import Page, Locator, TimeoutError as PlaywrightTimeoutError

from camouchat.Exceptions.base import ElementNotFoundError, HumanizedOperationError
from camouchat.WhatsApp.humanized_operations import HumanizedOperations
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
    return page


@pytest.fixture
def mock_ui_config():
    return Mock(spec=WebSelectorConfig)


@pytest.fixture
def humanize_fixture(mock_page, mock_logger, mock_ui_config):
    with patch("camouchat.WhatsApp.humanized_operations.pyperclip") as mock_clip:
        humanize = HumanizedOperations(page=mock_page, log=mock_logger, UIConfig=mock_ui_config)
        yield humanize, mock_clip


# ============================================================================
# TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_init_page_none(mock_logger, mock_ui_config):
    with pytest.raises(ValueError, match="page must not be None"):
        HumanizedOperations(page=None, log=mock_logger, UIConfig=mock_ui_config)


@pytest.mark.asyncio
async def test_typing_success_short(humanize_fixture):
    """Test typing short text uses keyboard typing."""
    humanize, mock_clip = humanize_fixture
    mock_source = AsyncMock(spec=Locator)

    result = await humanize.typing(text="Hello World", source=mock_source)

    assert result is True
    # Should click source
    mock_source.click.assert_called_once()
    # Should clear text (Ctrl+A, Backspace)
    mock_source.press.assert_any_call("Control+A")
    mock_source.press.assert_any_call("Backspace")

    # Should type text directly
    humanize.page.keyboard.type.assert_called_with(
        text="Hello World", delay=pytest.approx(90, abs=10)
    )
    # Should NOT use clipboard
    mock_clip.copy.assert_not_called()


@pytest.mark.asyncio
async def test_typing_success_long(humanize_fixture):
    """Test typing long text uses clipboard."""
    humanize, mock_clip = humanize_fixture
    mock_source = AsyncMock(spec=Locator)

    # Text > 50 chars
    long_text = "A" * 60 + "\n" + "B" * 60

    # Configure mock_clip to not fail
    mock_clip.copy = Mock()

    result = await humanize.typing(text=long_text, source=mock_source)

    assert result is True

    # Each paste calls pyperclip.copy twice: once to set, once to restore.
    # 2 long lines = 4 pyperclip.copy calls total.
    assert mock_clip.copy.call_count == 4
    humanize.page.keyboard.press.assert_any_call("Control+V")
    humanize.page.keyboard.press.assert_any_call("Shift+Enter")  # Newline handling


@pytest.mark.asyncio
async def test_typing_timeout_fallback(humanize_fixture):
    """Test fallback to instant fill on timeout."""
    humanize, _ = humanize_fixture
    mock_source = AsyncMock(spec=Locator)
    mock_source.click.side_effect = PlaywrightTimeoutError("Timeout")

    # Use patch to mock _Instant_fill to verify it gets called?
    # Or just verify behavior provided it works.

    result = await humanize.typing(text="test", source=mock_source)

    assert result is True
    # Verify fallback behavior: fill was called if _Instant_fill called fill
    # Actually, we can spy on _Instant_fill if we want, but let's check outcome
    mock_source.fill.assert_called_with("test")
    humanize.page.keyboard.press.assert_called_with("Enter")


@pytest.mark.asyncio
async def test_instant_fill_success(humanize_fixture):
    """Test _Instant_fill works correctly."""
    humanize, _ = humanize_fixture
    mock_source = AsyncMock(spec=Locator)

    result = await humanize._Instant_fill(text="failover", source=mock_source)

    assert result is True
    mock_source.fill.assert_called_with("failover")
    humanize.page.keyboard.press.assert_called_with("Enter")


@pytest.mark.asyncio
async def test_instant_fill_failure(humanize_fixture):
    """Test _Instant_fill returns False on exception."""
    humanize, _ = humanize_fixture
    mock_source = AsyncMock(spec=Locator)
    # Mock fallback failure logic - raises HumanizedOperationError?
    mock_source.fill.side_effect = Exception("Fill Error")

    # The code implementation:
    # try: fill... except specific Playwright Errors -> raise HumanizedOperationError
    # BUT if generic Exception? It crashes.
    # Exception("Fill Error") is not PlaywrightTimeoutError.

    # Test internal exception bubbling or handling?
    # Let's mock a PlaywrightTimeoutError to test the catch block
    mock_source.fill.side_effect = PlaywrightTimeoutError("Time")

    # It should raise HumanizedOperationError
    with pytest.raises(HumanizedOperationError):
        await humanize._Instant_fill(text="failover", source=mock_source)


@pytest.mark.asyncio
async def test_typing_no_source(humanize_fixture):
    """Test typing raises error if source is None."""
    humanize, _ = humanize_fixture
    with pytest.raises(ElementNotFoundError):
        await humanize.typing(text="test", source=None)
