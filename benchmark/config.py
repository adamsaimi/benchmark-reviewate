"""
Configuration settings for the Benchmark API.

This module contains configuration constants and settings
that can be easily modified without changing core business logic.
"""

from typing import Final

# API Configuration
API_TITLE: Final[str] = "Benchmark API"
API_DESCRIPTION: Final[str] = "A pristine FastAPI application for managing blog posts"
API_VERSION: Final[str] = "1.0.0"

# Post validation constraints
MIN_TITLE_LENGTH: Final[int] = 3
MAX_TITLE_LENGTH: Final[int] = 100
MAX_CONTENT_LENGTH: Final[int] = 10000

# HTTP status messages
POST_NOT_FOUND_MESSAGE: Final[str] = "Post not found"
HEALTH_CHECK_MESSAGE: Final[str] = "ok"