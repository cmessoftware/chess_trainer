"""Update shap_values_with_games view with move context

Revision ID: update_shap_view_context
Revises: add_move_context_shap
Create Date: 2026-02-28

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '20260228_000002'
down_revision = '20260228_000001'
branch_labels = None
depends_on = None


def upgrade():
    # Recrear vista con nuevas columnas
    op.execute("""
        DROP VIEW IF EXISTS shap_values_with_games;
        
        CREATE VIEW shap_values_with_games AS
        SELECT 
            m.id AS shap_id,
            m.analysis_id,
            a.game_id,
            a.username,
            m.error_label,
            a.accuracy_percentage,
            a.analyzed_at,
            m.move_number,
            m.feature_name,
            m.shap_value,
            m.feature_value,
            m.move_san,  -- NUEVO
            m.move_uci,  -- NUEVO
            m.fen        -- NUEVO
        FROM move_shap_values m
        JOIN analysis_results a ON m.analysis_id = a.id
        ORDER BY a.id, m.move_number, ABS(m.shap_value) DESC;
    """)
    
    print("✅ Vista shap_values_with_games actualizada con move_san, move_uci, fen")


def downgrade():
    # Volver a versión anterior sin las columnas nuevas
    op.execute("""
        DROP VIEW IF EXISTS shap_values_with_games;
        
        CREATE VIEW shap_values_with_games AS
        SELECT 
            m.id AS shap_id,
            m.analysis_id,
            a.game_id,
            a.username,
            m.error_label,
            a.accuracy_percentage,
            a.analyzed_at,
            m.move_number,
            m.feature_name,
            m.shap_value,
            m.feature_value
        FROM move_shap_values m
        JOIN analysis_results a ON m.analysis_id = a.id
        ORDER BY a.id, m.move_number, ABS(m.shap_value) DESC;
    """)
    
    print("✅ Vista shap_values_with_games revertida a versión anterior")
