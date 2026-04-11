"""Contracts for platform authentication handlers."""

from typing import Protocol

class LoginInterface(Protocol):
    """Base contract for authentication handlers.

    Implementations own platform-specific logger defaults and selector wiring.
    """

    async def login(self, **kwargs) -> bool:
        """Perform login authentication."""
        ...

    async def is_login_successful(self, **kwargs) -> bool:
        """Check if login was successful."""
        ...
