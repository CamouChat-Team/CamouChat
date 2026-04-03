"""
Fingerprint generation and management for BrowserForge.

Handles creating, loading, and persisting browser fingerprints
that match the system's actual screen dimensions.
"""

import json
from logging import Logger, LoggerAdapter
import os
import pickle
from pathlib import Path
from typing import Tuple, Optional, Union

from browserforge.fingerprints import Fingerprint, FingerprintGenerator

from camouchat.BrowserManager.platform_manager import Platform
from camouchat.BrowserManager.profile_info import ProfileInfo
from camouchat.Exceptions.base import BrowserException


class BrowserForge:
    """
    BrowserForge fingerprint manager.

    Generates fingerprints that match system screen size to avoid detection.
    Reuses existing fingerprints from disk when available.
    """

    log: Union[Logger, LoggerAdapter]

    def __init__(self, log: Optional[Union[Logger, LoggerAdapter]] = None) -> None:
        if log is None:
            from camouchat.camouchat_logger import camouchatLogger

            self.log = camouchatLogger
        else:
            self.log = log

    def get_fg(self, profile: ProfileInfo) -> Fingerprint:
        """
        If old fingerprint exists -> returns that fingerprint.
        Else creates new fingerprint.
        :param profile: ProfileInfo instance
        :return: Fingerprint
        """
        fingerprint_path: Path = profile.fingerprint_path
        if fingerprint_path.exists():

            if os.stat(fingerprint_path).st_size > 0:
                with open(fingerprint_path, "rb") as fh:
                    fg = pickle.load(fh)
            else:
                existing_fgs = self._get_all_existing_fingerprints(profile.platform)
                fg = self.__gen_fg__(avoid=existing_fgs)
                if fg is not None:
                    with open(fingerprint_path, "wb") as fh:
                        pickle.dump(fg, fh)
            return fg
        else:
            raise BrowserException("path given does not exist")

    def _get_all_existing_fingerprints(self, platform: Platform) -> list[Fingerprint]:
        """
        Scans all platforms and profiles to collect existing fingerprints.
        :return: list of Fingerprint objects
        """
        from camouchat.directory import DirectoryManager

        dm = DirectoryManager()
        fingerprints: list[Fingerprint] = []

        platform_dir = dm.get_platform_dir(platform)
        if not platform_dir.exists():
            return fingerprints

        for profile_dir in platform_dir.iterdir():
            if not profile_dir.is_dir():
                continue

            fg_path = profile_dir / "fingerprint.pkl"
            if fg_path.exists() and fg_path.stat().st_size > 0:
                try:
                    with open(fg_path, "rb") as fh:
                        fg = pickle.load(fh)
                        fingerprints.append(fg)
                except Exception as e:
                    self.log.warning(f"Could not load fingerprint from {fg_path}: {e}")

        return fingerprints

    def __gen_fg__(self, avoid: Optional[list[Fingerprint]] = None) -> Fingerprint:
        """
        Generates a new fingerprint.
        :param avoid: Optional list of fingerprints to avoid
        :return: Fingerprint
        """
        gen = FingerprintGenerator()
        real_w, real_h = BrowserForge.get_screen_size()
        tolerance = 0.1
        attempt = 0
        avoid = avoid or []

        if real_w <= 0 or real_h <= 0:
            raise BrowserException("Invalid real screen dimensions")

        fg: Fingerprint
        while True:
            fg = gen.generate()
            w, h = fg.screen.width, fg.screen.height
            attempt += 1

            if abs(w - real_w) / real_w < tolerance and abs(h - real_h) / real_h < tolerance:
                if fg in avoid:
                    if self.log:
                        self.log.warning(
                            f"🔁 Generated fingerprint already exists in another profile. Regenerating... (attempt {attempt})"
                        )
                    if attempt < 30:
                        continue

                if self.log:
                    self.log.info(f"✅ Fingerprint screen OK: {w}x{h}")
                break

            if self.log:
                self.log.warning(
                    f"🔁 Invalid fingerprint screen ({w}x{h}) vs real ({real_w}x{real_h}). Regenerating... ({attempt})"
                )

            if attempt >= 10:
                if self.log:
                    self.log.warning("⚠️ Using last generated fingerprint after 10 attempts")
                break

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
    def get_fingerprint_as_dict(profile: ProfileInfo) -> dict:
        """
        Auto-Configure path to check & return data .
        :param profile: ProfileInfo
        :return: dict
        """
        saved_fingerprint_path: Path = profile.fingerprint_path

        if not saved_fingerprint_path.exists():
            raise BrowserException("saved_fingerprint_path does not exist")

        if not saved_fingerprint_path.is_file():
            raise BrowserException("saved_fingerprint_path is not a file")

        if os.stat(saved_fingerprint_path).st_size == 0:
            raise BrowserException("saved_fingerprint_path is empty")

        try:
            with open(saved_fingerprint_path, encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                raise BrowserException("Fingerprint JSON is not a valid dict")

            return data

        except json.JSONDecodeError as e:
            raise BrowserException(f"Invalid fingerprint JSON format: {e}")

        except Exception as e:
            raise BrowserException(f"Failed to load fingerprint JSON: {e}")

    def __repr__(self):
        return f"BrowserForge(" f"log={type(self.log).__name__}" f")"
