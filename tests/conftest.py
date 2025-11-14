"""
Pytest configuration and fixtures
"""
import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

# Set test environment variables
os.environ["API_BEARER_TOKEN"] = "test_token"
os.environ["GEMINI_API_KEY"] = "test_gemini_key"

from app import app

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

@pytest.fixture
def mock_gemini_service():
    """Mock Gemini service"""
    with patch('app.gemini_service') as mock:
        yield mock

@pytest.fixture
def mock_content_service():
    """Mock content service"""
    with patch('app.content_service') as mock:
        yield mock

@pytest.fixture
def mock_cache_service():
    """Mock cache service"""
    with patch('app.cache_service') as mock:
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock()
        yield mock

@pytest.fixture
def auth_headers():
    """Authorization headers for testing"""
    return {"Authorization": "Bearer test_token"}

@pytest.fixture
def test_domain():
    """
    Test domain URL - can be configured via TEST_DOMAIN env variable
    Default: https://m.cnyes.com/news/id/5627491
    """
    return os.getenv("TEST_DOMAIN", "https://m.cnyes.com/news/id/5627491")

@pytest.fixture
def test_base_url():
    """
    Test base URL for domain extraction tests
    Default: https://m.cnyes.com
    """
    return os.getenv("TEST_BASE_URL", "https://m.cnyes.com")

