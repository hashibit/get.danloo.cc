"""Logging configuration utility."""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional

from ai_provider.config.settings import LoggingConfig


def setup_logging(config: LoggingConfig) -> logging.Logger:
    """Setup logging configuration based on settings."""

    # Get the root logger
    root_logger = logging.getLogger()

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Set log level
    log_level = getattr(logging, config.level.upper(), logging.INFO)
    root_logger.setLevel(log_level)

    # Create formatter
    formatter = logging.Formatter(config.format)

    # Console handler
    if config.enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler
    if config.enable_file:
        try:
            # Create log directory if it doesn't exist
            log_file_path = Path(config.file_path)
            log_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Use RotatingFileHandler for file size management
            file_handler = logging.handlers.RotatingFileHandler(
                filename=config.file_path,
                maxBytes=config.max_file_size,
                backupCount=config.backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except (OSError, PermissionError) as e:
            # If file logging fails due to permissions, log a warning and continue
            print(
                f"Warning: Cannot create log file {config.file_path} due to permission error: {e}"
            )

    # Ensure at least one handler exists
    if not root_logger.handlers:
        raise RuntimeError(
            "No logging handlers configured. At least one of console or file logging must be enabled and functional."
        )

    # Return a logger for the main module
    return logging.getLogger("main")


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)
