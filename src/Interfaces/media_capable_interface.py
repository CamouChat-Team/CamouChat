"""Abstract base class for media upload functionality."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from playwright.async_api import Page

from src.Interfaces.web_ui_selector import WebUISelectorCapable


class MediaType(str, Enum):
    """Supported media types for upload."""

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"


@dataclass(frozen=True)
class FileTyped:
    """File metadata for media upload."""

    uri: str
    name: str
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None


class MediaCapableInterface(ABC):
    """Base interface for media upload operations."""

    @abstractmethod
    def __init__(self, page: Page, log: logging.Logger, UIConfig: WebUISelectorCapable, **kwargs):
        self.page = page
        self.log = log
        self.UIConfig = UIConfig

    @abstractmethod
    async def add_media(self, mtype: MediaType, file: FileTyped, **kwargs) -> bool:
        """Upload media file to a chat."""
        ...
