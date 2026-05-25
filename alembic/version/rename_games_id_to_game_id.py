"""rename games id to game_id

Revision ID: rename_games_id
Revises: 
Create Date: 2025-07-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'rename_games_id'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Rename id column to game_id in games table"""
    op.alter_column('games', 'id', new_column_name='game_id', schema='public')


def downgrade():
    """Rename game_id column back to id in games table"""
    op.alter_column('games', 'game_id', new_column_name='id', schema='public')
