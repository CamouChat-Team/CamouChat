# 🖼️ MediaCapable: Rich Media Sharing

The `MediaCapable` class handles uploading images, videos, audio, and documents to WhatsApp chats. It automates the attachment menu and file chooser interaction securely.

---

### 🛠️ Setting up MediaCapable

```python
from camouchat.WhatsApp import MediaCapable, WebSelectorConfig
from camouchat.camouchat_logger import CamouChatLogger

ui_config = WebSelectorConfig(page=page_obj, log=CamouChatLogger)

media_handler = MediaCapable(
    page=page_obj,
    log=CamouChatLogger,
    UIConfig=ui_config
)
```

---

### 📦 Key Functions

#### 1. `add_media(mtype, file, **kwargs)`
Uploads a file based on the specified media type.

```python
from camouchat.Interfaces.media_capable_interface import MediaType, FileTyped

# Define the file type object
# 'uri' must be an absolute path to the file on your disk.
my_file = FileTyped(uri="/path/to/your/image.png")

# Upload the image
success = await media_handler.add_media(
    mtype=MediaType.IMAGE,
    # ------------- Required Parameter -------------
    # Options: IMAGE, VIDEO, AUDIO, DOCUMENT
    
    file=my_file
    # ------------- Required Parameter -------------
    # Object containing the file URI path.
)

if success:
    print("✅ Media uploaded! Don't forget to press Enter to send.")
```

---

### 📦 Media Types Mapping
The internal `_getOperational` logic automatically maps your requests to the correct WhatsApp menu item:
*   **`IMAGE`, `VIDEO`, `TEXT`**: Opens the "Photos & videos" drawer.
*   **`AUDIO`**: Opens the "Audio" upload option.
*   **`DOCUMENT`**: default fallback for all other types.

---

### 🛡️ Stealth & Stability
1. **File Chooser Interception**: The SDK uses `expect_file_chooser()` to catch the OS file dialog instantly and set the file path without needing manual UI interaction with the OS-level dialog.
2. **Natural Menu Interaction**: It clicks the `+` icon and waits for the dropdown to appear naturally with randomized delays.

---

### 💡 Pro Tip
After calling `add_media`, WhatsApp Web opens the "Caption" screen. You can use your `HumanizedOperations` to type a caption or just press `Enter` using `page.keyboard` to send the file immediately!
