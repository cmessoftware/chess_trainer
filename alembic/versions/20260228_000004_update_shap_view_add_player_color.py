"""update_shap_view_add_player_color

Revision ID: update_shap_view_add_player_color
Revises: add_player_color_to_shap
Create Date: 2026-02-28 14:35:00.000000

Actualiza la vista shap_values_with_games para incluir la columna
player_color, mejorando la legibilidad del análisis SHAP.

Vista actualizada incluye:
  - move_san, move_uci, fen (contexto del movimiento)
  - player_color (identificación del jugador)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260228_000004'
down_revision: Union[str, None] = '20260228_000003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Recrear vista shap_values_with_games con player_color.
    """
    # Eliminar vista existente
    op.execute("DROP VIEW IF EXISTS public.shap_values_with_games CASCADE")
    
    # Recrear vista con player_color
    op.execute("""
        CREATE VIEW public.shap_values_with_games AS
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
            m.move_san,
            m.move_uci,
            m.fen,
            m.player_color,
            m.created_at AS shap_created_at
        FROM 
            public.move_shap_values m
        INNER JOIN 
            public.analysis_results a ON m.analysis_id = a.id
        ORDER BY 
            a.id, m.move_number, ABS(m.shap_value) DESC
    """)
    
    print("✅ Vista 'shap_values_with_games' actualizada con player_color")


def downgrade() -> None:
    """
    Revertir vista shap_values_with_games (sin player_color).
    """
    # Eliminar vista existente
    op.execute("DROP VIEW IF EXISTS public.shap_values_with_games CASCADE")
    
    # Recrear vista SIN player_color
    op.execute("""
        CREATE VIEW public.shap_values_with_games AS
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
            m.move_san,
            m.move_uci,
            m.fen,
            m.created_at AS shap_created_at
        FROM 
            public.move_shap_values m
        INNER JOIN 
            public.analysis_results a ON m.analysis_id = a.id
        ORDER BY 
            a.id, m.move_number, ABS(m.shap_value) DESC
    """)
    
    print("⚠️  Vista 'shap_values_with_games' revertida (sin player_color)")
