"""update view shap_values_with_games to use error_label

Revision ID: 20260226_000002
Revises: 20260226_000001
Create Date: 2026-02-26 06:15:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260226_000002"
down_revision = "20260226_000001"
branch_labels = None
depends_on = None


def upgrade():
    """Update view to use move-specific error_label instead of game-level error_level"""
    op.execute("DROP VIEW IF EXISTS shap_values_with_games;")

    op.execute(
        """
        CREATE OR REPLACE VIEW shap_values_with_games AS
        SELECT 
            m.id as shap_id,
            m.analysis_id,
            a.game_id,
            a.username,
            m.error_label,  -- CAMBIO: usar error_label de move_shap_values (move-specific)
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
    """Revert to previous view version"""
    op.execute("DROP VIEW IF EXISTS shap_values_with_games;")

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
