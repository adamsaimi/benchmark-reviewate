"""Add users table and update posts with relationships

Revision ID: 002
Revises: 001
Create Date: 2025-10-07 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add users table and update posts to use foreign key relationships."""
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Migrate existing posts data: create users from author_email
    # First, insert unique users from existing posts
    op.execute("""
        INSERT INTO users (email, name, created_at)
        SELECT DISTINCT 
            author_email,
            SPLIT_PART(author_email, '@', 1) as name,
            MIN(created_at) as created_at
        FROM posts
        GROUP BY author_email
        ON CONFLICT (email) DO NOTHING
    """)
    
    # Add author_id column to posts (temporarily nullable)
    op.add_column('posts', sa.Column('author_id', sa.Integer(), nullable=True))
    
    # Populate author_id from author_email
    op.execute("""
        UPDATE posts
        SET author_id = users.id
        FROM users
        WHERE posts.author_email = users.email
    """)
    
    # Now make author_id non-nullable and add foreign key
    op.alter_column('posts', 'author_id', nullable=False)
    op.create_foreign_key(
        'fk_posts_author_id_users',
        'posts', 'users',
        ['author_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_index(op.f('ix_posts_author_id'), 'posts', ['author_id'], unique=False)
    
    # Drop the old author_email column and its index
    op.drop_index(op.f('ix_posts_author_email'), table_name='posts')
    op.drop_column('posts', 'author_email')


def downgrade() -> None:
    """Revert users table and restore posts to use author_email."""
    
    # Re-add author_email column to posts
    op.add_column('posts', sa.Column('author_email', sa.String(length=255), nullable=True))
    
    # Populate author_email from users table
    op.execute("""
        UPDATE posts
        SET author_email = users.email
        FROM users
        WHERE posts.author_id = users.id
    """)
    
    # Make author_email non-nullable
    op.alter_column('posts', 'author_email', nullable=False)
    op.create_index(op.f('ix_posts_author_email'), 'posts', ['author_email'], unique=False)
    
    # Drop foreign key and author_id
    op.drop_index(op.f('ix_posts_author_id'), table_name='posts')
    op.drop_constraint('fk_posts_author_id_users', 'posts', type_='foreignkey')
    op.drop_column('posts', 'author_id')
    
    # Drop users table
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
