from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional

from src.BrowserManager.platform_manager import Platform
from src.Interfaces.browserforge_capable_interface import BrowserForgeCapable


@dataclass
class BrowserConfig:
    """
    Config dataclass for browser.
    """

    # {
    #     "dom.event.clipboardevents.enabled": True,
    #     "dom.allow_cut_copy": True,
    #     "dom.allow_copy": True,
    #     "dom.allow_paste": True,
    #     "dom.events.testing.asyncClipboard": True,
    # }
    platform: Platform
    locale: str
    enable_cache: bool
    headless: bool
    fingerprint_obj: BrowserForgeCapable
    prefs: Optional[Dict[str, bool]] = None
    addons: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict) -> BrowserConfig:
        """dict should expose exact same name in the above given params."""
        return cls(
            platform=data["platform"],
            locale=data["locale"],
            enable_cache=data["enable_cache"],
            headless=data["headless"],
            prefs=data["prefs"],
            addons=data["addons"],
            fingerprint_obj=data["fingerprint_obj"],
        )
