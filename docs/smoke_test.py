from camouchat.BrowserManager import BrowserConfig
from camouchat.BrowserManager import Platform
from camouchat.BrowserManager import BrowserForgeCompatible
from camouchat.BrowserManager import ProfileManager
from camouchat.BrowserManager import ProfileInfo

# Steps to automate platforms via camouchat.

# Step 1  : Understand & Create a Profile from BrowserManager's ProfileManager

# Get a Object of ProfileManager
pm_obj = ProfileManager()

# Create a Profile with a name u want to add for your profile
work_profile : ProfileInfo  = pm_obj.create_profile(
    platform= Platform.WHATSAPP,
    #------------- This is a Required parameter -------------
    # or Any Platform available in the Platform class

    profile_id= "Work"
    #------------- This is a Required parameter -------------
    # This is your profile name for that platform.
    # Also name is fixed and same platform cannot have same profile name.
    # Ex : "Work"  ,  "woRk"  would not work , they are considered as same.
    # Case insensitivity is used so that it is easy to organize & profiles user-friendly to access.
)

"""
This work_profile we just created is actually a ProfileInfo dataclass
which contains all the information your profile needs.
"""

# Now that you have ur Profile Created we can create a browser with sandboxed to keep profile systems in isolation.

bdict = {
    "platform": Platform.WHATSAPP,
    #------------- This is Required Parameter -------------
    # Use BrowserManager's Internal class for to give platform attribute anywhere.

    "locale": "en-Us",
    # Or ur side in case if ur Locale is different.

    "enable_cache":False,
    # Generally not needed as True, But to save ram & resources usage make it False

    "headless" : True ,
    # Only use True if u want to see Browser working as visible UI.
    # but if Multiple Profiles are being activated it will be automatically set False to any more than 1 Browser.

    "prefs" : {},
    # It is given for Experimental bases , Works same as Camoufox's Browser Prefs to give to Firefox
    # Accepts [str , bool] , For Simple purpose and stealth purpose passing Empty Dict is recommended
    # Ex: Prefs for Clipboard event will look like :
    #     # {
    #     #     "dom.event.clipboardevents.enabled": True,
    #     #     "dom.allow_cut_copy": True,
    #     #     "dom.allow_copy": True,
    #     #     "dom.allow_paste": True,
    #     #     "dom.events.testing.asyncClipboard": True,
    #     # }

    "addons" : [],
    # Accepts List[str] , the str should be the real zip download path of addons | Extensions download in ur system,
    # It loads those Extensions in the browser , Making Browser More stealth.

    "fingerprint_obj" : BrowserForgeCompatible().get_fg(profile=work_profile)
    #------------- This is a Required Parameter -------------
    # Accepts single parameter "profile" of type "ProfileInfo"
    # This fingerprint is a BrowserForge Integration .
    # This Automatically uses the path in the dataclass given.
}

b_config = BrowserConfig.from_dict(bdict)

# After we have our browser Config Ready via BrowserConfig we are now able to start this profile's Browser.
# Note : Every New Profile has its own Browser , Same Steps .
# You can learn more about the Profiles & Management in the ProfileManager.md section .

# --- Lets proceed with our browser launch & getting our page from it & then opening a Bot for the available Platforms.
# Remember we had a Platform class in BrowserManager , We can only make Bots | Agents for those platforms only.

# Get the Browser obj.
from camouchat.BrowserManager import CamoufoxBrowser
# Import the CamoufoxBrowser , this is integrated & Customized for our camouchat usage.

from camouchat.camouchat_logger import camouchatLogger
# Import camouchatlogger from Custom_logger

browser = CamoufoxBrowser(
    # It takes 3 parameter & All are REQUIRED PARAMETER:

    config=b_config,
    # This is the browser_config we just created earlier , we can custom set our browser by changing data in the b_config.

    profile=work_profile,
    # Remember we created the profile earlier ?
    # That profile goes here so that browser is saved & Isolated with the Profiles.

    log=camouchatLogger
    # This logs details & Metrics. Nothing goes outside nothing comes inside. Fully maintain on user's side.
    # Used for Error Debugging
)

# Here is ur browser ready.

# Now get a Page from the browser.
# This page will be used throughout the platforms.

page_obj = browser.get_page()


# WhatsApp Platform Automation bot creating ------------

# step 1 : login.
import asyncio
from camouchat.WhatsApp import Login

# to work in any module you would need to pass on a UIConfig file.
# that's the Core heart of the camouchat to talk to WhatsApp

from camouchat.WhatsApp import WebSelectorConfig

async def main():
    ui_config_obj = WebSelectorConfig(page=await page_obj, log=camouchatLogger)
    login_obj = Login(
        # Need 3 Parameter --- all 3 are REQUIRED PARAMETER -------
        page=await page_obj,
        # Here give ur page obj
        # We Support Asyncio only.

        UIConfig=ui_config_obj,
        # Pass the UI Config Obj here.

        log=camouchatLogger
    )

    await login_obj.login(
        method = 0,
        # ---- REQUIRED PARAMETER ------
        # 0 FOR QR BASED LOGIN.
        # 1 FOR CODE BASED LOGIN.
        # It is only 1 time setup for your profile afterward it will auto save the session.

        wait_time=150_000,
        # ---- REQUIRED PARAMETER ------
        # The time it would wait for QR SCAN to be scanned , Default -> 180_000 seconds

        url = "web url of whatsapp.",
        # Optional to give sdk itself catches the saved URL.

        # ----------- THESE ARE ONLY REQUIRED WHEN YOU CHOOSE 1 AS YOUR LOGIN METHOD -------------
        number=0000000000,
        # ---- REQUIRED PARAMETER ------
        # No need of adding country Code

        country="Your Country"
        # ---- REQUIRED PARAMETER ------
        # This will automatically select your country.

        # -- IF U CHOOSE LOGIN 1 , IT USES CODE BASED LOGIN , IT WILL SEND THE CODE IN THE TERMINAL.
        #PLEASE ENTER THAT CODE INTO YOUR DEVICE -> NOTIFICATION [WHATSAPP SEND NOTIFICATION ITSELF] -> CLICK -> ENTER CODE.
    )

    # After you select your method & proceed , it will save your session inside the profile on your disk.
    # You can see all the Profiles & it's saved at the precised locations, You can check the fixed paths via ProfileInfo in ProfileInfo_&_PlatformManager.md

    # If you u want to log out , Just delete the profile via ProfileManager. Read more about ProfileManager in ProfileManager.md
    # OR you can log out via from your device too : WhatsApp -> Linked Devices -> Remove your Device.
    # In Case there are multiple linked devices -> Open Your Profile which you want to remove.
    # Then check in Linked Devices for recent active & remove it.

if __name__ == "__main__":
    asyncio.run(main()) # Run


# Fetch Chats
# Assuming you have already done Login into your account.

async def chatprocessor():
    from camouchat.WhatsApp import ChatProcessor
    from camouchat.WhatsApp import WebSelectorConfig
    from camouchat.WhatsApp import MessageProcessor

    C_processor = ChatProcessor(page=await page_obj, log=camouchatLogger, UIConfig=WebSelectorConfig(page=await page_obj, log=camouchatLogger))
    # All 3 are REQUIRED PARAMETER for ChatProcessor

    M_processor = MessageProcessor()

    count = 1
    while True:
        chats = await C_processor.fetch_chats()
        # Returns list of WhatsApp_chat
        count+=1


        if count== 6 : break

