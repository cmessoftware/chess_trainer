"""Add users table with combinatorial roles

Revision ID: 20260211_000000
Revises: 20260131_233554
Create Date: 2026-02-11 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "20260211_000000"
down_revision = "20260131_233554"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("email", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("roles", postgresql.ARRAY(sa.String(50)), nullable=False, default=[]),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("last_login", sa.DateTime(), nullable=True),
        sa.Column("profile_data", postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
    )

    # Create user_sessions table for JWT management
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_jti", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_jti"),
    )

    # Create indexes for performance
    op.create_index("idx_users_username", "users", ["username"])
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_active", "users", ["is_active"])
    op.create_index("idx_sessions_user_id", "user_sessions", ["user_id"])
    op.create_index("idx_sessions_expires", "user_sessions", ["expires_at"])

    # Insert default admin user
    from sqlalchemy import text

    op.execute(
        text(
            """
        INSERT INTO users (username, email, password_hash, roles, is_active) 
        VALUES (
            'admin', 
            'admin@chess-trainer.com', 
            '$2b$12$LQv3c1yqBWVHxkd0LHAiMOJ6T9Gdy/1Uz8PyTKnM8YaARCXHkRmja', -- password: admin123
            ARRAY['admin'], 
            true
        )
    """
        )
    )


def downgrade() -> None:
    op.drop_index("idx_sessions_expires", table_name="user_sessions")
    op.drop_index("idx_sessions_user_id", table_name="user_sessions")
    op.drop_index("idx_users_active", table_name="users")
    op.drop_index("idx_users_email", table_name="users")
    op.drop_index("idx_users_username", table_name="users")
    op.drop_table("user_sessions")
    op.drop_table("users")
