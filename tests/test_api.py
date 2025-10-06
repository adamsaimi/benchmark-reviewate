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
        "author_email": "test@example.com",
        "author_name": "Test User"
    }
    
    response = client.post("/posts/", json=post_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["title"] == post_data["title"]
    assert data["content"] == post_data["content"]
    assert data["author"]["email"] == post_data["author_email"]
    assert data["author"]["name"] == post_data["author_name"]
    assert "id" in data
    assert "author_id" in data
    assert "created_at" in data


def test_create_post_without_author_name(client):
    """Test creating a post without author name (should use email prefix)."""
    post_data = {
        "title": "Test Post No Name",
        "content": "Content without author name.",
        "author_email": "noname@example.com"
    }
    
    response = client.post("/posts/", json=post_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["author"]["email"] == post_data["author_email"]
    assert data["author"]["name"] == "noname"  # Email prefix


def test_create_post_with_existing_user(client):
    """Test creating posts with same email uses same user."""
    post_data1 = {
        "title": "First Post",
        "content": "First content.",
        "author_email": "same@example.com",
        "author_name": "Same User"
    }
    
    post_data2 = {
        "title": "Second Post",
        "content": "Second content.",
        "author_email": "same@example.com"
    }
    
    response1 = client.post("/posts/", json=post_data1)
    response2 = client.post("/posts/", json=post_data2)
    
    assert response1.status_code == 201
    assert response2.status_code == 201
    
    data1 = response1.json()
    data2 = response2.json()
    
    # Both posts should have the same author_id
    assert data1["author_id"] == data2["author_id"]


def test_get_all_posts(client):
    """Test getting all posts."""
    # First create a post
    post_data = {
        "title": "Another Test Post",
        "content": "Another test content.",
        "author_email": "another@example.com",
        "author_name": "Another User"
    }
    client.post("/posts/", json=post_data)
    
    # Then get all posts
    response = client.get("/posts/")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # Verify each post has author information
    for post in data:
        assert "author" in post
        assert "email" in post["author"]


def test_get_post_by_id(client):
    """Test getting a specific post by ID."""
    # First create a post
    post_data = {
        "title": "Specific Test Post",
        "content": "Specific test content.",
        "author_email": "specific@example.com",
        "author_name": "Specific User"
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
    assert data["author"]["email"] == post_data["author_email"]


def test_get_nonexistent_post(client):
    """Test getting a non-existent post returns 404."""
    response = client.get("/posts/99999")
    assert response.status_code == 404
    
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Post not found"


def test_get_all_users(client):
    """Test getting all users."""
    # Create posts with different users
    client.post("/posts/", json={
        "title": "Post 1",
        "content": "Content 1",
        "author_email": "user1@example.com",
        "author_name": "User One"
    })
    client.post("/posts/", json={
        "title": "Post 2",
        "content": "Content 2",
        "author_email": "user2@example.com",
        "author_name": "User Two"
    })
    
    response = client.get("/users/")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


def test_get_user_by_email(client):
    """Test getting a specific user by email."""
    # Create a post (which creates a user)
    post_data = {
        "title": "User Test Post",
        "content": "Content for user test.",
        "author_email": "getuser@example.com",
        "author_name": "Get User"
    }
    client.post("/posts/", json=post_data)
    
    # Get the user by email
    response = client.get("/users/getuser@example.com")
    assert response.status_code == 200
    
    data = response.json()
    assert data["email"] == "getuser@example.com"
    assert data["name"] == "Get User"
    assert "id" in data
    assert "created_at" in data


def test_get_nonexistent_user(client):
    """Test getting a non-existent user returns 404."""
    response = client.get("/users/nonexistent@example.com")
    assert response.status_code == 404
    
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "User not found"


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


def test_get_post_invalid_id(client):
    """Test getting a post with invalid ID (negative or zero)."""
    # Test with negative ID
    response = client.get("/posts/-1")
    assert response.status_code == 422
    
    # Test with zero
    response = client.get("/posts/0")
    assert response.status_code == 422