"""
CamouBrowser Config.
Pass this config to the CamouBrowser
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional

from camouchat.BrowserManager.platform_manager import Platform
from camouchat.BrowserManager.browserforge import BrowserForge


@dataclass
class BrowserConfig:
    """
    Config dataclass for browser.
    """

    platform: Platform
    locale: str
    enable_cache: bool
    headless: bool
    fingerprint_obj: BrowserForge
    geoip: bool = True
    proxy: Optional[Dict[str, str]] = None
    prefs: Optional[Dict[str, bool]] = None
    addons: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict) -> BrowserConfig:
        """
        Creates a BrowserConfig instance from a dictionary.

        Args:
            data: Dictionary containing configuration parameters.
                 - platform: Target platform (e.g., Platform.WHATSAPP)
                 - locale: Browser locale (e.g., "en-US")
                 - enable_cache: Whether to use browser cache
                 - headless: Whether to run in headless mode
                 - geoip: Whether to use GeoIP spoofing (default: True)
                 - proxy: Proxy configuration dictionary (server, username, password)
                 - prefs: Firefox user preferences
                 - addons: List of absolute paths to extensions
                 - fingerprint_obj: BrowserForgeCapable instance
        """
        return cls(
            platform=data.get("platform", Platform.WHATSAPP),
            locale=data.get("locale", "en-US"),
            enable_cache=data.get("enable_cache", False),
            headless=data.get("headless", False),
            prefs=data.get("prefs", {}),
            addons=data.get("addons", []),
            fingerprint_obj=data["fingerprint_obj"],
            geoip=data.get("geoip", True),
            proxy=data.get("proxy"),
        )

    def __str__(self):
        return f"""
            Platform: {self.platform}
            Locale: {self.locale}
            EnableCache: {self.enable_cache}
            Headless: {self.headless}
            Fingerprint: {self.fingerprint_obj!r} # Need to check for the fingerprint's __repr__
            geoip: {self.geoip}
            Proxy: {self.proxy}
            Preferences: {self.prefs}
            Addons: {self.addons}
            """

    def __repr__(self):
        return (
            f"BrowserConfig("
            f"platform={self.platform}, "
            f"locale='{self.locale}', "
            f"headless={self.headless}, "
            f"geoip={self.geoip}, "
            f"fingerprint_obj={self.fingerprint_obj!r}"
            f")"
        )
