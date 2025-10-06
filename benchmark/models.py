"""
SQLAlchemy database models for the Benchmark API.

This module defines the database models using SQLAlchemy ORM,
providing a clean abstraction over the database tables.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Post(Base):
    """
    Post database model.
    
    Represents a blog post stored in the PostgreSQL database.
    """
    
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(100), nullable=False, index=True)
    content = Column(Text, nullable=False)
    author_email = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self) -> str:
        return f"<Post(id={self.id}, title='{self.title}', author='{self.author_email}')>"
