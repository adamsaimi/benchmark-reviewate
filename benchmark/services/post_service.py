"""
Business logic service for post-related operations.

This module contains all post-related business logic and data interactions.
It provides a clean separation between the API layer and data operations,
with no knowledge of HTTP-specific constructs.
"""

from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from benchmark.models import Post as PostModel
from benchmark.schemas import Post, PostCreate


class PostNotFoundException(Exception):
    """
    Exception raised when a requested post cannot be found.
    
    This custom exception provides clear error signaling for
    operations that depend on post existence.
    """
    pass


class PostService:
    """
    Service class encapsulating all post-related business operations.
    
    This class handles post creation, retrieval, and management,
    maintaining separation of concerns from the API layer.
    """

    def __init__(self, db: Session):
        """
        Initialize the PostService with a database session.
        
        Args:
            db: SQLAlchemy database session for database operations
        """
        self.db = db

    def create_post(self, post_create: PostCreate) -> Post:
        """
        Create a new post with system-generated metadata.
        
        Args:
            post_create: The post data provided by the user
            
        Returns:
            The newly created post with system-generated fields
            
        Raises:
            SQLAlchemyError: If there's a database error during creation
        """
        try:
            db_post = PostModel(
                title=post_create.title,
                content=post_create.content,
                author_email=str(post_create.author_email)
            )
            
            self.db.add(db_post)
            self.db.commit()
            self.db.refresh(db_post)
            
            return Post.model_validate(db_post)
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e

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
        db_post = self.db.query(PostModel).filter(PostModel.id == post_id).first()
        
        if db_post is None:
            raise PostNotFoundException(f"Post with ID {post_id} not found")
        
        return Post.model_validate(db_post)

    def get_all_posts(self) -> List[Post]:
        """
        Retrieve all posts from the database.
        
        Returns:
            A list of all posts in the system, ordered by creation date (newest first)
        """
        db_posts = self.db.query(PostModel).order_by(PostModel.created_at.desc()).all()
        return [Post.model_validate(post) for post in db_posts]