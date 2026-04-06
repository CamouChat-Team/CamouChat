"""
Unit tests for BrowserForge class.
Tests fingerprint generation, loading, and screen size matching.
"""

import logging
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from browserforge.fingerprints import Fingerprint

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from camouchat.BrowserManager import browserforge as bf_module
from camouchat.Exceptions import base

BrowserForge = bf_module.BrowserForge
BrowserException = base.BrowserException


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_logger():
    return Mock(spec=logging.Logger)


@pytest.fixture
def browserforge(mock_logger):
    return BrowserForge(log=mock_logger)


@pytest.fixture
def mock_fingerprint():
    """Create a mock fingerprint object."""
    fg = Mock(spec=Fingerprint)
    fg.screen = Mock()
    fg.screen.width = 1920
    fg.screen.height = 1080
    return fg


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================


def test_init_success(mock_logger):
    """Test BrowserForge initializes with logger."""
    bf = BrowserForge(log=mock_logger)
    assert bf.log == mock_logger


def test_init_no_logger():
    """Test BrowserForge uses default logger when not provided."""
    bf = BrowserForge(log=None)
    from camouchat.camouchat_logger import camouchatLogger

    assert bf.log == camouchatLogger


# ============================================================================
# GET_FG TESTS
# ============================================================================


def test_get_fg_loads_existing(browserforge, mock_fingerprint, tmp_path):
    """Test get_fg loads existing fingerprint from file."""
    fg_path = tmp_path / "fingerprint.pkl"
    mock_profile = Mock()
    mock_profile.fingerprint_path = fg_path

    # Create dummy fingerprint file
    with open(fg_path, "wb") as f:
        f.write(b"dummy")

    with patch("pickle.load", return_value=mock_fingerprint):
        # Mock _get_all_existing_fingerprints since it's called even if existing is found
        # Actually it's only called in the else block when file is empty.
        # Let's check get_fg again.
        result = browserforge.get_fg(mock_profile)

    assert result == mock_fingerprint


def test_get_fg_generates_new(browserforge, mock_fingerprint, tmp_path, mock_logger):
    """Test get_fg generates new fingerprint if file is empty."""
    fg_path = tmp_path / "fingerprint.pkl"
    mock_profile = Mock()
    mock_profile.fingerprint_path = fg_path

    fg_path.touch()  # Create empty file

    with patch.object(browserforge, "_get_all_existing_fingerprints", return_value=[]):
        with patch.object(browserforge, "__gen_fg__", return_value=mock_fingerprint):
            with patch("pickle.dump"):
                result = browserforge.get_fg(mock_profile)

    assert result == mock_fingerprint


def test_get_fg_path_not_exists(browserforge):
    """Test get_fg raises error if path doesn't exist."""
    fake_path = Path("/nonexistent/path/fg.pkl")
    mock_profile = Mock()
    mock_profile.fingerprint_path = fake_path

    with pytest.raises(BrowserException, match="path given does not exist"):
        browserforge.get_fg(mock_profile)


# ============================================================================
# FINGERPRINT GENERATION TESTS
# ============================================================================


def test_gen_fg_success(browserforge, mock_fingerprint, mock_logger):
    """Test __gen_fg__ generates valid fingerprint matching screen size."""
    with patch(
        "camouchat.BrowserManager.browserforge.BrowserForge.get_screen_size",
        return_value=(1920, 1080),
    ):
        with patch("camouchat.BrowserManager.browserforge.FingerprintGenerator") as MockGen:
            mock_gen_instance = MockGen.return_value
            mock_gen_instance.generate.return_value = mock_fingerprint

            result = browserforge.__gen_fg__()

            assert result == mock_fingerprint
            mock_logger.info.assert_called()


def test_gen_fg_retries_on_mismatch(browserforge, mock_logger):
    """Test __gen_fg__ retries if fingerprint screen doesn't match."""
    # First fingerprint mismatches, second matches
    bad_fg = Mock(spec=Fingerprint)
    bad_fg.screen = Mock(width=800, height=600)

    good_fg = Mock(spec=Fingerprint)
    good_fg.screen = Mock(width=1920, height=1080)

    with patch(
        "camouchat.BrowserManager.browserforge.BrowserForge.get_screen_size",
        return_value=(1920, 1080),
    ):
        with patch("camouchat.BrowserManager.browserforge.FingerprintGenerator") as MockGen:
            mock_gen_instance = MockGen.return_value
            mock_gen_instance.generate.side_effect = [bad_fg, good_fg]

            result = browserforge.__gen_fg__()

            assert result == good_fg
            assert mock_gen_instance.generate.call_count == 2
            mock_logger.warning.assert_called()


