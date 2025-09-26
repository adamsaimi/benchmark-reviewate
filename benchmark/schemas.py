"""
Data contracts and schemas for the Benchmark API.

This module defines Pydantic models that serve as the data contracts
for API requests and responses, ensuring type safety and validation.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from benchmark.config import MAX_CONTENT_LENGTH, MAX_TITLE_LENGTH, MIN_TITLE_LENGTH


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
        example="My First Blog Post"
    )
    content: str = Field(
        max_length=MAX_CONTENT_LENGTH,
        description="The main content of the post",
        example="This is the content of my blog post. It contains valuable information."
    )


class PostCreate(PostBase):
    """
    Schema for creating a new post.
    
    Inherits the base post fields and adds the author email,
    which is required when creating a new post.
    """
    
    author_email: EmailStr = Field(description="Email address of the post author")


class Post(PostBase):
    """
    Complete post schema for API responses.
    
    Represents a full post with all system-generated fields
    including ID, author email, and creation timestamp.
    """
    
    id: int = Field(description="Unique identifier for the post")
    author_email: EmailStr = Field(description="Email address of the post author")
    created_at: datetime = Field(description="UTC timestamp when the post was created")