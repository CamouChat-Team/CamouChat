"""
Generic SQLAlchemy storage implementation supporting multiple databases.
Uses async operations for non-blocking performance.
"""

from __future__ import annotations

import asyncio
from logging import Logger, LoggerAdapter

from camouchat.WhatsApp.api.models import MessageModelAPI
from camouchat.camouchat_logger import camouchatLogger
from typing import List, Dict, Any, Optional, Sequence, Union

from sqlalchemy import select, exists
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from camouchat.BrowserManager.profile_info import ProfileInfo
from camouchat.Exceptions.base import StorageError
from camouchat.Interfaces.message_interface import MessageInterface
from camouchat.Interfaces.storage_interface import StorageInterface
from camouchat.StorageDB.models import Base, Message
from camouchat.WhatsApp.models import Message as WhatsAppMessage

class SQLAlchemyStorage(StorageInterface):
    """
    Generic SQLAlchemy storage implementation for MessageInterface data.

    Features:
    - Async queue-based batch insertion
    - Background writer task for performance
    - Support for SQLite, PostgreSQL, MySQL via connection string
    - Generic message storage (works with any MessageInterface implementation)

    Connection string examples:
    - SQLite: sqlite+aiosqlite:///path/to/messages.db
    - PostgreSQL: postgresql+asyncpg://user:pass@host/db
    - MySQL: mysql+aiomysql://user:pass@host/db
    """

    _instances: Dict[str, SQLAlchemyStorage] = {}
    _initialized: bool = False

    def __new__(cls, *args, **kwargs) -> SQLAlchemyStorage:
        database_url = kwargs.get("database_url") or (
            args[2] if len(args) > 2 else "sqlite+aiosqlite:///messages.db"
        )
        if database_url not in cls._instances:
            instance = super(SQLAlchemyStorage, cls).__new__(cls)
            cls._instances[database_url] = instance
        return cls._instances[database_url]

    def __init__(
        self,
        queue: asyncio.Queue,
        log: Optional[Union[Logger, LoggerAdapter]] = None,
        database_url: str = "sqlite+aiosqlite:///messages.db",
        batch_size: int = 50,
        flush_interval: float = 2.0,
        echo: bool = False,
    ) -> None:
        if hasattr(self, "_initialized") and self._initialized:
            return
        """
        Initialize SQLAlchemy storage.

        Args:
            queue: Async queue for message batching
            log: Logger instance
            database_url: SQLAlchemy database URL
            batch_size: Max messages before auto-flush
            flush_interval: Seconds before auto-flush even if batch not full
            echo: Enable SQL query logging (for debugging)
        """
        super().__init__(queue=queue, log=log)

        self.database_url = database_url
        self._initialized = True
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.echo = echo

        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self._writer_task: Optional[asyncio.Task] = None
        self._running = False

    @classmethod
    def from_profile(
        cls,
        profile: ProfileInfo,
        queue: asyncio.Queue,
        log: Optional[Union[Logger, LoggerAdapter]] = None,
        batch_size: int = 50,
        flush_interval: float = 2.0,
    ) -> "SQLAlchemyStorage":
        """
        Create storage from ProfileInfo.

        Args:
            profile: ProfileInfo from ProfileManager
            queue: Async queue
            log: Logger
            batch_size: Batch size
            flush_interval: Flush interval

        Returns:
            Configured SQLAlchemyStorage instance
        """
        database_url = profile.database_url
        return cls(
            queue=queue,
            log=log or camouchatLogger,
            database_url=database_url,
            batch_size=batch_size,
            flush_interval=flush_interval,
        )

    async def init_db(self, **kwargs) -> None:
        """Initialize SQLAlchemy engine and session factory."""
        try:
            is_sqlite = self.database_url.startswith("sqlite")
            engine_kwargs: dict = {
                "echo": self.echo,
                "pool_pre_ping": True,
            }
            if not is_sqlite:
                engine_kwargs.update(
                    {
                        "pool_recycle": 3600,
                        "pool_size": 5,
                        "max_overflow": 10,
                        "pool_timeout": 30,
                    }
                )

            self._engine = create_async_engine(self.database_url, **engine_kwargs)

            # Create session factory
            self._session_factory = async_sessionmaker(
                self._engine, class_=AsyncSession, expire_on_commit=False
            )

            self.log.info(f"SQLAlchemy engine initialized: {self.database_url}")
        except Exception as e:
            raise StorageError(f"Failed to initialize database: {e}") from e

    async def create_table(self, **kwargs) -> None:
        """Create tables if not exists."""
        if not self._engine:
            raise StorageError("Database not initialized. Call init_db() first.")

        try:
            async with self._engine.begin() as conn:  # type: ignore
                await conn.run_sync(Base.metadata.create_all)
            self.log.info("Tables created/verified.")
        except Exception as e:
            raise StorageError(f"Failed to create tables: {e}") from e

    async def _migrate_add_encryption_columns(self) -> None:
        """
        Safe migration for users upgrading from older versions.

        SQLAlchemy's create_all() only creates missing tables — it does NOT add
        new columns to existing tables. Users who already have a messages.db
        would get OperationalError without this migration.

        Uses 'ALTER TABLE ... ADD COLUMN' with silent error swallowing because
        SQLite does not support 'IF NOT EXISTS' on ADD COLUMN (pre-3.37.0).
        """
        from sqlalchemy import text

        migration_sqls = [
            "ALTER TABLE messages ADD COLUMN encryption_nonce VARCHAR(255)",
        ]
        if not self._engine:
            return

        async with self._engine.begin() as conn:  # type: ignore
            for sql in migration_sqls:
                try:
                    await conn.execute(text(sql))
                    self.log.debug(f"Migration applied: {sql}")
                except Exception:
                    pass  # Column already exists — expected on fresh installs

    async def start_writer(self, **kwargs) -> None:
        """Start background task to consume queue and write batches."""
        if self._writer_task and not self._writer_task.done():
            self.log.warning("Writer task already running.")
            return

        self._running = True
        self._writer_task = asyncio.create_task(self._writer_loop())
        self.log.info("Background writer started.")

    async def _writer_loop(self) -> None:
        """Background loop that consumes queue and writes batches."""
        batch: List[MessageInterface] = []
        last_flush = asyncio.get_event_loop().time()

        while self._running:
            try:
                try:
                    msg = await asyncio.wait_for(self.queue.get(), timeout=self.flush_interval)
                    if isinstance(msg, list):
                        batch.extend(msg)
                    else:
                        batch.append(msg)
                    self.queue.task_done()
                except asyncio.TimeoutError:
                    pass

                current_time = asyncio.get_event_loop().time()
                should_flush = len(batch) >= self.batch_size or (
                    batch and current_time - last_flush >= self.flush_interval
                )

                if should_flush and batch:
                    await self._insert_batch_internally(batch)
                    batch.clear()
                    last_flush = current_time

            except Exception as e:
                self.log.error(f"Writer loop error: {e}", exc_info=True)
                await asyncio.sleep(1)

        # Flush remaining messages on shutdown
        if batch:
            await self._insert_batch_internally(batch)

    async def enqueue_insert(self, msgs: Sequence[MessageInterface], **kwargs) -> None:
        """Add messages to queue for batch insertion."""
        if not msgs:
            return

        for msg in msgs:
            await self.queue.put(msg)

        self.log.debug(f"Enqueued {len(msgs)} messages for insertion.")

    async def _insert_batch_internally(self, msgs: Sequence[MessageInterface], **kwargs) -> None:
        """Insert batch of messages into database."""
        if not self._session_factory:
            raise StorageError("Database not initialized.")

        if not msgs:
            return

        # Convert messages to Message models
        message_models = []
        for msg in msgs:
            try:
                if isinstance(msg, WhatsAppMessage):
                    model = SQLAlchemyStorage._message_to_model(msg=msg)
                elif isinstance(msg, MessageModelAPI):
                    model = SQLAlchemyStorage._msg_api_to_model(msg=msg)
                else:
                    # Fallback duck-typing attempt
                    model = SQLAlchemyStorage._message_to_model(msg=msg)  # type: ignore
                message_models.append(model)
            except Exception as e:
                self.log.warning(f"Failed to convert message: {e}")
                continue

        if not message_models:
            return

        # Insert batch
        session_factory = self._session_factory
        if session_factory is None:
            raise StorageError("Database not initialized.")

        session_factory = self._get_session_factory()
        async with session_factory() as session:
            try:
                session.add_all(message_models)
                await session.commit()
                self.log.debug(f"Inserted {len(message_models)} messages.")
            except IntegrityError:
                await session.rollback()
                success_count = 0
                for model in message_models:
                    try:
                        session_factory = self._get_session_factory()
                        async with session_factory() as single_session:
                            single_session.add(model)
                            await single_session.commit()
                            success_count += 1
                    except IntegrityError:
                        continue  # Skip duplicate
                    except Exception as e:
                        self.log.warning(f"Failed to insert message {model.id_serialized}: {e}")

                self.log.debug(
                    f"Inserted {success_count}/{len(message_models)} messages (some duplicates)."
                )
            except Exception as e:
                await session.rollback()
                self.log.error(f"Batch insert failed: {e}", exc_info=True)
                raise StorageError(f"Batch insert failed: {e}") from e

    @staticmethod
    def _message_to_model(msg: WhatsAppMessage) -> Message:
        """Convert MessageInterface to Message model."""
        msg_id = getattr(msg, "id_serialized", "unknown")
        body = getattr(msg, "body", "")
        msgtype = getattr(msg, "msgtype", None)
        fromme = getattr(msg, "fromMe", None)
        timestamp = getattr(msg, "timestamp", 0.0)
        encryption_nonce = getattr(msg, "encryption_nonce", None)
        from_chat = getattr(msg, "from_chat", None)
        from_chat_id = ""
        if from_chat:
            from_chat_id = getattr(from_chat, "id_serialized", "")

        return Message(
            id_serialized=str(msg_id),
            body=str(body) if body else "",
            encryption_nonce=encryption_nonce,
            msgtype=str(msgtype) if msgtype else None,
            fromMe=fromme,
            chat_id=str(from_chat_id),
            timestamp=float(timestamp),
        )

    @staticmethod
    def _msg_api_to_model(msg: MessageModelAPI) -> Message:
        """Convert MessageModelAPI to unified Message DB model."""
        msg_id = getattr(msg, "id_serialized", "unknown")
        body = getattr(msg, "body", "")
        msgtype = getattr(msg, "msgtype", None)
        fromme = getattr(msg, "fromMe", None)
        timestamp = getattr(msg, "timestamp", 0.0)
        encryption_nonce = getattr(msg, "encryption_nonce", None)
        chat_id = getattr(msg, "jid_From", "")

        return Message(
            id_serialized=str(msg_id),
            body=str(body) if body else "",
            encryption_nonce=encryption_nonce,
            msgtype=str(msgtype) if msgtype else None,
            fromMe=fromme,
            chat_id=str(chat_id),
            timestamp=float(timestamp),
        )

    def check_message_if_exists(self, msg_id: str, **kwargs) -> bool:
        """
        Check if message exists by ID (synchronous for quick checks).
        Note: This uses asyncio.run() internally, not recommended in async context.
        Use check_message_if_exists_async() in async code.
        """
        try:
            return asyncio.run(self.check_message_if_exists_async(msg_id))
        except Exception as e:
            self.log.error(f"Existence check failed: {e}")
            return False

    async def check_message_if_exists_async(self, msg_id: str, **kwargs) -> bool:
        """Async version of existence check."""
        if not self._session_factory:
            return False

        session_factory = self._get_session_factory()
        async with session_factory() as session:
            try:
                stmt = select(exists().where(Message.id_serialized == msg_id))
                result = await session.execute(stmt)
                return result.scalar() or False
            except Exception as e:
                self.log.error(f"Async existence check failed: {e}")
                return False

    def get_all_messages(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Retrieve all messages from DB (synchronous).
        Uses asyncio.run() internally, not recommended in async context.
        """
        try:
            return asyncio.run(self.get_all_messages_async(**kwargs))
        except Exception as e:
            self.log.error(f"Get all messages failed: {e}")
            return []

    async def get_all_messages_async(self, **kwargs) -> List[Dict[str, Any]]:
        """Async version of get all messages."""
        if not self._session_factory:
            return []

        limit = kwargs.get("limit", 1000)
        offset = kwargs.get("offset", 0)

        session_factory = self._get_session_factory()
        async with session_factory() as session:
            try:
                stmt = select(Message).order_by(Message.id.desc()).limit(limit).offset(offset)
                result = await session.execute(stmt)
                messages = result.scalars().all()
                return [msg.to_dict() for msg in messages]
            except Exception as e:
                self.log.error(f"Async get all messages failed: {e}")
                return []

    async def get_messages_by_chat(self, chat_id: str, **kwargs) -> List[Dict[str, Any]]:
        """Get messages filtered by chat id (or HMAC digest if encryption is enabled)."""
        if not self._session_factory:
            return []

        limit = kwargs.get("limit", 100)
        session_factory = self._get_session_factory()

        async with session_factory() as session:
            try:
                stmt = (
                    select(Message)
                    .where(Message.chat_id == chat_id)
                    .order_by(Message.id.desc())
                    .limit(limit)
                )
                result = await session.execute(stmt)
                messages = result.scalars().all()
                return [msg.to_dict() for msg in messages]
            except Exception as e:
                self.log.error(f"Get messages by chat failed: {e}")
                return []

    async def get_messages_by_ids_async(self, message_ids: list[str]) -> List[Dict[str, Any]]:
        """Retrieve specific messages by their serialized IDs."""
        if not self._session_factory or not message_ids:
            return []

        session_factory = self._get_session_factory()
        async with session_factory() as session:
            try:
                stmt = select(Message).where(Message.id_serialized.in_(message_ids))
                result = await session.execute(stmt)
                messages = result.scalars().all()
                return [msg.to_dict() for msg in messages]
            except Exception as e:
                self.log.error(f"Failed to fetch messages by IDs: {e}")
                return []

    async def execute_raw_sql(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a raw SQL query and return results as a list of dictionaries.
        Supports both SELECT and DML (INSERT/UPDATE/DELETE).
        """
        from sqlalchemy import text

        if not self._session_factory:
            return []

        session_factory = self._get_session_factory()
        async with session_factory() as session:
            try:
                stmt = text(query)
                result = await session.execute(stmt, params or {})

                # If query returns rows (like SELECT), convert to dicts
                if result.returns_rows:
                    return [dict(row._mapping) for row in result.all()]

                # For DML, commit and return empty
                await session.commit()
                return []
            except Exception as e:
                self.log.error(f"Raw SQL execution failed: {e}")
                await session.rollback()
                return []

    async def get_decrypted_messages_async(
        self,
        key: bytes,
        limit: int = 1000,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all messages and decrypt body + chat name on-the-fly.

        This is the primary way a user retrieves readable messages when
        encryption is enabled.  Pass the key from
        ``ProfileManager.get_key(platform, profile_id)``.

        Args:
            key:    Raw 32-byte AES-256 key (from ProfileManager.get_key).
            limit:  Max rows to fetch.
            offset: Pagination offset.

            List of dicts identical to ``to_dict()`` but with:
            - ``body`` populated with decrypted plaintext (or original value
              when the row was stored without encryption).

        Example::

            key = manager.get_key(Platform.WHATSAPP, "my_profile")
            rows = await storage.get_decrypted_messages_async(key)
        """
        import base64 as _b64
        from camouchat.Encryption import MessageDecryptor

        rows = await self.get_all_messages_async(limit=limit, offset=offset)

        decryptor = MessageDecryptor(key)

        result = []
        for row in rows:
            out = dict(row)

            # Decrypt message body
            enc_nonce = row.get("encryption_nonce")
            if enc_nonce and out.get("body"):
                try:
                    nonce_bytes = _b64.b64decode(enc_nonce)
                    cipher_bytes = _b64.b64decode(out["body"])
                    msg_id = row.get("id_serialized", "")
                    out["body"] = decryptor.decrypt_message(
                        nonce_bytes, cipher_bytes, msg_id or None
                    )
                except Exception as e:
                    self.log.warning(f"Failed to decrypt message {row.get('id_serialized')}: {e}")
                    out["body"] = "<decryption failed>"

            result.append(out)

        return result

    def _get_session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            raise StorageError("Database not initialized.")
        return self._session_factory

    async def close_db(self, **kwargs) -> None:
        """Close connection and stop writer."""
        self._running = False

        if self._writer_task:
            self._writer_task.cancel()
            try:
                await self._writer_task
            except asyncio.CancelledError:
                pass
            self._writer_task = None

        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            self.log.info("Database connection closed.")

    async def start(self, **kwargs) -> None:
        """Start database and background writer."""
        await self.init_db()
        await self.create_table()
        await self._migrate_add_encryption_columns()
        await self.start_writer()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_db()
        return False
