"""
pytest configuration and fixtures
"""

import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base

# Import models from common for testing
from common.database_models import UserDB, MaterialDB, ObjectDB, TagDB, PelletDB


@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test function"""
    # Create temporary database file
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.close()

    # Create test database URL
    test_db_url = f"sqlite:///{temp_file.name}"

    # Create engine for test database
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})

    # Create all tables (testing only - production uses Alembic migrations)
    Base.metadata.create_all(bind=engine)

    # Create session factory
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    yield TestingSessionLocal, engine

    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    os.unlink(temp_file.name)


@pytest.fixture
def db_session(test_db):
    """Create a database session for testing"""
    TestingSessionLocal, engine = test_db
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
