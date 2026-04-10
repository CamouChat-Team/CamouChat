"""
SQLAlchemy database models for message storage.
Supports SQLite, PostgreSQL, and MySQL.
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text
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
    id_serialized: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    # Message content
    body: Mapped[str] = mapped_column(Text, nullable=True)
    encryption_nonce: Mapped[str | None] = mapped_column(String(255), nullable=True)
    msgtype: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fromMe: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Chat relationship
    chat_id: Mapped[str] = mapped_column(String(255), nullable=False, default="", index=True)

    # Timing
    timestamp: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True
    )

    # Composite indexes for common queries
    __table_args__ = (Index("idx_chat_id_time", "chat_id", "created_at"),)

    def __repr__(self) -> str:
        return (
            f"<Message(id={self.id}, id_serialized='{self.id_serialized}', "
            f"fromMe={self.fromMe}, chat_id='{self.chat_id}')>"
        )

    def to_dict(self) -> dict:
        """Convert message to dictionary."""
        return {
            "id": self.id,
            "id_serialized": self.id_serialized,
            "body": self.body,
            "encryption_nonce": self.encryption_nonce,
            "msgtype": self.msgtype,
            "fromMe": self.fromMe,
            "chat_id": self.chat_id,
            "timestamp": self.timestamp,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
