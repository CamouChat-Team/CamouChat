"""
Importing Only WAPI Wrapper, All functions requires this to fetch data of any Kind.
"""

from .wajs_wrapper import WapiWrapper
from .wajs_scripts import WAJS_Scripts

__all__ = ["WapiWrapper", "WAJS_Scripts"]
