"""
SQLAlchemy database models for the Benchmark API.

This module defines the database models using SQLAlchemy ORM,
providing a clean abstraction over the database tables.
"""

from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    """
    User database model.
    
    Represents a user in the system who can create posts.
    """
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Relationship to posts
    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}')>"


class Post(Base):
    """
    Post database model.
    
    Represents a blog post stored in the PostgreSQL database.
    """
    
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(100), nullable=False, index=True)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Relationship to user
    author = relationship("User", back_populates="posts")
    
    def __repr__(self) -> str:
        return f"<Post(id={self.id}, title='{self.title}', author_id={self.author_id})>"

class Order(Base):
    """
    Order database model.
    
    Represents an order made by a user.
    """
    
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    total_amount = Column(Numeric(10, 2), nullable=False)
    refund_amount = Column(Numeric(10, 2), nullable=True, default=Decimal("0.00"))
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Relationship to user
    user = relationship("User", back_populates="orders")

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, user_id={self.user_id}, total_amount={self.total_amount})>"
