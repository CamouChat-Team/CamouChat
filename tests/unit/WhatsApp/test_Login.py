"""
Unit tests for Login class.
Tests cover QR login, Code-based login, and session management.
"""

import logging
from unittest.mock import Mock, AsyncMock

import pytest
from playwright.async_api import (
    Page,
    Locator,
    TimeoutError as PlaywrightTimeoutError,
    BrowserContext,
)

from src.Exceptions.whatsapp import LoginError
from src.WhatsApp.login import Login
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
    page.context = AsyncMock(spec=BrowserContext)
    page.keyboard = AsyncMock()
    return page


@pytest.fixture
def mock_ui_config():
    return Mock(spec=WebSelectorConfig)


@pytest.fixture
def login_instance(mock_page, mock_ui_config, mock_logger):
    return Login(page=mock_page, UIConfig=mock_ui_config, log=mock_logger)


# ============================================================================
# TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_init_page_none(mock_logger, mock_ui_config):
    with pytest.raises(ValueError, match="page must not be None"):
        Login(page=None, UIConfig=mock_ui_config, log=mock_logger)


@pytest.mark.asyncio
async def test_is_login_successful_success(login_instance, mock_ui_config):
    """Test is_login_successful returns True when chat list is visible."""
    mock_chats = AsyncMock(spec=Locator)
    mock_ui_config.chat_list.return_value = mock_chats

    result = await login_instance.is_login_successful()

    assert result is True
    mock_chats.wait_for.assert_called_once()


@pytest.mark.asyncio
async def test_is_login_successful_timeout(login_instance, mock_ui_config):
    """Test raises TimeoutError when chat list not visible."""
    mock_chats = AsyncMock(spec=Locator)
    mock_chats.wait_for.side_effect = PlaywrightTimeoutError("Timeout")
    mock_ui_config.chat_list.return_value = mock_chats

    with pytest.raises(TimeoutError, match="Timeout while checking"):
        await login_instance.is_login_successful()


@pytest.mark.asyncio
async def test_login_existing_session(login_instance, tmp_path):
    """Test login returns True immediately if session file exists."""
    # Create dummy session file
    session_file = tmp_path / "storage_state.json"
    session_file.write_text("{}")

    # Execution
    result = await login_instance.login(save_path=session_file)

    # Verification
    assert result is True
    # Implementation checks for session file AFTER navigation
    login_instance.page.goto.assert_called()


@pytest.mark.asyncio
async def test_qr_login_success(login_instance, mock_ui_config, tmp_path):
    """Test QR login flow success."""
    # Setup
    mock_canvas = AsyncMock(spec=Locator)
    mock_canvas.is_visible.return_value = False  # QR gone means scanned
    mock_ui_config.qr_canvas.return_value = mock_canvas

    mock_chats = AsyncMock(spec=Locator)
    mock_ui_config.chat_list.return_value = mock_chats

    session_file = tmp_path / "storage_state.json"

    # Execution
    result = await login_instance.login(method=0, save_path=session_file)

    # Verification
    assert result is True
    login_instance.page.goto.assert_called_once()
    mock_chats.wait_for.assert_called_once()
    login_instance.page.context.storage_state.assert_called_once()


@pytest.mark.asyncio
async def test_qr_login_timeout(login_instance, mock_ui_config, tmp_path):
    """Test QR login raises error on timeout."""
    mock_chats = AsyncMock(spec=Locator)
    mock_chats.wait_for.side_effect = PlaywrightTimeoutError("Wait timeout")
    mock_ui_config.chat_list.return_value = mock_chats
    mock_ui_config.qr_canvas.return_value = AsyncMock()

    with pytest.raises(LoginError, match="QR login timeout"):
        await login_instance.login(method=0, save_path=tmp_path / "new.json")


@pytest.mark.asyncio
async def test_code_login_missing_args(login_instance, tmp_path):
    """Test code login fails if number/country missing."""
    with pytest.raises(LoginError, match="Both number and country"):
        await login_instance.login(method=1, save_path=tmp_path / "new.json")


