"""
Unit tests for the post service.
"""

import pytest
from datetime import datetime

from benchmark.services.post_service import PostService, PostNotFoundException
from benchmark.schemas import PostCreate


def test_create_post(db_session):
    """Test creating a post through the service."""
    service = PostService(db_session)
    post_data = PostCreate(
        title="Service Test Post",
        content="Test content from service",
        author_email="service@example.com"
    )
    
    result = service.create_post(post_data)
    
    assert result.title == post_data.title
    assert result.content == post_data.content
    assert result.author_email == post_data.author_email
    assert result.id > 0
    assert isinstance(result.created_at, datetime)


def test_get_post_by_id(db_session):
    """Test retrieving a post by ID."""
    service = PostService(db_session)
    
    # Create a post first
    post_data = PostCreate(
        title="Retrievable Post",
        content="Content for retrieval test",
        author_email="retrieve@example.com"
    )
    created_post = service.create_post(post_data)
    
    # Then retrieve it
    retrieved_post = service.get_post_by_id(created_post.id)
    
    assert retrieved_post.id == created_post.id
    assert retrieved_post.title == created_post.title
    assert retrieved_post.content == created_post.content
    assert retrieved_post.author_email == created_post.author_email


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
        author_email="first@example.com"
    )
    post2_data = PostCreate(
        title="Second Post",
        content="Second content",
        author_email="second@example.com"
    )
    
    created_post1 = service.create_post(post1_data)
    created_post2 = service.create_post(post2_data)
    
    # Retrieve all posts
    all_posts = service.get_all_posts()
    
    assert len(all_posts) >= 2
    post_ids = [post.id for post in all_posts]
    assert created_post1.id in post_ids
    assert created_post2.id in post_ids