"""
Unit tests for fingerprint uniqueness in BrowserForgeCompatible.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch
from camouchat.BrowserManager.platform_manager import Platform
import pytest
from browserforge.fingerprints import Fingerprint

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from camouchat.BrowserManager import browserforge as bf_module
from camouchat.BrowserManager.profile_info import ProfileInfo

BrowserForgeCompatible = bf_module.BrowserForge


@pytest.fixture
def mock_logger():
    return Mock()


@pytest.fixture
def browserforge(mock_logger):
    return BrowserForgeCompatible(log=mock_logger)


def test_get_all_existing_fingerprints(browserforge, tmp_path):
    platforms_dir = tmp_path / "platforms"
    whatsapp_dir = platforms_dir / "whatsapp"
    profile1_dir = whatsapp_dir / "profile1"
    profile2_dir = whatsapp_dir / "profile2"

    profile1_dir.mkdir(parents=True)
    profile2_dir.mkdir(parents=True)

    with open(profile1_dir / "fingerprint.pkl", "wb") as f:
        f.write(b"dummy")
    with open(profile2_dir / "fingerprint.pkl", "wb") as f:
        f.write(b"dummy")

    fg1 = Mock(spec=Fingerprint)
    fg2 = Mock(spec=Fingerprint)

    with patch("camouchat.directory.DirectoryManager") as MockDM:
        mock_dm = MockDM.return_value
        mock_dm.get_platform_dir.return_value = whatsapp_dir

        with patch("pickle.load", side_effect=[fg1, fg2]):
            fgs = browserforge._get_all_existing_fingerprints(Platform.WHATSAPP)

    assert len(fgs) == 2
    assert fg1 in fgs
    assert fg2 in fgs


def test_gen_fg_avoids_duplicates(browserforge):
    """Test that __gen_fg__ retries if a duplicate is generated."""
    dup_fg = Mock(spec=Fingerprint)
    dup_fg.screen = Mock(width=1920, height=1080)

    unique_fg = Mock(spec=Fingerprint)
    unique_fg.screen = Mock(width=1920, height=1080)

    # Mock screen size
    with patch.object(BrowserForgeCompatible, "get_screen_size", return_value=(1920, 1080)):
        with patch("camouchat.BrowserManager.browserforge_manager.FingerprintGenerator") as MockGen:
            mock_gen_instance = MockGen.return_value
            # First return duplicate, then return unique
            mock_gen_instance.generate.side_effect = [dup_fg, unique_fg]

            result = browserforge.__gen_fg__(avoid=[dup_fg])

            assert result == unique_fg
            assert mock_gen_instance.generate.call_count == 2
            browserforge.log.warning.assert_called_with(
                "🔁 Generated fingerprint already exists in another profile. Regenerating... (attempt 1)"
            )


def test_get_fg_integration(browserforge, tmp_path):

    fg_path = tmp_path / "fingerprint.pkl"
    fg_path.touch()

    mock_profile = Mock(spec=ProfileInfo)
    mock_profile.fingerprint_path = fg_path
    mock_profile.platform = Platform.WHATSAPP

    existing_fg = Mock(spec=Fingerprint)
    new_fg = Mock(spec=Fingerprint)

    with patch.object(browserforge, "_get_all_existing_fingerprints", return_value=[existing_fg]):
        with patch.object(browserforge, "__gen_fg__", return_value=new_fg) as mock_gen:
            with patch("pickle.dump"):
                result = browserforge.get_fg(mock_profile)

                assert result == new_fg
                mock_gen.assert_called_with(avoid=[existing_fg])
