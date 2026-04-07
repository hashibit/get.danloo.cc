from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Import common database base
from common.database_models import CommonBase

# Database configuration
DATABASE_URL = os.environ.get("DATABASE_URL", "mysql+pymysql://danloo:password@db:3306/danloo")

# Lazy initialization for database connection
engine = None
SessionLocal = None

def get_engine():
    """Lazy initialize database engine"""
    global engine, SessionLocal
    if engine is None:
        engine = create_engine(
            DATABASE_URL,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine

# Use common base for models
Base = CommonBase


def get_database():
    """Get database session dependency for FastAPI"""
    get_engine()  # Ensure engine is initialized
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
