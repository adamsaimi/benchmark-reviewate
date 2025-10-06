"""
Configuration settings for the Benchmark API.

This module contains configuration constants and settings
that can be easily modified without changing core business logic.
"""

from typing import Final
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Uses Pydantic Settings for automatic environment variable
    loading and validation.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://benchmark_user:benchmark_password@localhost:5432/benchmark_db"
    TEST_DATABASE_URL: str = "postgresql://benchmark_user:benchmark_password@localhost:5433/benchmark_test_db"
    
    # API Configuration
    API_TITLE: str = "Benchmark API"
    API_DESCRIPTION: str = "A pristine FastAPI application for managing blog posts"
    API_VERSION: str = "1.0.0"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000


# Create a global settings instance
settings = Settings()

# Post validation constraints
MIN_TITLE_LENGTH: Final[int] = 3
MAX_TITLE_LENGTH: Final[int] = 100
MAX_CONTENT_LENGTH: Final[int] = 10000

# HTTP status messages
POST_NOT_FOUND_MESSAGE: Final[str] = "Post not found"
HEALTH_CHECK_MESSAGE: Final[str] = "ok"