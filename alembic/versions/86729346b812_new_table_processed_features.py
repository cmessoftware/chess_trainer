"""new table  processed_features

Revision ID: 86729346b812
Revises: 
Create Date: 2025-06-10 03:05:16.742748

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '86729346b812'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'processed_features',
        sa.Column('game_id', sa.String(), primary_key=True),
        sa.Column('date_processed', sa.DateTime(), nullable=False),
        schema='public'  # Replace with your actual schema name
    )
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table(
        'processed_features',
        schema='public'  # Replace with your actual schema name
    )
    # ### end Alembic commands ###