def test_gen_fg_max_attempts(browserforge, mock_logger):
    """Test __gen_fg__ stops after 10 attempts and returns last fingerprint."""
    bad_fg = Mock(spec=Fingerprint)
    bad_fg.screen = Mock(width=800, height=600)

    with patch(
        "camouchat.BrowserManager.browserforge.BrowserForge.get_screen_size",
        return_value=(1920, 1080),
    ):
        with patch("camouchat.BrowserManager.browserforge.FingerprintGenerator") as MockGen:
            mock_gen_instance = MockGen.return_value
            mock_gen_instance.generate.return_value = bad_fg

            result = browserforge.__gen_fg__()

            assert result == bad_fg
            assert mock_gen_instance.generate.call_count == 10
            assert "after 10 attempts" in mock_logger.warning.call_args[0][0]


def test_gen_fg_invalid_screen_size(browserforge):
    """Test __gen_fg__ raises error for invalid screen dimensions."""
    with patch(
        "camouchat.BrowserManager.browserforge.BrowserForge.get_screen_size",
        return_value=(0, 0),
    ):
        with pytest.raises(BrowserException, match="Invalid real screen dimensions"):
            browserforge.__gen_fg__()


# ============================================================================
# SCREEN SIZE DETECTION TESTS
# ============================================================================


@patch("platform.system", return_value="Windows")
def test_get_screen_size_windows(mock_system):
    """Test screen size detection on Windows."""
    with patch("ctypes.windll", create=True) as mock_windll:
        mock_windll.user32.GetSystemMetrics.side_effect = [1920, 1080]

        w, h = BrowserForge.get_screen_size()

        assert w == 1920
        assert h == 1080


@patch("platform.system", return_value="Linux")
def test_get_screen_size_linux(mock_system):
    """Test screen size detection on Linux."""
    mock_output = b"  dimensions:    1920x1080 pixels"

    with patch("subprocess.check_output", return_value=mock_output):
        w, h = BrowserForge.get_screen_size()

        assert w == 1920
        assert h == 1080


@patch("platform.system", return_value="Darwin")
def test_get_screen_size_macos(mock_system):
    """Test screen size detection on macOS."""
    mock_quartz = Mock()
    mock_quartz.CGMainDisplayID.return_value = 1
    mock_quartz.CGDisplayPixelsWide.return_value = 2560
    mock_quartz.CGDisplayPixelsHigh.return_value = 1440

    with patch.dict("sys.modules", {"Quartz": mock_quartz}):
        w, h = BrowserForge.get_screen_size()

        assert w == 2560
        assert h == 1440


@patch("platform.system", return_value="FreeBSD")
def test_get_screen_size_unsupported_os(mock_system):
    """Test get_screen_size raises error on unsupported OS."""
    with pytest.raises(BrowserException, match="Unsupported OS"):
        BrowserForge.get_screen_size()


# ============================================================================
# JSON UTILITY TESTS
# ============================================================================


def test_get_fingerprint_as_dict_success(tmp_path):
    """Test loading fingerprint JSON successfully."""
    json_path = tmp_path / "fg.json"
    json_path.write_text('{"screen": {"width": 1920, "height": 1080}}')

    mock_profile = Mock()
    mock_profile.fingerprint_path = json_path

    result = BrowserForge.get_fingerprint_as_dict(mock_profile)

    assert result["screen"]["width"] == 1920


def test_get_fingerprint_as_dict_not_exists():
    fake_path = Path("/fake/path.json")
    mock_profile = Mock()
    mock_profile.fingerprint_path = fake_path

    with pytest.raises(BrowserException, match="does not exist"):
        BrowserForge.get_fingerprint_as_dict(mock_profile)


def test_get_fingerprint_as_dict_not_file(tmp_path):
    """Test get_fingerprint_as_dict raises error if path is directory."""
    mock_profile = Mock()
    mock_profile.fingerprint_path = tmp_path

    with pytest.raises(BrowserException, match="is not a file"):
        BrowserForge.get_fingerprint_as_dict(mock_profile)


def test_get_fingerprint_as_dict_empty(tmp_path):
    """Test get_fingerprint_as_dict raises error if file is empty."""
    empty_file = tmp_path / "empty.json"
    empty_file.touch()

    mock_profile = Mock()
    mock_profile.fingerprint_path = empty_file

    with pytest.raises(BrowserException, match="is empty"):
        BrowserForge.get_fingerprint_as_dict(mock_profile)


def test_get_fingerprint_as_dict_invalid_json(tmp_path):
    """Test get_fingerprint_as_dict raises error for invalid JSON."""
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{invalid json")

    mock_profile = Mock()
    mock_profile.fingerprint_path = bad_json

    with pytest.raises(BrowserException, match="Invalid fingerprint JSON"):
        BrowserForge.get_fingerprint_as_dict(mock_profile)


def test_get_fingerprint_as_dict_not_dict(tmp_path):
    """Test get_fingerprint_as_dict raises error if JSON is not a dict."""
    list_json = tmp_path / "list.json"
    list_json.write_text("[1, 2, 3]")

    mock_profile = Mock()
    mock_profile.fingerprint_path = list_json

    with pytest.raises(BrowserException, match="not a valid dict"):
        BrowserForge.get_fingerprint_as_dict(mock_profile)
