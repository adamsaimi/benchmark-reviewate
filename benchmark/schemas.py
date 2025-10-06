"""
Data contracts and schemas for the Benchmark API.

This module defines Pydantic models that serve as the data contracts
for API requests and responses, ensuring type safety and validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from benchmark.config import MAX_CONTENT_LENGTH, MAX_TITLE_LENGTH, MIN_TITLE_LENGTH


# ============================================================================
# User Schemas
# ============================================================================

class UserBase(BaseModel):
    """
    Base schema containing common fields for user-related operations.
    """
    
    email: EmailStr = Field(description="Email address of the user")
    name: str = Field(
        min_length=1,
        max_length=100,
        description="Name of the user",
        examples=["John Doe"]
    )


class UserCreate(UserBase):
    """
    Schema for creating a new user.
    """
    pass


class User(UserBase):
    """
    Complete user schema for API responses.
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(description="Unique identifier for the user")
    created_at: datetime = Field(description="UTC timestamp when the user was created")


# ============================================================================
# Post Schemas
# ============================================================================

class PostBase(BaseModel):
    """
    Base schema containing common fields for post-related operations.
    
    This schema serves as the foundation for other post schemas,
    containing the core fields that are common across different operations.
    """
    
    title: str = Field(
        min_length=MIN_TITLE_LENGTH,
        max_length=MAX_TITLE_LENGTH,
        description="The title of the post",
        examples=["My First Blog Post"]
    )
    content: str = Field(
        max_length=MAX_CONTENT_LENGTH,
        description="The main content of the post",
        examples=["This is the content of my blog post. It contains valuable information."]
    )


class PostCreate(PostBase):
    """
    Schema for creating a new post.
    
    Inherits the base post fields and adds the author email,
    which is required when creating a new post.
    """
    
    author_email: EmailStr = Field(description="Email address of the post author")
    author_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Name of the post author (optional, will use existing user if email exists)"
    )


class Post(PostBase):
    """
    Complete post schema for API responses.
    
    Represents a full post with all system-generated fields
    including ID, author information, and creation timestamp.
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(description="Unique identifier for the post")
    author_id: int = Field(description="ID of the post author")
    created_at: datetime = Field(description="UTC timestamp when the post was created")
    
    # Include author details in response
    author: User = Field(description="Author information")