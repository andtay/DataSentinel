"""
Configuration management for DataSentinel.

This package handles all configuration including:
- Settings management with Pydantic
- Logging configuration with Loguru
- Environment variable loading
"""

from config.settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]

# Made with Bob
