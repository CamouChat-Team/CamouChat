"""
Fingerprint generation interface for browser compatibility.

Implementations handle loading or generating BrowserForge fingerprints
to ensure realistic browser behavior and avoid detection.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from browserforge.fingerprints import Fingerprint


class BrowserForgeCapable(ABC):
    """
    Interface for fingerprint generation and management.

    Used to decouple fingerprint logic from browser implementation.
    """

    @abstractmethod
    def get_fg(self, profile_path: Path) -> Fingerprint:
        """
        Load or generate a fingerprint for the given profile.

        If a fingerprint exists at profile_path, it's reused.
        Otherwise, a new one is generated and saved.
        """
        ...
