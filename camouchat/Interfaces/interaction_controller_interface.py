"""Generic low-level interaction controller interface."""

from abc import ABC, abstractmethod
from typing import Any


class InteractionControllerInterface(ABC):
    """Base contract for reusable browser interaction primitives.

    This interface intentionally avoids feature-level operations such as
    sending media, replying, or downloading files. Those belong in focused
    capability interfaces/classes. Implementations should expose only the
    common input actions that higher-level capabilities can compose.
    """

    @abstractmethod
    async def focus_input(self) -> Any:
        """Focus an input-like target and return the focused target when useful."""
        ...

    @abstractmethod
    async def type_text(self) -> bool:
        """Type text into an input-like target."""
        ...

    @abstractmethod
    async def clear_input(self) -> None:
        """Clear an input-like target."""
        ...

    @abstractmethod
    async def enter(self) -> None:
        """Confirm the current input, usually by pressing Enter."""
        ...
