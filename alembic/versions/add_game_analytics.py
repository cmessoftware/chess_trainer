"""Add game_analytics table

Revision ID: add_game_analytics
Revises: create_features_tables
Create Date: 2025-07-13 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_game_analytics"
down_revision = "create_features_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create game_analytics table
    op.create_table(
        "game_analytics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("white_elo", sa.Integer(), nullable=True),
        sa.Column("black_elo", sa.Integer(), nullable=True),
        sa.Column("time_control", sa.String(length=50), nullable=True),
        sa.Column("opening_name", sa.String(length=200), nullable=True),
        sa.Column("opening_eco", sa.String(length=10), nullable=True),
        sa.Column("game_result", sa.String(length=20), nullable=True),
        sa.Column("total_moves", sa.Integer(), nullable=True),
        sa.Column("avg_move_time", sa.Float(), nullable=True),
        sa.Column("blunders_white", sa.Integer(), server_default="0", nullable=True),
        sa.Column("blunders_black", sa.Integer(), server_default="0", nullable=True),
        sa.Column("mistakes_white", sa.Integer(), server_default="0", nullable=True),
        sa.Column("mistakes_black", sa.Integer(), server_default="0", nullable=True),
        sa.Column(
            "inaccuracies_white", sa.Integer(), server_default="0", nullable=True
        ),
        sa.Column(
            "inaccuracies_black", sa.Integer(), server_default="0", nullable=True
        ),
        sa.Column(
            "brilliant_moves_white", sa.Integer(), server_default="0", nullable=True
        ),
        sa.Column(
            "brilliant_moves_black", sa.Integer(), server_default="0", nullable=True
        ),
        sa.Column("good_moves_white", sa.Integer(), server_default="0", nullable=True),
        sa.Column("good_moves_black", sa.Integer(), server_default="0", nullable=True),
        sa.Column("book_moves_white", sa.Integer(), server_default="0", nullable=True),
        sa.Column("book_moves_black", sa.Integer(), server_default="0", nullable=True),
        sa.Column("best_moves_white", sa.Integer(), server_default="0", nullable=True),
        sa.Column("best_moves_black", sa.Integer(), server_default="0", nullable=True),
        sa.Column("accuracy_white", sa.Float(), nullable=True),
        sa.Column("accuracy_black", sa.Float(), nullable=True),
        sa.Column("avg_centipawn_loss_white", sa.Float(), nullable=True),
        sa.Column("avg_centipawn_loss_black", sa.Float(), nullable=True),
        sa.Column(
            "time_pressure_moves_white", sa.Integer(), server_default="0", nullable=True
        ),
        sa.Column(
            "time_pressure_moves_black", sa.Integer(), server_default="0", nullable=True
        ),
        sa.Column(
            "castle_kingside_white", sa.Boolean(), server_default="false", nullable=True
        ),
        sa.Column(
            "castle_queenside_white",
            sa.Boolean(),
            server_default="false",
            nullable=True,
        ),
        sa.Column(
            "castle_kingside_black", sa.Boolean(), server_default="false", nullable=True
        ),
        sa.Column(
            "castle_queenside_black",
            sa.Boolean(),
            server_default="false",
            nullable=True,
        ),
        sa.Column(
            "en_passant_captures", sa.Integer(), server_default="0", nullable=True
        ),
        sa.Column("promotions_white", sa.Integer(), server_default="0", nullable=True),
        sa.Column("promotions_black", sa.Integer(), server_default="0", nullable=True),
        sa.Column(
            "checks_given_white", sa.Integer(), server_default="0", nullable=True
        ),
        sa.Column(
            "checks_given_black", sa.Integer(), server_default="0", nullable=True
        ),
        sa.Column(
            "pieces_captured_white", sa.Integer(), server_default="0", nullable=True
        ),
        sa.Column(
            "pieces_captured_black", sa.Integer(), server_default="0", nullable=True
        ),
        sa.Column(
            "material_advantage_white", sa.Float(), server_default="0", nullable=True
        ),
        sa.Column(
            "material_advantage_black", sa.Float(), server_default="0", nullable=True
        ),
        sa.Column("position_evaluation_final", sa.Float(), nullable=True),
        sa.Column(
            "tactical_motifs_count", sa.Integer(), server_default="0", nullable=True
        ),
        sa.Column("endgame_type", sa.String(length=50), nullable=True),
        sa.Column(
            "pawn_structure_score_white", sa.Float(), server_default="0", nullable=True
        ),
        sa.Column(
            "pawn_structure_score_black", sa.Float(), server_default="0", nullable=True
        ),
        sa.Column("king_safety_white", sa.Float(), server_default="0", nullable=True),
        sa.Column("king_safety_black", sa.Float(), server_default="0", nullable=True),
        sa.Column(
            "piece_activity_white", sa.Float(), server_default="0", nullable=True
        ),
        sa.Column(
            "piece_activity_black", sa.Float(), server_default="0", nullable=True
        ),
        sa.Column(
            "center_control_white", sa.Float(), server_default="0", nullable=True
        ),
        sa.Column(
            "center_control_black", sa.Float(), server_default="0", nullable=True
        ),
        sa.Column(
            "development_speed_white", sa.Float(), server_default="0", nullable=True
        ),
        sa.Column(
            "development_speed_black", sa.Float(), server_default="0", nullable=True
        ),
        sa.Column(
            "space_advantage_white", sa.Float(), server_default="0", nullable=True
        ),
        sa.Column(
            "space_advantage_black", sa.Float(), server_default="0", nullable=True
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("game_id"),
    )
    op.create_index(
        "idx_game_analytics_game_id", "game_analytics", ["game_id"], unique=False
    )
    op.create_index(
        "idx_game_analytics_source", "game_analytics", ["source"], unique=False
    )
    op.create_index(
        "idx_game_analytics_elo",
        "game_analytics",
        ["white_elo", "black_elo"],
        unique=False,
    )
    op.create_index(
        "idx_game_analytics_quality",
        "game_analytics",
        ["accuracy_white", "accuracy_black"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_game_analytics_quality", table_name="game_analytics")
    op.drop_index("idx_game_analytics_elo", table_name="game_analytics")
    op.drop_index("idx_game_analytics_source", table_name="game_analytics")
    op.drop_index("idx_game_analytics_game_id", table_name="game_analytics")
    op.drop_table("game_analytics")
