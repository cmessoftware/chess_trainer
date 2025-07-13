"""Create features and tactical tables

Revision ID: create_features_tables
Revises:
Create Date: 2025-07-13 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "create_features_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create games table
    op.create_table(
        "games",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("pgn", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("white_player", sa.String(length=255), nullable=True),
        sa.Column("black_player", sa.String(length=255), nullable=True),
        sa.Column("white_elo", sa.Integer(), nullable=True),
        sa.Column("black_elo", sa.Integer(), nullable=True),
        sa.Column("result", sa.String(length=20), nullable=True),
        sa.Column("time_control", sa.String(length=50), nullable=True),
        sa.Column("opening", sa.String(length=200), nullable=True),
        sa.Column("eco", sa.String(length=10), nullable=True),
        sa.Column("date_played", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_games_source", "games", ["source"], unique=False)
    op.create_index("idx_games_elo", "games", ["white_elo", "black_elo"], unique=False)
    op.create_index("idx_games_result", "games", ["result"], unique=False)

    # Create features table
    op.create_table(
        "features",
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
    op.create_index("idx_features_game_id", "features", ["game_id"], unique=False)
    op.create_index("idx_features_source", "features", ["source"], unique=False)
    op.create_index(
        "idx_features_elo", "features", ["white_elo", "black_elo"], unique=False
    )

    # Create analyzed_tacticals table
    op.create_table(
        "analyzed_tacticals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.String(length=255), nullable=False),
        sa.Column("move_number", sa.Integer(), nullable=False),
        sa.Column("color", sa.String(length=10), nullable=False),
        sa.Column("tactic_type", sa.String(length=100), nullable=False),
        sa.Column("evaluation_before", sa.Float(), nullable=True),
        sa.Column("evaluation_after", sa.Float(), nullable=True),
        sa.Column("centipawn_difference", sa.Float(), nullable=True),
        sa.Column("move_played", sa.String(length=20), nullable=False),
        sa.Column("best_move", sa.String(length=20), nullable=True),
        sa.Column("position_fen", sa.Text(), nullable=True),
        sa.Column("tactical_motif", sa.String(length=100), nullable=True),
        sa.Column("difficulty_score", sa.Float(), nullable=True),
        sa.Column("time_spent", sa.Float(), nullable=True),
        sa.Column("is_blunder", sa.Boolean(), server_default="false", nullable=True),
        sa.Column("is_mistake", sa.Boolean(), server_default="false", nullable=True),
        sa.Column("is_inaccuracy", sa.Boolean(), server_default="false", nullable=True),
        sa.Column("is_brilliant", sa.Boolean(), server_default="false", nullable=True),
        sa.Column("is_good", sa.Boolean(), server_default="false", nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_tacticals_game_id", "analyzed_tacticals", ["game_id"], unique=False
    )
    op.create_index(
        "idx_tacticals_type", "analyzed_tacticals", ["tactic_type"], unique=False
    )
    op.create_index(
        "idx_tacticals_motif", "analyzed_tacticals", ["tactical_motif"], unique=False
    )

    # Create processed_features table
    op.create_table(
        "processed_features",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.String(length=255), nullable=False),
        sa.Column(
            "processed_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("game_id"),
    )
    op.create_index(
        "idx_processed_game_id", "processed_features", ["game_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("idx_processed_game_id", table_name="processed_features")
    op.drop_table("processed_features")
    op.drop_index("idx_tacticals_motif", table_name="analyzed_tacticals")
    op.drop_index("idx_tacticals_type", table_name="analyzed_tacticals")
    op.drop_index("idx_tacticals_game_id", table_name="analyzed_tacticals")
    op.drop_table("analyzed_tacticals")
    op.drop_index("idx_features_elo", table_name="features")
    op.drop_index("idx_features_source", table_name="features")
    op.drop_index("idx_features_game_id", table_name="features")
    op.drop_table("features")
    op.drop_index("idx_games_result", table_name="games")
    op.drop_index("idx_games_elo", table_name="games")
    op.drop_index("idx_games_source", table_name="games")
    op.drop_table("games")
