"""
Test configuration and fixtures.
"""

import pytest
from fastapi.testclient import TestClient

from benchmark.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def sample_post_data():
    """Sample post data for testing."""
    return {
        "title": "Test Post",
        "content": "This is a test post content.",
        "author_email": "test@example.com"
    }