"""add token usage table

Revision ID: 20250914_160000
Revises: 20250914_150000
Create Date: 2025-09-14 16:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '20250914_160000'
down_revision: Union[str, None] = '20250914_150000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create token_usage table
    op.create_table(
        'token_usage',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('request_uuid', sa.String(length=36), nullable=False),
        sa.Column('consumer', sa.String(length=100), nullable=False),
        sa.Column('model_id', sa.String(length=100), nullable=False),
        sa.Column('prompt_tokens', sa.Integer(), nullable=True),
        sa.Column('completion_tokens', sa.Integer(), nullable=True),
        sa.Column('total_tokens', sa.Integer(), nullable=True),
        sa.Column('input_cost', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('output_cost', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('total_cost', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('create_time', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('update_time', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8mb4_general_ci',
        mysql_charset='utf8mb4',
        mysql_comment='Token用量信息宽表'
    )

    # Create indexes
    op.create_index('idx_request_uuid', 'token_usage', ['request_uuid'])
    op.create_index('idx_model_id', 'token_usage', ['model_id'])
    op.create_index('idx_create_time', 'token_usage', ['create_time'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_create_time', table_name='token_usage')
    op.drop_index('idx_model_id', table_name='token_usage')
    op.drop_index('idx_request_uuid', table_name='token_usage')

    # Drop table
    op.drop_table('token_usage')