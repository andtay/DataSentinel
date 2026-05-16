"""
Logging configuration using Loguru.

This module sets up structured logging with:
- Console and file handlers
- JSON and text formats
- Log rotation
- Integration with FastAPI
"""

import sys
from pathlib import Path

from loguru import logger

from config.settings import get_settings


def setup_logging(level: str = "INFO", log_file: str | None = None) -> None:
    """
    Configure Loguru with appropriate handlers and formats.
    
    This function should be called once at application startup.
    It configures logging based on settings from the environment or provided parameters.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
    """
    settings = get_settings()
    
    # Override settings with provided parameters
    log_level = level or settings.log_level
    log_file_path = log_file or settings.log_file
    
    # Remove default handler
    logger.remove()
    
    # Console handler
    if settings.log_format == "json":
        logger.add(
            sys.stderr,
            format="{message}",
            level=log_level,
            serialize=True,  # JSON format
        )
    else:
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=log_level,
            colorize=True,
        )
    
    # File handler (if configured)
    if log_file_path:
        log_file_obj = Path(log_file_path)
        log_file_obj.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            str(log_file_obj),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=log_level,
            rotation="500 MB",  # Rotate when file reaches 500MB
            retention="10 days",  # Keep logs for 10 days
            compression="zip",  # Compress rotated logs
            serialize=settings.log_format == "json",
        )
    
    logger.info(f"Logging configured: level={log_level}, format={settings.log_format}")


def get_logger(name: str):
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Module name (typically __name__)
        
    Returns:
        Logger instance bound to the module name
    """
    return logger.bind(name=name)

# Made with Bob
