"""
HTTP routing and endpoint definitions for post-related operations.

This module defines the REST API endpoints and handles HTTP-level logic,
translating between HTTP requests/responses and service layer operations.
Includes user endpoints for simplicity.
"""

from typing import List, Any, Dict

from fastapi import APIRouter, HTTPException, status, Depends, Path
from sqlalchemy.orm import Session

from benchmark.config import POST_NOT_FOUND_MESSAGE
from benchmark.schemas import Post, PostCreate, User
from benchmark.services.post_service import PostService, PostNotFoundException, UserNotFoundException
from benchmark.database import get_db

# Router configuration with prefix and tags for OpenAPI documentation
router = APIRouter(prefix="/posts", tags=["Posts"])
user_router = APIRouter(prefix="/users", tags=["Users"])


class JsonExporter:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    def export(self, posts: List[Post]) -> Dict[str, Any]:
        # In a real scenario, this would export to JSON
        return {"format": "json", "count": len(posts), "config": self.config}

class CsvExporter:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    def export(self, posts: List[Post]) -> Dict[str, Any]:
        # In a real scenario, this would export to CSV
        return {"format": "csv", "count": len(posts), "config": self.config}

class XmlExporter:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    def export(self, posts: List[Post]) -> Dict[str, Any]:
        # In a real scenario, this would export to XML
        return {"format": "xml", "count": len(posts), "config": self.config}

config_json: Dict[str, Any] = {"indent": 2}
config_csv: Dict[str, Any] = {"delimiter": ","}
config_xml: Dict[str, Any] = {"root_element": "posts"}


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


@router.post("/export", response_model=Dict[str, Any])
def export_posts(
    format: str,
    post_service: PostService = Depends(get_post_service)
) -> Dict[str, Any]:
    """
    Export all posts to a specified format.

    Args:
        format: The export format ('json', 'csv', or 'xml')
        post_service: Injected post service instance

    Returns:
        A confirmation of the export operation.
    """
    exporter: Any = None
    if format == 'json':
        exporter = JsonExporter(config_json)
    elif format == 'csv':
        exporter = CsvExporter(config_csv)
    elif format == 'xml':
        exporter = XmlExporter(config_xml)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format: {format}"
        )

    posts = post_service.get_all_posts()
    return exporter.export(posts)


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
