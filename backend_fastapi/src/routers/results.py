from pathlib import Path

from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from asgiref.sync import sync_to_async


# Now import Django models
try:
    from django.contrib.auth import get_user_model
    from main.models import TestAttempt
    print("Successfully imported Django models")
except Exception as e:
    print(f"Error importing Django models: {e}")
    raise

from src.schemas import schemas
from .. import utils

# Mount static files
frontend_path = Path("/usr/share/nginx/html")
if not frontend_path.exists():
    # Fallback for development
    frontend_path = Path(__file__).resolve().parent.parent.parent.parent.parent / 'frontend'

# Templates
templates = Jinja2Templates(directory=frontend_path)

router = APIRouter()

@router.get("/results/{attempt_id}/{test_type}", response_class=HTMLResponse)
async def results_page(request: Request, attempt_id: int, test_type: str):
    """Show results for a specific test attempt"""
    try:
        def db_get_details():
            return TestAttempt.objects.get(id=attempt_id, test_type=test_type)

        attempt = await sync_to_async(db_get_details)()

    except TestAttempt.DoesNotExist:
        raise HTTPException(status_code=404, detail="Attempt not found")

    # Convert attempt.details to a list if it's not already
    details = attempt.details
    if isinstance(details, str):
        import json
        details = json.loads(details)

    return templates.TemplateResponse(
        "results.html",
        {
            "request": request,
            "attempt": attempt,
            "details": details,
            "test_type": test_type,
        }
    )
