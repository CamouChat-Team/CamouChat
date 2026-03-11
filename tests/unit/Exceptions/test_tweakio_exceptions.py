from src.Exceptions import (
    ChatNotFoundError,
    ChatClickError,
    MessageNotFoundError,
    AuthenticationError,
)

import pytest


def test_chat_not_found_error():
    """Test ChatNotFoundError can be raised and caught."""
    with pytest.raises(ChatNotFoundError) as exc_info:
        raise ChatNotFoundError("test")
    assert str(exc_info.value) == "test"


def test_chat_click_error():
    """Test ChatClickError can be raised and caught."""
    with pytest.raises(ChatClickError) as exc_info:
        raise ChatClickError("test")
    assert str(exc_info.value) == "test"


def test_message_not_found_error():
    """Test MessageNotFoundError can be raised and caught."""
    with pytest.raises(MessageNotFoundError) as exc_info:
        raise MessageNotFoundError("test")
    assert str(exc_info.value) == "test"


def test_authentication_error():
    """Test AuthenticationError can be raised and caught."""
    with pytest.raises(AuthenticationError) as exc_info:
        raise AuthenticationError("test")
    assert str(exc_info.value) == "test"
