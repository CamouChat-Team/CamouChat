"""Contract for platform-specific web selector providers."""

from typing import Protocol


class UiConfigProtocol(Protocol):
    """Base type for selector configuration objects.

    Selector providers expose stable, named locators for a platform UI.
    Concrete providers choose logger defaults because logger naming often
    depends on the platform, profile, or runtime context.
    """

    ...
