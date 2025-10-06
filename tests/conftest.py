"""
Test configuration and fixtures.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from benchmark.main import app
from benchmark.models import Base
from benchmark.database import get_db
from benchmark.config import settings


# Create test database engine
engine = create_engine(
    settings.TEST_DATABASE_URL,
    pool_pre_ping=True
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_post_data():
    """Sample post data for testing."""
    return {
        "title": "Test Post",
        "content": "This is a test post content.",
        "author_email": "test@example.com"
    }