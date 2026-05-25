"""add_shap_analysis_tables

Revision ID: 20260223_140000
Revises: 20260216_030000
Create Date: 2026-02-23 14:00:00.000000

Adds 3 tables for ML Analysis + SHAP functionality (F 3.6):
- player_feature_importance: Aggregated SHAP values per player
- analysis_results: ML predictions persistence
- move_shap_values: Per-move SHAP explanations
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260223_140000"
down_revision = "20260216_030000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create player_feature_importance table
    op.create_table(
        "player_feature_importance",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("feature_name", sa.String(length=100), nullable=False),
        sa.Column(
            "mean_shap_value",
            sa.Float(),
            nullable=False,
            comment="SHAP promedio (puede ser negativo - reduce error probability)",
        ),
        sa.Column(
            "mean_abs_shap_value",
            sa.Float(),
            nullable=False,
            comment="SHAP absoluto promedio (magnitud de impacto sin dirección)",
        ),
        sa.Column(
            "total_samples",
            sa.Integer(),
            nullable=False,
            comment="Cantidad de jugadas/partidas analizadas para este agregado",
        ),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )
    op.create_index(
        "idx_pfi_username",
        "player_feature_importance",
        ["username"],
        unique=False,
        schema="public",
    )
    op.create_index(
        "idx_pfi_feature",
        "player_feature_importance",
        ["feature_name"],
        unique=False,
        schema="public",
    )
    op.create_index(
        "idx_pfi_period",
        "player_feature_importance",
        ["period_start", "period_end"],
        unique=False,
        schema="public",
    )

    # Create analysis_results table
    op.create_table(
        "analysis_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("game_id", sa.String(), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column(
            "error_level",
            sa.String(length=50),
            nullable=False,
            comment="Nivel global: blunder_prone, mistake_prone, accurate, excellent",
        ),
        sa.Column(
            "prediction_confidence",
            sa.Float(),
            nullable=True,
            comment="Confianza del modelo en la predicción (0.0 - 1.0)",
        ),
        sa.Column(
            "total_moves",
            sa.Integer(),
            nullable=True,
            comment="Total de jugadas analizadas en la partida",
        ),
        sa.Column(
            "blunder_count",
            sa.Integer(),
            nullable=True,
            comment="Cantidad de blunders detectados",
        ),
        sa.Column(
            "mistake_count",
            sa.Integer(),
            nullable=True,
            comment="Cantidad de mistakes detectados",
        ),
        sa.Column(
            "inaccuracy_count",
            sa.Integer(),
            nullable=True,
            comment="Cantidad de inaccuracies detectadas",
        ),
        sa.Column(
            "good_move_count",
            sa.Integer(),
            nullable=True,
            comment="Cantidad de jugadas buenas/excelentes",
        ),
        sa.Column(
            "average_centipawn_loss",
            sa.Float(),
            nullable=True,
            comment="Pérdida promedio en centipawnsijada por jug",
        ),
        sa.Column(
            "accuracy_percentage",
            sa.Float(),
            nullable=True,
            comment="Porcentaje de precisión general (0-100)",
        ),
        sa.Column(
            "analyzed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )
    op.create_index(
        "idx_analysis_username",
        "analysis_results",
        ["username"],
        unique=False,
        schema="public",
    )
    op.create_index(
        "idx_analysis_game_id",
        "analysis_results",
        ["game_id"],
        unique=False,
        schema="public",
    )
    op.create_index(
        "idx_analysis_date",
        "analysis_results",
        ["analyzed_at"],
        unique=False,
        schema="public",
    )
    op.create_index(
        "idx_analysis_user_date",
        "analysis_results",
        ["username", "analyzed_at"],
        unique=False,
        schema="public",
    )

    # Create move_shap_values table
    op.create_table(
        "move_shap_values",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "analysis_id",
            sa.Integer(),
            nullable=False,
            comment="FK a analysis_results.id",
        ),
        sa.Column(
            "move_number",
            sa.Integer(),
            nullable=False,
            comment="Número de jugada en la partida (1-indexed)",
        ),
        sa.Column(
            "feature_name",
            sa.String(length=100),
            nullable=False,
            comment="Nombre de la feature (e.g., 'material_balance', 'self_mobility')",
        ),
        sa.Column(
            "shap_value",
            sa.Float(),
            nullable=False,
            comment="Contribución de la feature a la predicción (puede ser +/-)",
        ),
        sa.Column(
            "feature_value",
            sa.Float(),
            nullable=True,
            comment="Valor original de la feature en esta jugada (antes de SHAP)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )
    op.create_index(
        "idx_move_shap_analysis",
        "move_shap_values",
        ["analysis_id"],
        unique=False,
        schema="public",
    )
    op.create_index(
        "idx_move_shap_move_number",
        "move_shap_values",
        ["move_number"],
        unique=False,
        schema="public",
    )
    op.create_index(
        "idx_move_shap_feature",
        "move_shap_values",
        ["feature_name"],
        unique=False,
        schema="public",
    )
    op.create_index(
        "idx_move_shap_analysis_move",
        "move_shap_values",
        ["analysis_id", "move_number"],
        unique=False,
        schema="public",
    )


def downgrade() -> None:
    # Drop tables in reverse order (respecting potential FK constraints)
    op.drop_index(
        "idx_move_shap_analysis_move", table_name="move_shap_values", schema="public"
    )
    op.drop_index(
        "idx_move_shap_feature", table_name="move_shap_values", schema="public"
    )
    op.drop_index(
        "idx_move_shap_move_number", table_name="move_shap_values", schema="public"
    )
    op.drop_index(
        "idx_move_shap_analysis", table_name="move_shap_values", schema="public"
    )
    op.drop_table("move_shap_values", schema="public")

    op.drop_index(
        "idx_analysis_user_date", table_name="analysis_results", schema="public"
    )
    op.drop_index("idx_analysis_date", table_name="analysis_results", schema="public")
    op.drop_index(
        "idx_analysis_game_id", table_name="analysis_results", schema="public"
    )
    op.drop_index(
        "idx_analysis_username", table_name="analysis_results", schema="public"
    )
    op.drop_table("analysis_results", schema="public")

    op.drop_index(
        "idx_pfi_period", table_name="player_feature_importance", schema="public"
    )
    op.drop_index(
        "idx_pfi_feature", table_name="player_feature_importance", schema="public"
    )
    op.drop_index(
        "idx_pfi_username", table_name="player_feature_importance", schema="public"
    )
    op.drop_table("player_feature_importance", schema="public")
