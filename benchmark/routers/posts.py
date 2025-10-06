"""
HTTP routing and endpoint definitions for post-related operations.

This module defines the REST API endpoints and handles HTTP-level logic,
translating between HTTP requests/responses and service layer operations.
"""

from typing import List

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from benchmark.config import POST_NOT_FOUND_MESSAGE
from benchmark.schemas import Post, PostCreate
from benchmark.services.post_service import PostService, PostNotFoundException
from benchmark.database import get_db

# Router configuration with prefix and tags for OpenAPI documentation
router = APIRouter(prefix="/posts", tags=["Posts"])


def get_post_service(db: Session = Depends(get_db)) -> PostService:
    """
    Dependency function to get PostService instance.
    
    Args:
        db: Database session injected by FastAPI
        
    Returns:
        PostService instance with the database session
    """
    return PostService(db)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Post)
def create_post(
    post_create: PostCreate,
    post_service: PostService = Depends(get_post_service)
) -> Post:
    """
    Create a new post.
    
    Creates a new post with the provided data and returns the created post
    with system-generated metadata including ID and creation timestamp.
    
    Args:
        post_create: The post data to create
        post_service: Injected post service instance
        
    Returns:
        The newly created post with all metadata
    """
    return post_service.create_post(post_create)


@router.get("/", response_model=List[Post])
def get_all_posts(
    post_service: PostService = Depends(get_post_service)
) -> List[Post]:
    """
    Retrieve all posts.
    
    Returns a list of all posts currently stored in the system,
    ordered by creation time (newest first).
    
    Args:
        post_service: Injected post service instance
    
    Returns:
        A list of all posts
    """
    return post_service.get_all_posts()


@router.get("/{post_id}", response_model=Post)
def get_post(
    post_id: int,
    post_service: PostService = Depends(get_post_service)
) -> Post:
    """
    Retrieve a specific post by ID.
    
    Fetches a single post using its unique identifier.
    
    Args:
        post_id: The unique identifier of the post to retrieve
        post_service: Injected post service instance
        
    Returns:
        The requested post
        
    Raises:
        HTTPException: 404 if the post is not found
    """
    try:
        return post_service.get_post_by_id(post_id)
    except PostNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=POST_NOT_FOUND_MESSAGE
        )