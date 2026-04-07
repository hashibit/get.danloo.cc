"""Add phone and wechat login support

Revision ID: 20250914_150000
Revises: 20250909_000000
Create Date: 2025-09-14 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250914_150000'
down_revision = '20250909_000000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to users table
    op.add_column('users', sa.Column('phone_number', sa.String(20), nullable=True))
    op.add_column('users', sa.Column('phone_verified', sa.Boolean(), default=False))
    op.add_column('users', sa.Column('wechat_openid', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('wechat_unionid', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('wechat_nickname', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('wechat_avatar', sa.String(500), nullable=True))

    # Make email field nullable to support social login
    op.alter_column('users', 'email',
               existing_type=sa.String(length=255),
               nullable=True)

    # Create verification_codes table
    op.create_table('verification_codes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('phone_number', sa.String(20), nullable=False),
        sa.Column('code', sa.String(10), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),  # 'login', 'register', 'phone_verification'
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_used', sa.Boolean(), default=False),
        sa.Column('attempts', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index for phone_number and type
    op.create_index('idx_verification_codes_phone_type', 'verification_codes', ['phone_number', 'type'])
    op.create_index('idx_verification_codes_expires_at', 'verification_codes', ['expires_at'])

    # Create user_social_accounts table for future social login expansion
    op.create_table('user_social_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),  # 'wechat', 'github', 'google', etc.
        sa.Column('provider_user_id', sa.String(255), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=True),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('scope', sa.Text(), nullable=True),
        sa.Column('raw_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create unique index for provider and provider_user_id
    op.create_index('idx_user_social_accounts_provider_user_id', 'user_social_accounts',
                     ['provider', 'provider_user_id'], unique=True)


def downgrade() -> None:
    # Drop tables
    op.drop_table('user_social_accounts')
    op.drop_table('verification_codes')

    # Drop indexes
    op.drop_index('idx_verification_codes_phone_type', table_name='verification_codes')
    op.drop_index('idx_verification_codes_expires_at', table_name='verification_codes')
    op.drop_index('idx_user_social_accounts_provider_user_id', table_name='user_social_accounts')

    # Drop columns
    op.drop_column('users', 'wechat_avatar')
    op.drop_column('users', 'wechat_nickname')
    op.drop_column('users', 'wechat_unionid')
    op.drop_column('users', 'wechat_openid')
    op.drop_column('users', 'phone_verified')
    op.drop_column('users', 'phone_number')

    # Revert email field to not nullable (restore original constraint)
    op.alter_column('users', 'email',
               existing_type=sa.String(255),
               nullable=False)
