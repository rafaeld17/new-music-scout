"""
Pytest configuration and fixtures for Music Scout tests.
"""
import pytest
from sqlmodel import SQLModel, create_engine, Session
from src.music_scout.models import Source, MusicItem, Artist, Album
from src.music_scout.services import SourceManager, IngestionService


@pytest.fixture
def test_engine():
    """Create a test database engine using SQLite in memory."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_session(test_engine):
    """Create a test database session."""
    with Session(test_engine) as session:
        yield session


@pytest.fixture
def source_manager(test_session):
    """Create a SourceManager instance for testing."""
    return SourceManager(test_session)


@pytest.fixture
def ingestion_service(test_session):
    """Create an IngestionService instance for testing."""
    return IngestionService(test_session)


@pytest.fixture
def sample_source(test_session):
    """Create a sample source for testing."""
    source = Source(
        name="Test Source",
        url="https://example.com/feed/",
        source_type="rss",
        weight=1.0,
        enabled=True
    )
    test_session.add(source)
    test_session.commit()
    test_session.refresh(source)
    return source


@pytest.fixture
def sample_rss_entry():
    """Sample RSS entry data for testing."""
    from types import SimpleNamespace
    import time

    entry = SimpleNamespace()
    entry.title = "Porcupine Tree - Closure/Continuation Review"
    entry.link = "https://example.com/porcupine-tree-review"
    entry.summary = "An excellent return to form for the progressive rock legends."
    entry.author = "Test Reviewer"
    entry.published_parsed = time.struct_time((2023, 1, 15, 10, 30, 0, 0, 15, 0))

    return entry