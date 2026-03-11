"""
SQLAlchemy database models for message storage.
Supports SQLite, PostgreSQL, and MySQL.
"""

from datetime import datetime, timezone
from sqlalchemy import String, Text, Float, DateTime, Integer, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class Message(Base):
    """
    Message storage model.

    Compatible with SQLite, PostgreSQL, and MySQL.
    """

    __tablename__ = "messages"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Message identification
    message_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    # Message content
    raw_data: Mapped[str] = mapped_column(Text, nullable=True)
    encrypted_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    encryption_nonce: Mapped[str | None] = mapped_column(String(255), nullable=True)
    data_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    direction: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Chat relationship
    parent_chat_name: Mapped[str] = mapped_column(
        String(255), nullable=False, default="", index=True
    )
    parent_chat_id: Mapped[str] = mapped_column(String(255), nullable=False, default="", index=True)
    # Encrypted versions of chat name (populated when encryption is enabled).
    # When encrypted_chat_name is set, parent_chat_name holds a HMAC-SHA256
    # hex digest of the original name (queryable, but not reversible without key).
    encrypted_chat_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    chat_name_nonce: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Timing
    system_hit_time: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True
    )

    # Composite indexes for common queries
    __table_args__ = (
        Index("idx_chat_name_time", "parent_chat_name", "created_at"),
        Index("idx_chat_id_time", "parent_chat_id", "created_at"),
    )

    def __repr__(self) -> str:
        chat_label = "<encrypted>" if self.encrypted_chat_name else self.parent_chat_name
        return (
            f"<Message(id={self.id}, message_id='{self.message_id}', "
            f"direction='{self.direction}', chat='{chat_label}')>"
        )

    def to_dict(self) -> dict:
        """Convert message to dictionary."""
        return {
            "id": self.id,
            "message_id": self.message_id,
            "raw_data": self.raw_data,
            "encrypted_message": self.encrypted_message,
            "encryption_nonce": self.encryption_nonce,
            "data_type": self.data_type,
            "direction": self.direction,
            "parent_chat_name": self.parent_chat_name,
            "parent_chat_id": self.parent_chat_id,
            "encrypted_chat_name": self.encrypted_chat_name,
            "chat_name_nonce": self.chat_name_nonce,
            "system_hit_time": self.system_hit_time,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
