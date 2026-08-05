import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

# Establish safe test environment variables BEFORE importing app modules
os.environ["GEMINI_API_KEY"] = "test-gemini-api-key-12345"
os.environ["GITHUB_TOKEN"] = "test-github-token-67890"
os.environ["GITHUB_WEBHOOK_SECRET"] = "test-webhook-secret-abcde"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import app.models  # Register all ORM models on Base.metadata
from starlette.testclient import TestClient
from app.main import app as fastapi_app
from app.database import Base, get_db, SessionLocal, engine as db_engine


@pytest.fixture(autouse=True)
def setup_test_database():
    """Sets up a clean shared in-memory database schema for every test."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=test_engine)
    SessionLocal.configure(bind=test_engine)

    def _override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    yield
    fastapi_app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    SessionLocal.configure(bind=db_engine)


@pytest.fixture
def db_session():
    """Returns a test database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client() -> TestClient:
    """FastAPI TestClient fixture."""
    return TestClient(fastapi_app)


@pytest.fixture
def dummy_secret() -> str:
    """Dummy webhook secret matching os.environ."""
    return "test-webhook-secret-abcde"
