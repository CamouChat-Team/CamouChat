import asyncio
import time
from camouchat.BrowserManager import ProfileManager, Platform
from camouchat.StorageDB import StorageType, SQLAlchemyStorage


class MockMessageAPI:
    """Mock representing MessageModelAPI for database testing"""

    def __init__(self, msg_id: str, body: str):
        self.id_serialized = msg_id
        self.body = body
        self.msgtype = "chat"
        self.fromMe = False
        self.timestamp = time.time()
        self.encryption_nonce = None
        self.from_chat = type("MockChat", (), {"id_serialized": "mock_chat_999@g.us"})()


async def main():
    print("--- Starting DB Smoke Test ---")

    # 1. Profile Setup
    pm = ProfileManager()
    profile = pm.create_profile(
        platform=Platform.WHATSAPP, profile_id="Work", storage_type=StorageType.SQLITE
    )

    # 2. Database Initialization
    storage = SQLAlchemyStorage.from_profile(profile=profile, queue=asyncio.Queue())
    await storage.start()

    # 3. Create Mock message
    mock_id = f"mock_{int(time.time())}"
    msg = MockMessageAPI(msg_id=mock_id, body="Smoke test message body!")

    print(f"\n[*] Inserting mock message with ID: {mock_id}")

    # 4. Insert directly
    await storage._insert_batch_internally([msg])

    # 5. Fetch and verify
    print("\n[*] Fetching message from Database...")
    db_msgs = await storage.get_messages_by_ids_async([mock_id])

    print(f"DATABASE VERIFICATION: {len(db_msgs)} records retrieved by target IDs.")

    if len(db_msgs) > 0:
        found_msg = db_msgs[0]
        print("\n--- Found DB Record ---")
        print(f"ID     : {found_msg.get('id_serialized')}")
        print(f"Body   : {found_msg.get('body')}")
        print(f"FromMe : {found_msg.get('fromMe')}")
        print(f"ChatID : {found_msg.get('chat_id')}")
        print("-----------------------")
    else:
        print("[!] Failed to retrieve message from DB.")


if __name__ == "__main__":
    asyncio.run(main())
