"""
Business logic service for post-related operations.

This module contains all post-related business logic and data interactions.
It provides a clean separation between the API layer and data operations,
with no knowledge of HTTP-specific constructs.
"""

from typing import List
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from benchmark.models import Post as PostModel, User as UserModel
from benchmark.schemas import Post, PostCreate, User


class PostNotFoundException(Exception):
    """
    Exception raised when a requested post cannot be found.
    
    This custom exception provides clear error signaling for
    operations that depend on post existence.
    """
    pass


class UserNotFoundException(Exception):
    """
    Exception raised when a requested user cannot be found.
    """
    pass


class PostService:
    """
    Service class encapsulating all post-related business operations.
    
    This class handles post creation, retrieval, and management,
    maintaining separation of concerns from the API layer.
    It also handles user operations to simplify the architecture.
    """

    def __init__(self, db: Session):
        """
        Initialize the PostService with a database session.
        
        Args:
            db: SQLAlchemy database session for database operations
        """
        self.db = db

    def get_or_create_user(self, email: str, name: str = None) -> UserModel:
        """
        Get an existing user by email or create a new one.
        
        Args:
            email: The email address of the user
            name: The name of the user (required if creating new user)
            
        Returns:
            The existing or newly created user
            
        Raises:
            ValueError: If name is not provided for a new user
            SQLAlchemyError: If there's a database error during creation
        """
        # Try to find existing user
        user = self.db.query(UserModel).filter(UserModel.email == email).first()
        
        if user:
            return user
        
        # Create new user
        if not name:
            raise ValueError("Name is required when creating a new user")
        
        try:
            user = UserModel(email=email, name=name)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e

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
            # Get or create user
            user = self.get_or_create_user(
                email=str(post_create.author_email),
                name=post_create.author_name or str(post_create.author_email).split('@')[0]
            )
            
            # Create post
            db_post = PostModel(
                title=post_create.title,
                content=post_create.content,
                author_id=user.id
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

    async def process_post(self, post_id: int) -> Post:
        """
        Simulates processing a post asynchronously.
        
        Args:
            post_id: The unique identifier of the post
            
        Returns:
            The processed post
            
        Raises:
            PostNotFoundException: If no post exists with the given ID
        """
        # In a real app, this might be a complex async operation
        # Here we simulate it by getting the post and adding a small delay.
        post = self.get_post_by_id(post_id)
        await asyncio.sleep(0.01) # Simulate async I/O work
        return post

    def get_all_posts(self) -> List[Post]:
        """
        Retrieve all posts from the database.
        
        Returns:
            A list of all posts in the system, ordered by creation date (newest first)
        """
        db_posts = self.db.query(PostModel).order_by(PostModel.created_at.desc()).all()
        return [Post.model_validate(post) for post in db_posts]
    
    def get_user_by_email(self, email: str) -> User:
        """
        Retrieve a user by email address.
        
        Args:
            email: The email address of the user
            
        Returns:
            The requested user
            
        Raises:
            UserNotFoundException: If no user exists with the given email
        """
        user = self.db.query(UserModel).filter(UserModel.email == email).first()
        
        if user is None:
            raise UserNotFoundException(f"User with email {email} not found")
        
        return User.model_validate(user)
    
    def get_all_users(self) -> List[User]:
        """
        Retrieve all users from the database.
        
        Returns:
            A list of all users in the system
        """
        users = self.db.query(UserModel).order_by(UserModel.created_at.desc()).all()
        return [User.model_validate(user) for user in users]