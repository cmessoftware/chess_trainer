"""add error_label to move_shap_values

Revision ID: 20260226_000001
Revises: 20260226_000000
Create Date: 2026-02-26 06:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260226_000001"
down_revision = "20260226_000000"
branch_labels = None
depends_on = None


def upgrade():
    """Add error_label column to move_shap_values"""
    op.add_column(
        "move_shap_values",
        sa.Column(
            "error_label",
            sa.String(50),
            nullable=True,
            comment="Error predicho por ML (blunder/mistake/inaccuracy/good)",
        ),
        schema="public",
    )

    # Add index for filtering by error_label
    op.create_index(
        "idx_move_shap_error_label",
        "move_shap_values",
        ["error_label"],
        schema="public",
    )


def downgrade():
    """Remove error_label column"""
    op.drop_index(
        "idx_move_shap_error_label", table_name="move_shap_values", schema="public"
    )
    op.drop_column("move_shap_values", "error_label", schema="public")
