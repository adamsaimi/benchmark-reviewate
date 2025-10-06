"""Initial migration - create posts table

Revision ID: 001
Revises: 
Create Date: 2025-10-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create posts table."""
    op.create_table(
        'posts',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('title', sa.String(length=100), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('author_email', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_posts_id'), 'posts', ['id'], unique=False)
    op.create_index(op.f('ix_posts_title'), 'posts', ['title'], unique=False)
    op.create_index(op.f('ix_posts_author_email'), 'posts', ['author_email'], unique=False)


def downgrade() -> None:
    """Drop posts table."""
    op.drop_index(op.f('ix_posts_author_email'), table_name='posts')
    op.drop_index(op.f('ix_posts_title'), table_name='posts')
    op.drop_index(op.f('ix_posts_id'), table_name='posts')
    op.drop_table('posts')
