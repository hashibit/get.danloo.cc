"""add blacklist table

Revision ID: 20251009_000000
Revises: 20250915_000000
Create Date: 2025-10-09 00:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '20251009_000000'
down_revision: Union[str, None] = '20250915_000000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create blacklist table
    op.create_table(
        'blacklist',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('identifier', sa.String(length=255), nullable=False, comment='IP address or user ID'),
        sa.Column('type', sa.Enum('ip', 'user', name='blacklisttype'), nullable=False, comment='Type of blacklist entry: ip or user'),
        sa.Column('reason', sa.Text(), nullable=False, comment='Reason for blacklisting'),
        sa.Column('created_by', sa.String(length=255), nullable=False, comment='Admin or system that created this entry'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1', comment='Whether this blacklist entry is active'),
        sa.Column('extra_data', sa.Text(), nullable=True, comment='JSON metadata for additional information'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='When this entry was created'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True, comment='When this entry expires (NULL for permanent)'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='Last update time'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8mb4_0900_ai_ci',
        mysql_charset='utf8mb4',
        mysql_comment='Blacklist table for IP and user blocking'
    )

    # Create indexes
    op.create_index('ix_blacklist_id', 'blacklist', ['id'])
    op.create_index('ix_blacklist_identifier', 'blacklist', ['identifier'])
    op.create_index('ix_blacklist_type', 'blacklist', ['type'])
    op.create_index('ix_blacklist_is_active', 'blacklist', ['is_active'])
    op.create_index('ix_blacklist_expires_at', 'blacklist', ['expires_at'])

    # Create compound index for efficient lookups
    op.create_index('ix_blacklist_type_identifier_active', 'blacklist', ['type', 'identifier', 'is_active'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_blacklist_type_identifier_active', table_name='blacklist')
    op.drop_index('ix_blacklist_expires_at', table_name='blacklist')
    op.drop_index('ix_blacklist_is_active', table_name='blacklist')
    op.drop_index('ix_blacklist_type', table_name='blacklist')
    op.drop_index('ix_blacklist_identifier', table_name='blacklist')
    op.drop_index('ix_blacklist_id', table_name='blacklist')

    # Drop table
    op.drop_table('blacklist')
