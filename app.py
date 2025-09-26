"""
Application entry point.

This module serves as the entry point for the FastAPI application,
importing the app from the benchmark package.
"""

from benchmark.main import app

# This allows uvicorn to find the app instance
__all__ = ["app"]