@pytest.mark.asyncio
async def test_code_login_success(login_instance, tmp_path):
    """Test code-based login full flow."""
    # Setup Mocks for UI interaction sequence
    mock_page = login_instance.page

    # 1. Phone login button
    mock_role_btn = AsyncMock(spec=Locator)
    mock_page.get_by_role.return_value = mock_role_btn
    mock_role_btn.count.return_value = 1

    # 2. Country selector
    mock_chevron = AsyncMock(spec=Locator)

    # 3. Country list items
    mock_countries = AsyncMock(spec=Locator)
    mock_countries.count.return_value = 1
    mock_country_item = AsyncMock(spec=Locator)
    mock_country_item.inner_text.return_value = "India"
    mock_countries.nth.return_value = mock_country_item

    mock_listitem = AsyncMock(spec=Locator)
    mock_listitem.locator.return_value = mock_countries

    def get_by_role_side_effect(role, name=None):
        if role == "button" and name:
            return mock_role_btn
        if role == "listitem":
            return mock_listitem
        return AsyncMock()

    mock_page.get_by_role.side_effect = get_by_role_side_effect

    # 4. Phone Input (using locator "form >> input")
    mock_input = AsyncMock(spec=Locator)
    mock_input.count.return_value = 1

    # 5. Code element
    mock_code_el = AsyncMock(spec=Locator)
    mock_code_el.get_attribute.return_value = "ABC-123"

    def locator_side_effect(sel):
        if "chevron" in sel:
            return mock_chevron
        if "form >> input" in sel:
            return mock_input
        if "data-link-code" in sel:
            return mock_code_el
        return AsyncMock()

    mock_page.locator.side_effect = locator_side_effect

    # Execution
    result = await login_instance.login(
        method=1, number=1234567890, country="India", save_path=tmp_path / "new.json"
    )

    # Verification
    assert result is True
    mock_role_btn.click.assert_called()
    mock_input.type.assert_called_with("1234567890", delay=pytest.approx(100, abs=20))
    mock_code_el.get_attribute.assert_called_with("data-link-code")


@pytest.mark.asyncio
async def test_logout_success(login_instance, tmp_path):
    """Test logout cleans up directory."""
    # Create a dummy file in a dir
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    (session_dir / "file.txt").write_text("data")

    result = await login_instance.logout(str(session_dir))

    assert result is True
    # Verify file deleted
    assert not (session_dir / "file.txt").exists()


@pytest.mark.asyncio
async def test_logout_invalid_path(login_instance):
    """Test logout returns False for invalid path."""
    result = await login_instance.logout("/invalid/path/that/does/not/exist")
    assert result is False


@pytest.mark.asyncio
async def test_login_unexpected_error(login_instance, tmp_path):
    """Test unexpected exception raises LoginError."""
    login_instance.page.goto.side_effect = Exception("Crash")

    # It catches PlaywrightTimeoutError but not generic Exception, so it should raise Exception
    with pytest.raises(Exception, match="Crash"):
        await login_instance.login(save_path=tmp_path / "fail.json")


@pytest.mark.asyncio
async def test_qr_login_visible_after_wait(login_instance, mock_ui_config, tmp_path):
    """Test QR login fails if QR is still visible after wait duration (not scanned)."""
    mock_chats = AsyncMock(spec=Locator)
    mock_ui_config.chat_list.return_value = mock_chats
    mock_chats.wait_for.return_value = None

    mock_canvas = AsyncMock(spec=Locator)
    mock_ui_config.qr_canvas.return_value = mock_canvas
    mock_canvas.is_visible.return_value = True  # QR still visible

    with pytest.raises(LoginError, match="QR not scanned"):
        await login_instance.login(method=0, save_path=tmp_path / "new.json")


@pytest.mark.asyncio
async def test_code_login_btn_missing(login_instance, tmp_path):
    """Test failure when phone login button is missing."""
    mock_role_btn = AsyncMock(spec=Locator)
    mock_role_btn.count.return_value = 0  # Button not found
    login_instance.page.get_by_role.return_value = mock_role_btn

    with pytest.raises(LoginError, match="Login-with-phone-number button not found"):
        await login_instance.login(
            method=1, number=123, country="Ind", save_path=tmp_path / "f.json"
        )


@pytest.mark.asyncio
async def test_code_login_country_missing(login_instance, tmp_path):
    """Test failure when country selector not found."""
    mock_role_btn = AsyncMock(spec=Locator)
    mock_role_btn.count.return_value = 1
    login_instance.page.get_by_role.return_value = mock_role_btn

    mock_chevron = AsyncMock(spec=Locator)
    mock_chevron.count.return_value = 0  # Selector missing
    login_instance.page.locator.return_value = mock_chevron

    with pytest.raises(LoginError, match="Country selector not found"):
        await login_instance.login(
            method=1, number=123, country="Ind", save_path=tmp_path / "f.json"
        )


@pytest.mark.asyncio
async def test_login_invalid_method(login_instance, tmp_path):
    """Test invalid login method raises error."""
    with pytest.raises(LoginError, match="Invalid login method"):
        await login_instance.login(method=99, save_path=tmp_path / "f.json")


@pytest.mark.asyncio
async def test_code_login_timeout(login_instance, tmp_path):
    """Test code login timeout on button click."""
    mock_role_btn = AsyncMock(spec=Locator)
    mock_role_btn.count.return_value = 1
    mock_role_btn.click.side_effect = PlaywrightTimeoutError("Bust")
    login_instance.page.get_by_role.return_value = mock_role_btn

    with pytest.raises(LoginError, match="Failed to open phone login screen"):
        await login_instance.login(
            method=1, number=123, country="Ind", save_path=tmp_path / "f.json"
        )
