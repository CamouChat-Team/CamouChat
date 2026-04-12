"""Generic low-level interaction controller interface."""

from typing import Any, Protocol


class InteractionControllerProtocol(Protocol):
    """Base contract for reusable browser interaction primitives.

    This interface intentionally avoids feature-level operations such as
    sending media, replying, or downloading files. Those belong in focused
    capability interfaces/classes. Implementations should expose only the
    common input actions that higher-level capabilities can compose.
    """

    async def focus_input(self, source: Any = None, **kwargs) -> Any:
        """Focus an input-like target and return the focused target when useful."""
        ...

    async def type_text(self, text: str, **kwargs) -> bool:
        """Type text into an input-like target."""
        ...

    async def clear_input(self, source: Any = None, **kwargs) -> None:
        """Clear an input-like target."""
        ...

    async def enter(self, **kwargs) -> None:
        """Confirm the current input, usually by pressing Enter."""
        ...
