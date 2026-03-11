"""
Fingerprint generation and management for BrowserForge.

Handles creating, loading, and persisting browser fingerprints
that match the system's actual screen dimensions.
"""

import json
import logging
import os
import pickle
from pathlib import Path
from typing import Tuple, Optional

from browserforge.fingerprints import Fingerprint, FingerprintGenerator

from src.Exceptions.base import BrowserException
from src.Interfaces.browserforge_capable_interface import BrowserForgeCapable


class BrowserForgeCompatible(BrowserForgeCapable):
    """
    BrowserForge fingerprint manager.

    Generates fingerprints that match system screen size to avoid detection.
    Reuses existing fingerprints from disk when available.
    """

    def __init__(self, log: Optional[logging.Logger] = None) -> None:
        self.log = log

        if log is None:
            raise BrowserException("log not given in BrowserForgeCompatible")

    def get_fg(self, profile_path: Path) -> Fingerprint:
        """
        profile_path : certified path for fingerprint to be saved and re-use later
        Returns : Fingerprint

        work :
        if data is already there on the file , it will be reused.
        if not it will then generate and save at the given file path.

        """
        if profile_path.exists():
            if os.stat(profile_path).st_size > 0:
                # Pick the old fg , changing fg for an account enables security issues for platform
                # Potential in Account Ban
                with open(profile_path, "rb") as fh:
                    fg = pickle.load(fh)
            else:
                # Create new fg there compatible to the current device.
                fg = self.__gen_fg__()
                if fg is not None:
                    with open(profile_path, "wb") as fh:
                        pickle.dump(fg, fh)  # Save to same file
            return fg
        else:
            raise BrowserException("path given does not exist")

    def __gen_fg__(self) -> Fingerprint:
        gen = FingerprintGenerator()
        real_w, real_h = BrowserForgeCompatible.get_screen_size()
        tolerance = 0.1
        attempt = 0

        if real_w <= 0 or real_h <= 0:
            raise BrowserException("Invalid real screen dimensions")

        while True:
            fg = gen.generate()
            w, h = fg.screen.width, fg.screen.height
            attempt += 1

            if abs(w - real_w) / real_w < tolerance and abs(h - real_h) / real_h < tolerance:
                if self.log:
                    self.log.info(f"✅ Fingerprint screen OK: {w}x{h}")
                return fg

            if self.log:
                self.log.warning(
                    f"🔁 Invalid fingerprint screen ({w}x{h}) vs real ({real_w}x{real_h}). Regenerating... ({attempt})"
                )

            if attempt >= 10:
                if self.log:
                    self.log.warning("⚠️ Using last generated fingerprint after 10 attempts")
                return fg

    @staticmethod
    def get_screen_size() -> Tuple[int, int]:
        """
        Returns the width and height of the primary display in pixels.
        Supports Windows, Linux (X11), and macOS.
        """
        import platform

        system = platform.system()

        # ---------------- Windows ----------------
        if system == "Windows":
            try:
                import ctypes

                user32 = ctypes.windll.user32  # type: ignore[attr-defined]
                try:
                    user32.SetProcessDPIAware()
                except Exception:
                    pass  # older Windows versions

                return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

            except Exception as e:
                raise BrowserException("Windows screen size detection failed") from e

        # ---------------- Linux ----------------
        elif system == "Linux":
            try:
                import subprocess

                out = subprocess.check_output(["xdpyinfo"], stderr=subprocess.DEVNULL).decode()

                for line in out.splitlines():
                    if "dimensions:" in line:
                        dims = line.split()[1].split("x")
                        return int(dims[0]), int(dims[1])

                raise BrowserException("xdpyinfo did not return screen dimensions")

            except Exception as e:
                raise BrowserException("Linux screen size detection failed") from e

        # ---------------- macOS ----------------
        elif system == "Darwin":
            try:
                import Quartz
            except ImportError as e:
                raise BrowserException("Quartz not available on macOS") from e

            display = Quartz.CGMainDisplayID()
            return (
                Quartz.CGDisplayPixelsWide(display),
                Quartz.CGDisplayPixelsHigh(display),
            )

        # ---------------- Unsupported OS ----------------
        else:
            raise BrowserException(f"Unsupported OS for screen size detection: {system}")

    @staticmethod
    def get_fingerprint_as_dict(saved_fingerprint_path: Path) -> dict:
        if not saved_fingerprint_path.exists():
            raise BrowserException("saved_fingerprint_path does not exist")

        if not saved_fingerprint_path.is_file():
            raise BrowserException("saved_fingerprint_path is not a file")

        if os.stat(saved_fingerprint_path).st_size == 0:
            raise BrowserException("saved_fingerprint_path is empty")

        try:
            with open(
                saved_fingerprint_path, encoding="utf-8"
            ) as f:  # default opens in reading mode.
                data = json.load(f)

            if not isinstance(data, dict):
                raise BrowserException("Fingerprint JSON is not a valid dict")

            return data

        except json.JSONDecodeError as e:
            raise BrowserException(f"Invalid fingerprint JSON format: {e}")

        except Exception as e:
            raise BrowserException(f"Failed to load fingerprint JSON: {e}")
