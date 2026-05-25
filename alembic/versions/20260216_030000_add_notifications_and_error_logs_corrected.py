"""Add notifications and error_logs tables with corrected column names

Revision ID: 20260216_030000
Revises: 20260213_231617
Create Date: 2026-02-16 03:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260216_030000'
down_revision: Union[str, None] = '20260213_231617'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create notifications and error_logs tables."""
    
    # Drop tables if they exist (cleanup from previous attempt)
    op.execute("DROP TABLE IF EXISTS public.notifications CASCADE")
    op.execute("DROP TABLE IF EXISTS public.error_logs CASCADE")
    
    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('dismissed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('meta_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_log_id', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='public'
    )
    
    # Create indexes for notifications
    op.create_index(
        op.f('ix_notifications_user_id'), 
        'notifications', 
        ['user_id'], 
        unique=False,
        schema='public'
    )
    op.create_index(
        op.f('ix_notifications_error_log_id'), 
        'notifications', 
        ['error_log_id'], 
        unique=False,
        schema='public'
    )
    
    # Create error_logs table
    op.create_table(
        'error_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('error_type', sa.String(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('stack_trace', sa.Text(), nullable=True),
        sa.Column('meta_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('resolved', sa.String(), nullable=False, server_default='open'),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='public'
    )
    
    # Create indexes for error_logs
    op.create_index(
        op.f('ix_error_logs_user_id'), 
        'error_logs', 
        ['user_id'], 
        unique=False,
        schema='public'
    )


def downgrade() -> None:
    """Drop notifications and error_logs tables."""
    op.drop_index(op.f('ix_error_logs_user_id'), table_name='error_logs', schema='public')
    op.drop_table('error_logs', schema='public')
    
    op.drop_index(op.f('ix_notifications_error_log_id'), table_name='notifications', schema='public')
    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications', schema='public')
    op.drop_table('notifications', schema='public')
