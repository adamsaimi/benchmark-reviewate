"""
Business logic service for post-related operations.

This module contains all post-related business logic and data interactions.
It provides a clean separation between the API layer and data operations,
with no knowledge of HTTP-specific constructs.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List

from benchmark.schemas import Post, PostCreate


class PostNotFoundException(Exception):
    """
    Exception raised when a requested post cannot be found.
    
    This custom exception provides clear error signaling for
    operations that depend on post existence.
    """
    pass


# In-memory database simulation
_posts_db: List[Dict[str, Any]] = []
_next_id: int = 1


class PostService:
    """
    Service class encapsulating all post-related business operations.
    
    This class handles post creation, retrieval, and management,
    maintaining separation of concerns from the API layer.
    """

    def create_post(self, post_create: PostCreate) -> Post:
        """
        Create a new post with system-generated metadata.
        
        Args:
            post_create: The post data provided by the user
            
        Returns:
            The newly created post with system-generated fields
        """
        global _next_id
        
        post_dict: Dict[str, Any] = {
            "id": _next_id,
            "title": post_create.title,
            "content": post_create.content,
            "author_email": str(post_create.author_email),
            "created_at": datetime.now(timezone.utc),
        }
        
        _posts_db.append(post_dict)
        _next_id += 1
        
        return Post(**post_dict)

    def get_post_by_id(self, post_id: int) -> Post:
        """
        Retrieve a specific post by its unique identifier.
        
        Args:
            post_id: The unique identifier of the post
            
        Returns:
            The requested post
            
        Raises:
            PostNotFoundException: If no post exists with the given ID
        """
        for post_dict in _posts_db:
            if post_dict["id"] == post_id:
                return Post(**post_dict)
        
        raise PostNotFoundException(f"Post with ID {post_id} not found")

    def get_all_posts(self) -> List[Post]:
        """
        Retrieve all posts from the database.
        
        Returns:
            A list of all posts in the system
        """
        return [Post(**post_dict) for post_dict in _posts_db]