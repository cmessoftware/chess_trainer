"""Add move context to move_shap_values

Revision ID: add_move_context_shap
Revises: <PREVIOUS_REVISION>
Create Date: 2026-02-28

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260228_000001'
down_revision = '20260226_000002'
branch_labels = None
depends_on = None


def upgrade():
    # Agregar columnas para contexto del movimiento
    op.add_column('move_shap_values', sa.Column('move_san', sa.String(20), nullable=True, comment='Movimiento en notación algebraica (e.g., Nf3)'))
    op.add_column('move_shap_values', sa.Column('move_uci', sa.String(10), nullable=True, comment='Movimiento en notación UCI (e.g., e2e4)'))
    op.add_column('move_shap_values', sa.Column('fen', sa.String(100), nullable=True, comment='Posición FEN antes del movimiento'))
    
    print("✅ Columnas move_san, move_uci, fen agregadas a move_shap_values")


def downgrade():
    # Revertir cambios
    op.drop_column('move_shap_values', 'fen')
    op.drop_column('move_shap_values', 'move_uci')
    op.drop_column('move_shap_values', 'move_san')
    
    print("✅ Columnas move_san, move_uci, fen eliminadas de move_shap_values")
