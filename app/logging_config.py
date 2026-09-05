"""Centralized logging configuration module."""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler


def setup_logging(log_level: str = "INFO", log_file_path: str = "logs/bot.log") -> logging.Logger:
    """Configure root logger with stream handler (stdout) and rotating file handler."""
    log_dir = os.path.dirname(log_file_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Stream Handler (stdout for Docker/Systemd)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(numeric_level)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    # Rotating File Handler (Max 10MB per file, keep 5 backups)
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Reduce noisy libraries log
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)

    logger = logging.getLogger("cloudphonefree_bot")
    logger.info("Logging configured successfully with level: %s", log_level.upper())
    return logger
