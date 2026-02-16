import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock, MagicMock

from src.app import app


# Create a fixture for the async client
@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_root(async_client: AsyncClient):
    response = await async_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "ORT Testing API", "status": "running"}

@pytest.mark.asyncio
async def test_get_test_types(async_client: AsyncClient):
    """ Test the test types endpoint asynchronously"""
    response = await async_client.get("/api/test/types")
    assert response.status_code == 200
    data = response.json()
    assert "standard_tests" in data
    assert any(test["id"] == "math_1" for test in data["standard_tests"])

@pytest.mark.asyncio
async def test_get_test_data_success(async_client: AsyncClient):
    """ Test fetching data for a valid test asynchronously"""
    response = await async_client.get("/api/test/math_1")
    assert response.status_code == 200
    data = response.json()
    assert "time_limit" in data
    assert "questions" in data

@pytest.mark.asyncio
@patch('src.routers.testing.sync_to_async')
async def test_submit_test(mock_sync_to_async, async_client: AsyncClient):
    """Test submitting a test asynchronously with database mocking"""

    # Setup mock database
    mock_attempt = MagicMock()
    mock_attempt.id = 999
    mock_sync_to_async.return_value = AsyncMock(return_value=mock_attempt)

    # Setup payload
    payload = {
        "test_type": "math_1",
        "answers": {
            "0": 0,
            "1": 1,
        }
    }

    # Make the ASYNC request
    response = await async_client.post("/api/test/submit", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["attempt_id"] == 999
    assert data["score"] == 1
