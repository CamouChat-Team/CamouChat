import sys
from pathlib import Path

# Add project root to sys.path so 'src' can be imported
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.resolve()))

from src.BrowserManager.profile_manager import ProfileManager


def test_profile_manager_manual():

    pm = ProfileManager()

    print("Creating profiles...")
    try:
        pm.create_profile("whatsapp", "test1")
    except ValueError:
        pass

    try:
        pm.create_profile("whatsapp", "test2")
    except ValueError:
        pass

    print("Profiles:", pm.list_profiles("whatsapp"))

    pm.create_backup("whatsapp", "test2")

    print("Deleting test1...")
    pm.delete_profile("whatsapp", "test1")

    print("Profiles after deletion:", pm.list_profiles("whatsapp"))
