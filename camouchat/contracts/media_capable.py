"""Contracts and value objects for media capabilities."""

from dataclasses import dataclass
from enum import Enum
from typing import Generic, Optional, TypeVar, Protocol

from camouchat.contracts.web_ui_selector import WebUISelectorCapable

T = TypeVar("T", bound=WebUISelectorCapable)


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


class MediaCapableProtocol(Protocol, Generic[T]):
    """Base contract for media operations.

    Concrete implementations own platform-specific selectors, browser state,
    and logger defaults. This interface only defines the shared upload action.
    """

    ui_config: T

    async def add_media(self, mtype: MediaType, file: FileTyped, **kwargs) -> bool:
        """Upload media file to a chat."""
        ...
