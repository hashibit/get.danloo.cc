"""Complete unified schema - all tables and features in one migration

Revision ID: 20250909_000000
Revises: 
Create Date: 2025-09-09 00:00:00.000000

This migration replaces all previous migrations and creates the complete
database schema with all features:
- Core tables: users, materials, pellets, tags, crypto_keys, objects
- Process service: jobs, tasks  
- Associations: pellet_tags, pellet_counters
- Visibility system: pellets.visibility field with indexes
- All foreign key constraints and indexes

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250909_000000'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create complete database schema with all features."""
    
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("exp_level", sa.String(10), server_default="1", nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_0900_ai_ci',
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    # Create objects table
    op.create_table(
        "objects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("s3_path", sa.String(512), nullable=False),
        sa.Column("presigned_url", sa.Text(), nullable=True),
        sa.Column("file_info", sa.JSON(), nullable=True),
        sa.Column(
            "is_uploaded", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("idx_objects_is_uploaded", "objects", ["is_uploaded"])
    op.create_index("idx_objects_created_at", "objects", ["created_at"])
    op.create_index("idx_objects_s3_path", "objects", ["s3_path"])

    # Create materials table
    op.create_table(
        "materials",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("object_id", sa.String(36), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["object_id"], 
            ["objects.id"], 
            ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_materials_id", "materials", ["id"], unique=False)
    op.create_index("ix_materials_user_id", "materials", ["user_id"], unique=False)
    op.create_index("ix_materials_object_id", "materials", ["object_id"], unique=False)

    # Create tags table
    op.create_table(
        "tags",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("color", sa.String(20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tags_id"), "tags", ["id"], unique=False)
    op.create_index(op.f("ix_tags_name"), "tags", ["name"], unique=True)

    # Create pellets table with visibility field
    op.create_table(
        "pellets",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("material_ids", sa.Text(), nullable=True),
        sa.Column("title", sa.String(255), nullable=True),  
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("visibility", sa.String(10), server_default="private", nullable=False),  # New field
        sa.Column(
            "status", sa.String(50), server_default="in-queue", nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        # AI-related fields
        sa.Column("ai_score", sa.Float(), nullable=True),
        sa.Column("pellet_type", sa.String(50), nullable=True),
        sa.Column("generation_metadata", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pellets_id", "pellets", ["id"], unique=False)
    op.create_index("ix_pellets_user_id", "pellets", ["user_id"], unique=False)
    # Visibility indexes for permission system
    op.create_index("ix_pellets_visibility", "pellets", ["visibility"], unique=False)
    op.create_index("ix_pellets_public_created", "pellets", ["visibility", "created_at"], unique=False)

    # Create pellet_counters table
    op.create_table(
        "pellet_counters",
        sa.Column("pellet_id", sa.String(36), nullable=False),
        sa.Column(
            "view_count", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "like_count", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "estimated_read_time",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "referenced_material_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "referenced_job_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "referenced_pellet_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "referenced_by_pellet_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["pellet_id"], ["pellets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("pellet_id"),
    )
    op.create_index(
        "ix_pellet_counters_pellet_id", "pellet_counters", ["pellet_id"], unique=True
    )

    # Create pellet_tags association table
    op.create_table(
        "pellet_tags",
        sa.Column("pellet_id", sa.String(36), nullable=False),
        sa.Column("tag_id", sa.String(36), nullable=False),
        sa.ForeignKeyConstraint(
            ["pellet_id"],
            ["pellets.id"],
            ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["tag_id"],
            ["tags.id"],
            ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("pellet_id", "tag_id"),
    )

    # Create crypto_keys table
    op.create_table(
        "crypto_keys",
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("access_key", sa.Text(), nullable=False),
        sa.Column("secret_key", sa.Text(), nullable=False),
        sa.Column("hash_key", sa.Text(), nullable=False),
        sa.Column("salt", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index(
        op.f("ix_crypto_keys_user_id"), "crypto_keys", ["user_id"], unique=False
    )

    # Create jobs table
    op.create_table(
        "jobs",
        sa.Column("job_id", sa.String(36), nullable=False),
        sa.Column(
            "job_type",
            sa.String(50),
            nullable=False,
            server_default="material_processing",
        ),
        sa.Column("status", sa.String(50), nullable=True, server_default="pending"),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("job_metadata", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("job_id"),
    )
    op.create_index("ix_jobs_job_id", "jobs", ["job_id"], unique=False)
    op.create_index("ix_jobs_user_id", "jobs", ["user_id"], unique=False)
    op.create_index("ix_jobs_status", "jobs", ["status"], unique=False)

    # Create tasks table with object_id and content_type fields
    op.create_table(
        "tasks",
        sa.Column("task_id", sa.String(36), nullable=False),
        sa.Column("job_id", sa.String(36), nullable=False),
        sa.Column("material_id", sa.String(36), nullable=False),
        sa.Column("object_id", sa.String(36), nullable=True),  # New field
        sa.Column("content_type", sa.String(50), nullable=True),  # New field
        sa.Column(
            "task_type",
            sa.String(50),
            nullable=False,
            server_default="PROCESS_MATERIAL",
        ),
        sa.Column("status", sa.String(50), nullable=True, server_default="pending"),
        sa.Column("result", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.String(10), nullable=True, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.job_id"],
        ),
        sa.ForeignKeyConstraint(
            ["material_id"],
            ["materials.id"],
            ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["object_id"],
            ["objects.id"],
            ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("task_id"),
    )
    op.create_index("ix_tasks_task_id", "tasks", ["task_id"], unique=False)
    op.create_index("ix_tasks_job_id", "tasks", ["job_id"], unique=False)
    op.create_index("ix_tasks_material_id", "tasks", ["material_id"], unique=False)
    op.create_index("ix_tasks_object_id", "tasks", ["object_id"], unique=False)
    op.create_index("ix_tasks_status", "tasks", ["status"], unique=False)



def downgrade():
    """Drop all tables."""
    # Drop tables in reverse order to handle foreign key constraints
    op.drop_table("tasks")
    op.drop_table("jobs")
    op.drop_table("crypto_keys")
    op.drop_table("pellet_tags")
    op.drop_table("pellet_counters")
    op.drop_table("pellets")
    op.drop_table("tags")
    op.drop_table("materials")
    op.drop_table("objects")
    op.drop_table("users")