"""
Integration tests for the FastAPI application.
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session

from src.music_scout.main import app
from src.music_scout.core.database import get_session


@pytest.fixture
def test_db():
    """Create test database for integration tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False}  # Allow SQLite to be used across threads
    )
    SQLModel.metadata.create_all(engine)

    def get_test_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session
    yield engine
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db):
    """Create test client."""
    return TestClient(app)


def test_health_check(client):
    """Test basic health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "New Music Scout"
    assert data["version"] == "0.1.0"


def test_database_health_check(client):
    """Test database health check endpoint."""
    response = client.get("/api/health/db")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"