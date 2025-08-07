import pytest
from fastapi.testclient import TestClient
from app.server import app # Import your FastAPI app instance

@pytest.fixture(scope="module")
def test_client():
    """Create a TestClient instance for the app."""
    client = TestClient(app)
    yield client