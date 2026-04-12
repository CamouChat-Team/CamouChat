from enum import Enum
from typing import List


class StorageType(str, Enum):
    """Supported storage database dialects."""

    SQLITE = "sqlite"
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"

    @staticmethod
    def list_types() -> List[str]:
        """List available storage types."""
        return [t.value for t in StorageType]
