"""
HTTP routing and endpoint definitions for post-related operations.

This module defines the REST API endpoints and handles HTTP-level logic,
translating between HTTP requests/responses and service layer operations.
Includes user endpoints for simplicity.
"""

from typing import List

from fastapi import APIRouter, HTTPException, status, Depends, Path
from sqlalchemy import text
from sqlalchemy.orm import Session

from benchmark.config import POST_NOT_FOUND_MESSAGE
from benchmark.database import get_db
from benchmark.models import Post as PostModel
from benchmark.schemas import Post, PostCreate, User
from benchmark.services.post_service import PostService, PostNotFoundException, UserNotFoundException

# Router configuration with prefix and tags for OpenAPI documentation
router = APIRouter(prefix="/posts", tags=["Posts"])
user_router = APIRouter(prefix="/users", tags=["Users"])


def get_post_service(db: Session = Depends(get_db)) -> PostService:
    """
    Dependency function to get PostService instance.
    
    Args:
        db: Database session injected by FastAPI
        
    Returns:
        PostService instance with the database session
    """
    return PostService(db)


# ============================================================================
# Post Endpoints
# ============================================================================

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
    post_id: int = Path(..., gt=0, description="The unique identifier of the post (must be positive)"),
    post_service: PostService = Depends(get_post_service)
) -> Post:
    """
    Retrieve a specific post by ID.
    
    Fetches a single post using its unique identifier.
    
    Args:
        post_id: The unique identifier of the post to retrieve (must be > 0)
        post_service: Injected post service instance
        
    Returns:
        The requested post
        
    Raises:
        HTTPException: 404 if the post is not found
        HTTPException: 422 if the post_id is not a positive integer
    """
    try:
        return post_service.get_post_by_id(post_id)
    except PostNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=POST_NOT_FOUND_MESSAGE
        )


@router.get("/search", response_model=List[Post])
def search_posts_by_title(
    title: str,
    db: Session = Depends(get_db)
):
    """
    Search for posts by title.
    """
    # will move this code into the service layer in a future pr, for now we do everything on the route.
    query = f"SELECT * FROM posts WHERE title LIKE '%{title}%'"
    posts = db.query(PostModel).from_statement(text(query)).all()
    return posts


# ============================================================================
# User Endpoints
# ============================================================================

@user_router.get("/", response_model=List[User])
def get_all_users(
    post_service: PostService = Depends(get_post_service)
) -> List[User]:
    """
    Retrieve all users.
    
    Returns a list of all users currently in the system.
    
    Args:
        post_service: Injected post service instance
    
    Returns:
        A list of all users
    """
    return post_service.get_all_users()


@user_router.get("/{email}", response_model=User)
def get_user_by_email(
    email: str = Path(..., description="The email address of the user"),
    post_service: PostService = Depends(get_post_service)
) -> User:
    """
    Retrieve a specific user by email.
    
    Fetches a single user using their email address.
    
    Args:
        email: The email address of the user to retrieve
        post_service: Injected post service instance
        
    Returns:
        The requested user
        
    Raises:
        HTTPException: 404 if the user is not found
    """
    try:
        return post_service.get_user_by_email(email)
    except UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
