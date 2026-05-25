"""merge heads

Revision ID: f0f85e5542e7
Revises: 20260211_000000, 9879ef8b3f54
Create Date: 2026-02-11 18:02:14.471146

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f0f85e5542e7'
down_revision: Union[str, None] = ('20260211_000000', '9879ef8b3f54')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
