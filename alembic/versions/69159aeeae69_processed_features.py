"""processed_features

Revision ID: 69159aeeae69
Revises: 66e04ee582df
Create Date: 2025-06-13 22:14:23.776431

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '69159aeeae69'
down_revision: Union[str, None] = '66e04ee582df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'processed_features',
        sa.Column('game_id', sa.String(), primary_key=True),
        sa.Column('date_processed', sa.DateTime(), nullable=False)
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('processed_features')
    # ### end Alembic commands ###
