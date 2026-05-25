"""add_batch_tracking

Revision ID: 20260131_233554
Revises: 0b916c932d3b
Create Date: 2026-01-31 23:35:54

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260131_233554'
down_revision: Union[str, None] = '0b916c932d3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add batch tracking columns to games table."""
    # Add import_batch_id column
    op.add_column('games', sa.Column('import_batch_id', sa.String(), nullable=True), schema='public')
    
    # Add source_filename column
    op.add_column('games', sa.Column('source_filename', sa.String(), nullable=True), schema='public')
    
    # Create index for efficient batch filtering
    op.create_index('idx_games_batch_id', 'games', ['import_batch_id'], schema='public')
    
    # Create index for filename filtering
    op.create_index('idx_games_source_filename', 'games', ['source_filename'], schema='public')


def downgrade() -> None:
    """Remove batch tracking columns from games table."""
    # Drop indexes first
    op.drop_index('idx_games_source_filename', table_name='games', schema='public')
    op.drop_index('idx_games_batch_id', table_name='games', schema='public')
    
    # Drop columns
    op.drop_column('games', 'source_filename', schema='public')
    op.drop_column('games', 'import_batch_id', schema='public')
