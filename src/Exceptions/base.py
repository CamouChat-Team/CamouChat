"""
Tweakio SDK Custom Exceptions

Hierarchy:
    TweakioError etc. (Base.py)
    ├── WhatsApp.py
        ├── ChatError,
        └── MessageError etc.
"""


# -------------------- Base Tweakio Error --------------------
class TweakioError(Exception):
    """Base exception for all Tweakio SDK errors"""

    pass


# -------------------- Authentication errors --------------------
class AuthenticationError(TweakioError):
    """Base exception for authentication errors"""

    pass


# -------------------- Filtering Errors --------------------
class MessageFilterError(TweakioError):
    """Base exception for message-related errors"""

    pass


# -------------------- Storage Errors --------------------
class StorageError(TweakioError):
    """Base exception for storage errors"""

    pass


# -------------------- Humanized Operations Errors --------------------


class HumanizedOperationError(TweakioError):
    """Base exception for humanized operation errors"""

    pass


class ElementNotFoundError(HumanizedOperationError):
    """Element not found error  , expects Element/target empty"""

    pass


# -------------------- Browser Exceptions --------------------
class BrowserException(TweakioError):
    """Base exception for browser errors"""

    pass
