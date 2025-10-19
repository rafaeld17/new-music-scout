"""
Configuration management for the Music Scout application.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "sqlite:///./music_scout.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    allowed_origins: str = ""  # Comma-separated list of allowed origins for CORS

    # External APIs
    musicbrainz_api_url: str = "https://musicbrainz.org/ws/2"
    spotify_client_id: Optional[str] = None
    spotify_client_secret: Optional[str] = None

    # Email
    email_service: Optional[str] = None
    email_api_key: Optional[str] = None

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()