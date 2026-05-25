"""add_player_color_to_shap

Revision ID: add_player_color_to_shap
Revises: update_shap_view_with_moves
Create Date: 2026-02-28 14:30:00.000000

Agrega la columna player_color a move_shap_values para identificar
si el movimiento fue realizado por blancas ('white') o negras ('black').

Esto mejora la claridad del análisis SHAP al mostrar qué jugador
hizo cada movimiento analizado.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260228_000003'
down_revision: Union[str, None] = '20260228_000002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Agregar columna player_color a move_shap_values.
    
    Valores:
      - 'white': Movimiento jugado por las blancas
      - 'black': Movimiento jugado por las negras
    """
    # Agregar columna player_color
    op.add_column(
        'move_shap_values',
        sa.Column(
            'player_color',
            sa.String(length=10),
            nullable=True,
            comment="Color del jugador que hizo el movimiento ('white' o 'black')"
        ),
        schema='public'
    )
    
    print("✅ Columna 'player_color' agregada a move_shap_values")


def downgrade() -> None:
    """
    Eliminar columna player_color de move_shap_values.
    """
    op.drop_column('move_shap_values', 'player_color', schema='public')
    
    print("⚠️  Columna 'player_color' eliminada de move_shap_values")
