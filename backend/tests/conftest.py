import os
import pytest

# Establish safe test environment variables BEFORE importing app modules
os.environ["GEMINI_API_KEY"] = "test-gemini-api-key-12345"
os.environ["GITHUB_TOKEN"] = "test-github-token-67890"
os.environ["GITHUB_WEBHOOK_SECRET"] = "test-webhook-secret-abcde"

from starlette.testclient import TestClient
from app.main import app


@pytest.fixture
def client() -> TestClient:
    """FastAPI TestClient fixture."""
    return TestClient(app)


@pytest.fixture
def dummy_secret() -> str:
    """Dummy webhook secret matching os.environ."""
    return "test-webhook-secret-abcde"
