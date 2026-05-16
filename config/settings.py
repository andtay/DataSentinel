"""
Settings management using Pydantic Settings.

This module provides centralized configuration management with:
- Environment variable loading
- Type validation
- Default values
- Documentation
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    Settings can be configured via:
    1. Environment variables (highest priority)
    2. .env file
    3. Default values (lowest priority)
    """
    
    # Logging Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["json", "text"] = "json"
    log_file: Path | None = None
    
    # API Configuration
    default_timeout: int = 30
    max_retries: int = 3
    retry_backoff_factor: float = 2.0
    
    # Generation Configuration
    output_dir: Path = Path("./output")
    template_dir: Path = Path("./templates")
    
    # Code Style Configuration
    line_length: int = 88
    use_black: bool = True
    use_isort: bool = True
    
    # Optional Authentication (for parsing remote APIs)
    api_key: str | None = None
    bearer_token: str | None = None
    oauth2_client_id: str | None = None
    oauth2_client_secret: str | None = None
    oauth2_token_url: str | None = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if not self.template_dir.exists():
            # Template dir should exist, but don't create it automatically
            pass


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    This function uses lru_cache to ensure settings are loaded only once
    and reused throughout the application lifecycle.
    
    Returns:
        Settings instance
    """
    return Settings()

# Made with Bob
