"""
Main application entry point for the Benchmark API.

This module initializes the FastAPI application, configures routing,
and provides the main entry point for the API server.
"""

from typing import Dict

from fastapi import FastAPI

from benchmark.config import API_DESCRIPTION, API_TITLE, API_VERSION, HEALTH_CHECK_MESSAGE
from benchmark.routers import posts

# Initialize the main FastAPI application
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION
)

# Include the posts router for all post-related endpoints
app.include_router(posts.router)


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