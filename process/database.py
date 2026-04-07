from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Import database models from common
from common.database_models.job_model import JobDB
from common.database_models.task_model import TaskDB
from common.database_models.token_usage_model import TokenUsageDB
from common.database_models.base import CommonBase

# Database configuration
DATABASE_URL = os.environ.get(
    "PROCESS_DATABASE_URL", "mysql+pymysql://root:root@localhost:3306/process_db"
)

# Create database engine with connection pooling settings
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Use common base for models
Base = CommonBase


def get_database():
    """Get database session dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Database tables are managed by Alembic migrations
