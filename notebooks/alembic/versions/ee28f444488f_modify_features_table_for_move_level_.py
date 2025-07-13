"""modify_features_table_for_move_level_analysis

Revision ID: ee28f444488f
Revises: bea41b56e74d
Create Date: 2025-07-13 06:28:55.645739

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ee28f444488f'
down_revision: Union[str, None] = 'bea41b56e74d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Transform features table from game-level to move-level analysis."""
    # 1. Rename current features table to preserve game-level data
    op.rename_table('features', 'game_features_legacy')
    
    # 2. Create new features table with move-level structure
    op.create_table('features',
        sa.Column('game_id', sa.String(255), nullable=False),
        sa.Column('move_number', sa.Integer, nullable=False),
        sa.Column('player_color', sa.Integer, nullable=False),  # 0=white, 1=black
        sa.Column('material_balance', sa.Float, nullable=True),
        sa.Column('material_total', sa.Float, nullable=True),
        sa.Column('num_pieces', sa.Integer, nullable=True),
        sa.Column('branching_factor', sa.Integer, nullable=True),
        sa.Column('position_evaluation', sa.Float, nullable=True),
        sa.Column('move_quality', sa.String(20), nullable=True),
        sa.Column('time_taken', sa.Float, nullable=True),
        sa.Column('is_capture', sa.Boolean, default=False),
        sa.Column('is_check', sa.Boolean, default=False),
        sa.Column('is_castling', sa.Boolean, default=False),
        sa.Column('piece_type', sa.String(10), nullable=True),
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('game_id', 'move_number', 'player_color')
    )
    
    # 3. Create indexes for performance
    op.create_index('idx_features_game_id', 'features', ['game_id'])
    op.create_index('idx_features_source', 'features', ['source'])
    op.create_index('idx_features_move_quality', 'features', ['move_quality'])


def downgrade() -> None:
    """Restore original features table structure."""
    # Drop new move-level features table
    op.drop_table('features')
    
    # Restore original game-level features table
    op.rename_table('game_features_legacy', 'features')
