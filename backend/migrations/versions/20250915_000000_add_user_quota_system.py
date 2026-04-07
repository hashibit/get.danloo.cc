"""add user quota system tables

Revision ID: 20250915_000000
Revises: 20250914_160000
Create Date: 2025-09-15 00:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '20250915_000000'
down_revision: Union[str, None] = '20250914_160000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_quotas table
    op.create_table(
        'user_quotas',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('quota_type', sa.String(length=50), nullable=False, server_default='credits'),
        sa.Column('daily_limit', sa.Numeric(precision=15, scale=6), nullable=False, server_default='0.0'),
        sa.Column('used_amount', sa.Numeric(precision=15, scale=6), nullable=False, server_default='0.0'),
        sa.Column('reset_date', sa.Date(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8mb4_0900_ai_ci',
        mysql_charset='utf8mb4',
        mysql_comment='User daily quota tracking table'
    )

    # Create quota_usage_logs table
    op.create_table(
        'quota_usage_logs',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('quota_type', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=6), nullable=False),
        sa.Column('operation_type', sa.String(length=20), nullable=False),
        sa.Column('related_request_uuid', sa.String(length=36), nullable=True),
        sa.Column('quota_before', sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column('quota_after', sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8mb4_0900_ai_ci',
        mysql_charset='utf8mb4',
        mysql_comment='Quota usage operation log table'
    )

    # Create indexes for user_quotas table
    op.create_index('idx_user_quota_date', 'user_quotas', ['user_id', 'quota_type', 'reset_date'], unique=True)
    op.create_index('idx_reset_date', 'user_quotas', ['reset_date'])
    op.create_index('idx_user_active', 'user_quotas', ['user_id', 'is_active'])
    op.create_index('idx_quota_type', 'user_quotas', ['quota_type'])

    # Create indexes for quota_usage_logs table
    op.create_index('idx_user_date', 'quota_usage_logs', ['user_id', 'created_at'])
    op.create_index('idx_request_uuid', 'quota_usage_logs', ['related_request_uuid'])
    op.create_index('idx_operation_type', 'quota_usage_logs', ['operation_type'])
    op.create_index('idx_quota_type_log', 'quota_usage_logs', ['quota_type'])
    op.create_index('idx_created_at', 'quota_usage_logs', ['created_at'])


def downgrade() -> None:
    # Drop indexes for quota_usage_logs table
    op.drop_index('idx_created_at', table_name='quota_usage_logs')
    op.drop_index('idx_quota_type_log', table_name='quota_usage_logs')
    op.drop_index('idx_operation_type', table_name='quota_usage_logs')
    op.drop_index('idx_request_uuid', table_name='quota_usage_logs')
    op.drop_index('idx_user_date', table_name='quota_usage_logs')

    # Drop indexes for user_quotas table
    op.drop_index('idx_quota_type', table_name='user_quotas')
    op.drop_index('idx_user_active', table_name='user_quotas')
    op.drop_index('idx_reset_date', table_name='user_quotas')
    op.drop_index('idx_user_quota_date', table_name='user_quotas')

    # Drop tables (order matters due to foreign keys)
    op.drop_table('quota_usage_logs')
    op.drop_table('user_quotas')