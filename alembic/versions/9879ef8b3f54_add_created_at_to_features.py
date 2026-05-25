"""add_created_at_to_features

Revision ID: 9879ef8b3f54
Revises: 20260131_233554
Create Date: 2026-02-01 13:57:09.933713

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9879ef8b3f54'
down_revision: Union[str, None] = '20260131_233554'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add created_at column to features table
    op.add_column(
        'features',
        sa.Column('created_at', sa.DateTime(), nullable=True),
        schema='public'
    )
    
    # Create index for better query performance
    op.create_index(
        'idx_features_created_at',
        'features',
        ['created_at'],
        schema='public'
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop index first
    op.drop_index('idx_features_created_at', table_name='features', schema='public')
    
    # Drop column
    op.drop_column('features', 'created_at', schema='public')
