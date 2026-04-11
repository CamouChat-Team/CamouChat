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

from camouchat.Exceptions.whatsapp import LoginError
from camouchat.WhatsApp.core.login import Login
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
    """Test login returns True after navigation (QR method)."""
    # Mock page.goto and wait_for_load_state
    login_instance.page.goto = AsyncMock()
    login_instance.page.wait_for_load_state = AsyncMock()

    mock_canvas = AsyncMock(spec=Locator)
    mock_canvas.is_visible.return_value = False  # QR gone = scanned
    login_instance.UIConfig.qr_canvas.return_value = mock_canvas

    mock_chats = AsyncMock(spec=Locator)
    mock_chats.wait_for = AsyncMock()
    login_instance.UIConfig.chat_list.return_value = mock_chats

    result = await login_instance.login(method=0)

    assert result is True
    login_instance.page.goto.assert_called()


@pytest.mark.asyncio
async def test_qr_login_success(login_instance, mock_ui_config, tmp_path):
    """Test QR login flow success."""
    # Setup
    mock_canvas = AsyncMock(spec=Locator)
    mock_canvas.is_visible.return_value = False  # QR gone means scanned
    mock_ui_config.qr_canvas.return_value = mock_canvas

    mock_chats = AsyncMock(spec=Locator)
    mock_chats.wait_for = AsyncMock()
    mock_ui_config.chat_list.return_value = mock_chats

    # Execution
    result = await login_instance.login(method=0)

    # Verification
    assert result is True
    login_instance.page.goto.assert_called_once()
    mock_chats.wait_for.assert_called_once()


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

    # 1. Phone login button
    mock_role_btn = AsyncMock(spec=Locator)
    mock_role_btn.count.return_value = 1
    login_instance.UIConfig.link_phone_number_button.return_value = mock_role_btn

    # 2. Country selector
    mock_chevron = AsyncMock(spec=Locator)
    login_instance.UIConfig.country_selector_button.return_value = mock_chevron

    # 3. Country list items
    mock_countries = AsyncMock(spec=Locator)
    mock_countries.count.return_value = 1
    mock_country_item = AsyncMock(spec=Locator)
    mock_country_item.inner_text.return_value = "India"
    mock_countries.nth.return_value = mock_country_item
    login_instance.UIConfig.country_list_items.return_value = mock_countries

    # 4. Phone Input
    mock_input = AsyncMock(spec=Locator)
    mock_input.count.return_value = 1
    login_instance.UIConfig.phone_number_input.return_value = mock_input

    # 5. Code element
    mock_code_el = AsyncMock(spec=Locator)
    mock_code_el.wait_for = AsyncMock()
    mock_code_el.get_attribute.return_value = "ABC-123"
    login_instance.UIConfig.link_code_container.return_value = mock_code_el

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
    login_instance.UIConfig.link_phone_number_button.return_value = mock_role_btn

    with pytest.raises(LoginError, match="Login-with-phone-number button not found"):
        await login_instance.login(
            method=1, number=123, country="Ind", save_path=tmp_path / "f.json"
        )


@pytest.mark.asyncio
async def test_code_login_country_missing(login_instance, tmp_path):
    """Test failure when country selector not found."""
    mock_role_btn = AsyncMock(spec=Locator)
    mock_role_btn.count.return_value = 1
    login_instance.UIConfig.link_phone_number_button.return_value = mock_role_btn

    mock_chevron = AsyncMock(spec=Locator)
    mock_chevron.count.return_value = 0  # Selector missing
    login_instance.UIConfig.country_selector_button.return_value = mock_chevron

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
    login_instance.UIConfig.link_phone_number_button.return_value = mock_role_btn

    with pytest.raises(LoginError, match="Failed to open phone login screen"):
        await login_instance.login(
            method=1, number=123, country="Ind", save_path=tmp_path / "f.json"
        )
