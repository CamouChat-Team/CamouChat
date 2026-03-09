"""
Custom logging module for tweakio-sdk.
Supports separate loggers for application and browser events, 
contextual logging, and JSON formatting.
"""
import logging
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from colorlog import ColoredFormatter
except ImportError:
    ColoredFormatter = None

try:
    from concurrent_log_handler import ConcurrentRotatingFileHandler
except ImportError:
    from logging.handlers import RotatingFileHandler as ConcurrentRotatingFileHandler

from src.directory import DirectoryManager

class JSONFormatter(logging.Formatter):
    """Formatter that outputs log records as JSON objects."""
    def format(self, record: logging.LogRecord) -> str:
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

class TweakioLoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that injects contextual information like profile_id and process_id.
    """
    def process(self, msg: Any, kwargs: Any) -> tuple[Any, Any]:
        extra = dict(self.extra) if self.extra else {}
        if "extra" in kwargs:
            extra.update(kwargs["extra"])
        kwargs["extra"] = extra
        return msg, kwargs

class TweakioLogger:
    """
    Centralized logger management for Tweakio SDK.
    Handles general application logs, specialized browser logs, 
    contextual logging, and various output formats.
    """
    _instances: Dict[str, logging.Logger] = {}
    
    # Default configurations
    MAX_BYTES = 20 * 1024 * 1024  # 20 MB
    BACKUP_COUNT = 3
    # Updated format to include contextual fields
    LOG_FORMAT = "%(asctime)s | %(levelname)s | [%(profile_id)s][%(process_id)s] | %(name)s | %(message)s"
    CONSOLE_FORMAT = "%(log_color)s%(asctime)s | %(levelname)s | [%(profile_id)s][%(process_id)s] | %(name)s | %(message)s"

    @classmethod
    def get_logger(
        cls, 
        name: str = "tweakio", 
        log_type: str = "app",
        level: int = logging.INFO,
        profile_id: str = "N/A",
        use_json: bool = False
    ) -> logging.LoggerAdapter:
        """
        Get or create a logger instance wrapped in an adapter for contextual logging.
        
        Args:
            name: The name of the logger.
            log_type: 'app' for general logs, 'browser' for browser-specific logs.
            level: Logging level (default: logging.INFO).
            profile_id: Optional profile identifier for contextual logging.
            use_json: Whether to use JSON formatting for file logs.
            
        Returns:
            A configured logging.LoggerAdapter instance.
        """
        logger_key = f"{log_type}:{name}:{use_json}"
        if logger_key not in cls._instances:
            logger = logging.getLogger(name)
            logger.setLevel(level)
            logger.propagate = False

            # Determine file path based on log type
            dm = DirectoryManager()
            if log_type == "browser":
                log_file = dm.get_browser_log_file()
            else:
                log_file = dm.get_error_trace_file()

            # Add handlers if they don't exist
            if not logger.handlers:
                # Console Handler
                cls._add_console_handler(logger)
                # File Handler
                cls._add_file_handler(logger, log_file, use_json)

            cls._instances[logger_key] = logger

        # Wrap in adapter to inject profile_id and process_id
        return TweakioLoggerAdapter(
            cls._instances[logger_key], 
            {"profile_id": profile_id, "process_id": os.getpid()}
        )

    @classmethod
    def _add_console_handler(cls, logger: logging.Logger) -> None:
        """Adds a console handler to the logger."""
        if ColoredFormatter:
            console_formatter = ColoredFormatter(
                cls.CONSOLE_FORMAT,
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'bold_red'
                }
            )
        else:
            console_formatter = logging.Formatter(cls.LOG_FORMAT)
            
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    @classmethod
    def _add_file_handler(cls, logger: logging.Logger, log_file: Path, use_json: bool) -> None:
        """Adds a concurrent rotating file handler to the logger."""
        os.makedirs(log_file.parent, exist_ok=True)
        
        # Use ConcurrentRotatingFileHandler for process-safe rotation
        file_handler = ConcurrentRotatingFileHandler(
            log_file,
            maxBytes=cls.MAX_BYTES,
            backupCount=cls.BACKUP_COUNT
        )
        
        file_formatter: logging.Formatter
        if use_json:
            file_formatter = JSONFormatter()
        else:
            file_formatter = logging.Formatter(cls.LOG_FORMAT)
            
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

# Initialize default loggers for backward compatibility
logger = TweakioLogger.get_logger("tweakio", "app")
browser_logger = TweakioLogger.get_logger("tweakio.browser", "browser")
