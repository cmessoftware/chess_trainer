"""merge_heads

Revision ID: bea41b56e74d
Revises: add_game_analytics, mlflow_postgres_migration
Create Date: 2025-07-13 06:28:42.535142

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bea41b56e74d'
down_revision: Union[str, None] = ('add_game_analytics', 'mlflow_postgres_migration')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
