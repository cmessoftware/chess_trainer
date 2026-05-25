"""create view shap_values_with_games

Revision ID: 20260226_000000
Revises:
Create Date: 2026-02-26 05:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260226_000000"
down_revision = "20260223_140000"
branch_labels = None
depends_on = None


def upgrade():
    """Create view for SHAP values with game information"""
    op.execute(
        """
        CREATE OR REPLACE VIEW shap_values_with_games AS
        SELECT 
            m.id as shap_id,
            m.analysis_id,
            a.game_id,
            a.username,
            a.error_level,
            a.accuracy_percentage,
            a.analyzed_at,
            m.move_number,
            m.feature_name,
            m.shap_value,
            m.feature_value
        FROM move_shap_values m
        INNER JOIN analysis_results a ON m.analysis_id = a.id
        ORDER BY a.id, m.move_number, ABS(m.shap_value) DESC;
    """
    )


def downgrade():
    """Drop view"""
    op.execute("DROP VIEW IF EXISTS shap_values_with_games;")
