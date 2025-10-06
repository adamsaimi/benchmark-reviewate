"""
Unit tests for the API endpoints.
"""

import pytest


def test_health_check(client):
    """Test the root health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_post(client):
    """Test creating a new post."""
    post_data = {
        "title": "Test Post",
        "content": "This is a test post content.",
        "author_email": "test@example.com"
    }
    
    response = client.post("/posts/", json=post_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["title"] == post_data["title"]
    assert data["content"] == post_data["content"]
    assert data["author_email"] == post_data["author_email"]
    assert "id" in data
    assert "created_at" in data


def test_get_all_posts(client):
    """Test getting all posts."""
    # First create a post
    post_data = {
        "title": "Another Test Post",
        "content": "Another test content.",
        "author_email": "another@example.com"
    }
    client.post("/posts/", json=post_data)
    
    # Then get all posts
    response = client.get("/posts/")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_post_by_id(client):
    """Test getting a specific post by ID."""
    # First create a post
    post_data = {
        "title": "Specific Test Post",
        "content": "Specific test content.",
        "author_email": "specific@example.com"
    }
    create_response = client.post("/posts/", json=post_data)
    created_post = create_response.json()
    post_id = created_post["id"]
    
    # Then get it by ID
    response = client.get(f"/posts/{post_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == post_id
    assert data["title"] == post_data["title"]


def test_get_nonexistent_post(client):
    """Test getting a non-existent post returns 404."""
    response = client.get("/posts/99999")
    assert response.status_code == 404
    
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Post not found"


def test_create_post_invalid_email(client):
    """Test creating a post with invalid email."""
    post_data = {
        "title": "Test Post",
        "content": "Content",
        "author_email": "invalid-email"
    }
    
    response = client.post("/posts/", json=post_data)
    assert response.status_code == 422  # Validation error


def test_create_post_title_too_short(client):
    """Test creating a post with title too short."""
    post_data = {
        "title": "Hi",  # Too short (min 3 chars)
        "content": "Content",
        "author_email": "test@example.com"
    }
    
    response = client.post("/posts/", json=post_data)
    assert response.status_code == 422


def test_create_post_title_too_long(client):
    """Test creating a post with title too long."""
    post_data = {
        "title": "x" * 101,  # Too long (max 100 chars)
        "content": "Content",
        "author_email": "test@example.com"
    }
    
    response = client.post("/posts/", json=post_data)
    assert response.status_code == 422