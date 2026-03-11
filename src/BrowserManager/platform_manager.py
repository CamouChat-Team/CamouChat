from enum import Enum
from typing import List


class Platform(str, Enum):
    """Absolute names"""

    WHATSAPP = "WhatsApp"
    ARATTAI = "Arattai"

    @staticmethod
    def list_platforms() -> List[str]:
        """List available platforms"""
        return [p.value for p in Platform]
