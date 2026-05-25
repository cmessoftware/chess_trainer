"""add_imported_by_to_games

Revision ID: 20260213_231617
Revises: 20260211_000000
Create Date: 2026-02-13 23:16:17.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260213_231617"
down_revision = "f0f85e5542e7"
branch_labels = None
depends_on = None


def upgrade():
    """Add imported_by column to games table"""
    op.add_column("games", sa.Column("imported_by", sa.String(), nullable=True))

    # Create index for faster queries by imported_by
    op.create_index("idx_games_imported_by", "games", ["imported_by"])


def downgrade():
    """Remove imported_by column from games table"""
    op.drop_index("idx_games_imported_by", table_name="games")
    op.drop_column("games", "imported_by")
