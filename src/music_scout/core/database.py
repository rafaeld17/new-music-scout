"""
Database connection and session management.
"""
from sqlmodel import SQLModel, create_engine, Session
from .config import settings

# Create database engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,  # Log SQL queries in debug mode
    pool_pre_ping=True,   # Verify connections before use
)


def create_db_and_tables():
    """Create database tables based on SQLModel definitions."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get a database session for dependency injection."""
    with Session(engine) as session:
        yield session