"""
CamouChatError base exception for all camouchat based plugins.
all plugins must inherit this and create thier own child-exceptions.
"""


# -------------------- Base camouchat Error --------------------
class CamouChatError(Exception):
    """Base exception for all camouchat SDK errors"""

    pass


__all__ = ["CamouChatError"]
