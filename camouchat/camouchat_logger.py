"""
Shared Resources Module for CamouChat
Supports separate loggers, contextual logging, and JSON formatting.
"""

import json
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Any

from colorlog import ColoredFormatter

from camouchat.directory import DirectoryManager

try:
    from concurrent_log_handler import ConcurrentRotatingFileHandler
except ImportError:
    ConcurrentRotatingFileHandler = RotatingFileHandler  # type: ignore[assignment, misc]


class JSONFormatter(logging.Formatter):
    """Formatter that outputs log records as JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        """
        Formats the LogRecord as a JSON string, including standard fields
        and any custom contextual information like profile_id.
        """
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add contextual information if available
        if hasattr(record, "profile_id"):
            log_record["profile_id"] = record.profile_id
        if hasattr(record, "process_id"):
            log_record["process_id"] = record.process_id

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)


class CamouChatLoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that injects contextual information like profile_id and process_id.
    """

    def process(self, msg: Any, kwargs: Any) -> tuple[Any, Any]:
        """
        Process the logging message and keyword arguments passed to the logging call
        to insert contextual information (extra).
        """
        extra = dict(self.extra) if self.extra else {}
        if "extra" in kwargs:
            extra.update(kwargs["extra"])
        kwargs["extra"] = extra
        return msg, kwargs


# ------ Logger Configs ---------
logger = logging.getLogger("camouchat")
logger.setLevel(logging.DEBUG)
logger.propagate = False  # Avoid duplication


# ------ Logger Handlers --------
def _has_stream_handler(lg: logging.Logger):
    return any(
        isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        for h in lg.handlers
    )


def _has_file_handler(lg: logging.Logger):
    return any(isinstance(h, logging.FileHandler) for h in lg.handlers)


# We use contextual formatting
LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | [%(profile_id)s][%(process_id)s] | %(name)s | %(message)s"
)
CONSOLE_FORMAT = (
    "%(log_color)s%(asctime)s | %(levelname)s | [%(profile_id)s][%(process_id)s] | %(message)s"
)

# -------------------------------
# Console handler
# -------------------------------
console_formatter = ColoredFormatter(
    CONSOLE_FORMAT,
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    },
)

console_handler = logging.StreamHandler()
console_handler.setFormatter(console_formatter)

if not _has_stream_handler(logger):
    logger.addHandler(console_handler)

# -------------------------------
# File handler with rotation
# -------------------------------
if not _has_file_handler(logger):
    log_file = DirectoryManager().get_error_trace_file()
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    file_handler = ConcurrentRotatingFileHandler(log_file, maxBytes=20 * 1024 * 1024, backupCount=3)

    file_formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

# -------------------------------
# Browser Logger Setup
# -------------------------------
_browser_logger = logging.getLogger("camouchat.browser")
_browser_logger.setLevel(logging.INFO)
_browser_logger.propagate = False

if not _has_stream_handler(_browser_logger):
    _browser_logger.addHandler(console_handler)

if not _has_file_handler(_browser_logger):
    b_log_file = DirectoryManager().get_browser_log_file()
    os.makedirs(os.path.dirname(b_log_file), exist_ok=True)

    b_file_handler = ConcurrentRotatingFileHandler(
        b_log_file, maxBytes=20 * 1024 * 1024, backupCount=3
    )
    b_file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    _browser_logger.addHandler(b_file_handler)

# -------------------------------
# Global wrapped instances
# -------------------------------
# By default, use GLOBAL for profile if not specified to maintain backward compatibility.
camouchatLogger = CamouChatLoggerAdapter(
    logger, {"profile_id": "GLOBAL", "process_id": os.getpid()}
)
browser_logger = CamouChatLoggerAdapter(
    _browser_logger, {"profile_id": "GLOBAL", "process_id": os.getpid()}
)

_adapter_cache: dict[str, CamouChatLoggerAdapter] = {"GLOBAL": camouchatLogger}
_browser_adapter_cache: dict[str, CamouChatLoggerAdapter] = {"GLOBAL": browser_logger}


def get_profile_logger(profile_id: str) -> CamouChatLoggerAdapter:
    """Returns a logger adapter configured for a specific profile_id."""
    if profile_id not in _adapter_cache:
        _adapter_cache[profile_id] = CamouChatLoggerAdapter(
            logger, {"profile_id": profile_id, "process_id": os.getpid()}
        )
    return _adapter_cache[profile_id]


def get_browser_profile_logger(profile_id: str) -> CamouChatLoggerAdapter:
    """Returns a browser logger adapter configured for a specific profile_id."""
    if profile_id not in _browser_adapter_cache:
        _browser_adapter_cache[profile_id] = CamouChatLoggerAdapter(
            _browser_logger, {"profile_id": profile_id, "process_id": os.getpid()}
        )
    return _browser_adapter_cache[profile_id]
