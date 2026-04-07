"""
Common database base for all shared models - SQLAlchemy 2.0 style
"""

from sqlalchemy.orm import DeclarativeBase
from typing import Any


# Base class for all common database models using modern SQLAlchemy 2.0 syntax
class CommonBase(DeclarativeBase):
    """Base class for all shared database models with SQLAlchemy 2.0 support"""

    pass
