"""
Unit tests for the post service.
"""

import pytest
from datetime import datetime

from benchmark.services.post_service import PostService, PostNotFoundException, UserNotFoundException
from benchmark.schemas import PostCreate


def test_create_post(db_session):
    """Test creating a post through the service."""
    service = PostService(db_session)
    post_data = PostCreate(
        title="Service Test Post",
        content="Test content from service",
        author_email="service@example.com",
        author_name="Service User"
    )
    
    result = service.create_post(post_data)
    
    assert result.title == post_data.title
    assert result.content == post_data.content
    assert result.author.email == post_data.author_email
    assert result.author.name == post_data.author_name
    assert result.id > 0
    assert result.author_id > 0
    assert isinstance(result.created_at, datetime)


def test_create_post_with_existing_user(db_session):
    """Test creating a post with an existing user."""
    service = PostService(db_session)
    
    # Create first post (creates user)
    post_data1 = PostCreate(
        title="First Post",
        content="First content",
        author_email="existing@example.com",
        author_name="Existing User"
    )
    result1 = service.create_post(post_data1)
    
    # Create second post with same email (should reuse user)
    post_data2 = PostCreate(
        title="Second Post",
        content="Second content",
        author_email="existing@example.com"
    )
    result2 = service.create_post(post_data2)
    
    # Both posts should have the same author_id
    assert result1.author_id == result2.author_id
    assert result1.author.email == result2.author.email


def test_get_post_by_id(db_session):
    """Test retrieving a post by ID."""
    service = PostService(db_session)
    
    # Create a post first
    post_data = PostCreate(
        title="Retrievable Post",
        content="Content for retrieval test",
        author_email="retrieve@example.com",
        author_name="Retrieve User"
    )
    created_post = service.create_post(post_data)
    
    # Then retrieve it
    retrieved_post = service.get_post_by_id(created_post.id)
    
    assert retrieved_post.id == created_post.id
    assert retrieved_post.title == created_post.title
    assert retrieved_post.content == created_post.content
    assert retrieved_post.author.email == post_data.author_email


def test_get_post_by_id_not_found(db_session):
    """Test retrieving a non-existent post raises exception."""
    service = PostService(db_session)
    
    with pytest.raises(PostNotFoundException):
        service.get_post_by_id(99999)


def test_get_all_posts(db_session):
    """Test retrieving all posts."""
    service = PostService(db_session)
    
    # Create multiple posts
    post1_data = PostCreate(
        title="First Post",
        content="First content",
        author_email="first@example.com",
        author_name="First User"
    )
    post2_data = PostCreate(
        title="Second Post",
        content="Second content",
        author_email="second@example.com",
        author_name="Second User"
    )
    
    created_post1 = service.create_post(post1_data)
    created_post2 = service.create_post(post2_data)
    
    # Retrieve all posts
    all_posts = service.get_all_posts()
    
    assert len(all_posts) >= 2
    post_ids = [post.id for post in all_posts]
    assert created_post1.id in post_ids
    assert created_post2.id in post_ids


def test_get_user_by_email(db_session):
    """Test retrieving a user by email."""
    service = PostService(db_session)
    
    # Create a post (which creates a user)
    post_data = PostCreate(
        title="Test Post",
        content="Test content",
        author_email="usertest@example.com",
        author_name="User Test"
    )
    service.create_post(post_data)
    
    # Retrieve the user
    user = service.get_user_by_email("usertest@example.com")
    
    assert user.email == "usertest@example.com"
    assert user.name == "User Test"
    assert user.id > 0


def test_get_user_by_email_not_found(db_session):
    """Test retrieving a non-existent user raises exception."""
    service = PostService(db_session)
    
    with pytest.raises(UserNotFoundException):
        service.get_user_by_email("nonexistent@example.com")


def test_get_all_users(db_session):
    """Test retrieving all users."""
    service = PostService(db_session)
    
    # Create posts with different users
    post1_data = PostCreate(
        title="Post 1",
        content="Content 1",
        author_email="user1@example.com",
        author_name="User One"
    )
    post2_data = PostCreate(
        title="Post 2",
        content="Content 2",
        author_email="user2@example.com",
        author_name="User Two"
    )
    
    service.create_post(post1_data)
    service.create_post(post2_data)
    
    # Retrieve all users
    all_users = service.get_all_users()
    
    assert len(all_users) >= 2
    user_emails = [user.email for user in all_users]
    assert "user1@example.com" in user_emails
    assert "user2@example.com" in user_emails