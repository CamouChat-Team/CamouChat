import sys
from pathlib import Path

# Add project root to sys.path so 'src' can be imported
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.resolve()))

from src.BrowserManager.profile_manager import ProfileManager


def test_profile_manager_manual():
    """Test full ProfileManager lifecycle: create, list, check existence, delete."""

    pm = ProfileManager()

    # Create two profiles (idempotent – OK if they already exist from a previous run)
    pm.create_profile("whatsapp", "test1")
    pm.create_profile("whatsapp", "test2")

    listing = pm.list_profiles("whatsapp")
    assert "whatsapp" in listing
    assert "test1" in listing["whatsapp"]
    assert "test2" in listing["whatsapp"]

    assert pm.is_profile_exists("whatsapp", "test1")
    assert pm.is_profile_exists("whatsapp", "test2")

    # Fetch profile info
    info = pm.get_profile("whatsapp", "test1")
    assert info.profile_id == "test1"

    # Delete both profiles
    pm.delete_profile("whatsapp", "test1", force=True)
    pm.delete_profile("whatsapp", "test2", force=True)

    assert not pm.is_profile_exists("whatsapp", "test1")
    assert not pm.is_profile_exists("whatsapp", "test2")
