"""add email_verified field

Revision ID: 20251013_000000
Revises: 20251009_000000
Create Date: 2025-10-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251013_000000'
down_revision = '20251009_000000'
branch_labels = None
depends_on = None


def upgrade():
    # Add email_verified column to users table
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    # Remove email_verified column from users table
    op.drop_column('users', 'email_verified')
