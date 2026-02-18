import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock, AsyncMock

# Adjust these imports to match your project structure
from src.app import app
from ..dependencies import get_current_user


# --- 1. Authentication Mock ---
async def override_get_current_user():
    """Mock the logged-in user so we don't need real JWT tokens."""
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.email = "student@novaprep.com"
    return mock_user


# --- 2. Async Client Fixture ---
@pytest_asyncio.fixture
async def async_client():
    app.dependency_overrides[get_current_user] = override_get_current_user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


# --- 3. The Tests ---

@pytest.mark.asyncio
@patch('src.routers.results.sync_to_async')
async def test_results_page_html(mock_sync_to_async, async_client: AsyncClient):
    """Test that the HTML template route loads successfully."""

    # Mock the database check for the attempt
    mock_attempt = MagicMock()
    mock_attempt.id = 999
    mock_attempt.user.id = 1

    # Provide a dummy string for details so json.loads() doesn't crash in results.py
    mock_attempt.details = "[]"

    mock_sync_to_async.return_value = AsyncMock(return_value=mock_attempt)

    # Call your actual HTML route
    response = await async_client.get("/results/999/math_1")

    # Verify the HTML page loads
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]