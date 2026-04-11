"""Contracts for platform authentication handlers."""

from abc import ABC, abstractmethod


class LoginInterface(ABC):
    """Base contract for authentication handlers.

    Implementations own platform-specific logger defaults and selector wiring.
    """

    @abstractmethod
    async def login(self) -> bool:
        """Perform login authentication."""
        ...

    @abstractmethod
    async def is_login_successful(self) -> bool:
        """Check if login was successful."""
        ...
