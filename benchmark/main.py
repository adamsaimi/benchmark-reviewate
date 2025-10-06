"""
Main application entry point for the Benchmark API.

This module initializes the FastAPI application, configures routing,
and provides the main entry point for the API server.
"""

from typing import Dict

from fastapi import FastAPI

from benchmark.config import settings, HEALTH_CHECK_MESSAGE
from benchmark.routers import posts

# Initialize the main FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION
)

# Include the posts router for all post-related endpoints
app.include_router(posts.router)

# Include the users router for all user-related endpoints
app.include_router(posts.user_router)


@app.get("/")
def read_root() -> Dict[str, str]:
    """
    Health check endpoint.
    
    Provides a simple health check to verify that the API is running
    and responding to requests.
    
    Returns:
        A simple status dictionary indicating the API is operational
    """
    return {"status": HEALTH_CHECK_MESSAGE}