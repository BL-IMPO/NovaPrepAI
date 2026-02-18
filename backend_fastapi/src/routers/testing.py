from pathlib import Path

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from asgiref.sync import sync_to_async

from ..dependencies import get_current_user


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

# Initialize test utils
test_ort = utils.TestORT()

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "ORT Testing API", "status": "running"}

@router.get("/api/test/types")
async def get_test_types():
    """Get available test types"""
    return {
        "standard_tests": [
            {"id": "math_1", "name": "Math 1", "questions": 30, "time": 60},
            {"id": "math_2", "name": "Math 2", "questions": 30, "time": 60},
            {"id": "analogy", "name": "Analogy", "questions": 30, "time": 30},
            {"id": "reading", "name": "Reading", "questions": 30, "time": 60},
            {"id": "grammar", "name": "Grammar", "questions": 30, "time": 30},
            {"id": "full_test", "name": "Full Test", "questions": 150, "time": 180}
        ],
        "special_tests": [
            {"id": "special_math", "name": "Mathematics", "questions": 40, "time": 90},
            {"id": "special_biology", "name": "Biology", "questions": 40, "time": 90},
            {"id": "special_chemistry", "name": "Chemistry", "questions": 40, "time": 90},
            {"id": "special_english", "name": "English", "questions": 40, "time": 90},
            {"id": "special_history", "name": "History", "questions": 40, "time": 90},
            {"id": "special_physics", "name": "Physics", "questions": 40, "time": 90},
            {"id": "special_russian_grammar", "name": "Russian Grammar", "questions": 40, "time": 90},
            {"id": "special_kyrgyz_grammar", "name": "Kyrgyz Grammar", "questions": 40, "time": 90}
        ]
    }

@router.get("/testing/{test_type}", response_class=HTMLResponse)
async def testing_page(request: Request, test_type: str):
    """Serve the testing interface for a specific test type"""
    try:
        # Validate test type exists
        test_data = test_ort.get_test_data(test_type)

        return templates.TemplateResponse("testing.html",
                                      {"request": request,
                                       "test_type": test_type,
                                       "test_name": test_type.replace('_', ' ').title()})
    except ValueError as e:
        # Return 404 if test type not found
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"Error serving testing page: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/api/test/{test_type}")
async def get_test_data(test_type: str):
    """Get test data including questions and time limit.
        Hides complexity scores from frontend"""
    try:
        raw_data = test_ort.get_test_data(test_type)

        # Clean the questions from complexity score
        cleaned_questions = {}
        for question_text, options in raw_data["questions"].items():
            extra_data = options.pop(-1)  # 1. Take out extra_data
            options.pop(-1)  # 2. Take out the hidden score
            options.append(extra_data)  # 3. Put extra_data back at the end
            cleaned_questions[question_text] = options

        return {
            "time_limit": raw_data["time_limit"],
            "questions": cleaned_questions,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/api/test/submit")
async def submit_test(submission: schemas.TestSubmission,
                      current_user = Depends(get_current_user)):
    try:
        # 1. Use data directly from the Pydantic model (No need for request.json)
        test_type = submission.test_type

        # 2. Validation
        if not test_type:
            raise HTTPException(status_code=400, detail="Test type is required")

        # Get test data for validation
        test_data = test_ort.get_test_data(test_type)
        questions = list(test_data["questions"].items())

        # Initializing scores
        base_score = 0
        weighted_score = 0.0

        details = []

        for idx, (question, options) in enumerate(questions):
            # 3. Access answers safely
            # Note: JSON keys are always strings, but our loop index is int.
            options.pop(-1)
            answer_options = options.copy()[0:-1]
            # Get specific points for answer
            question_points = float(options[-1])

            # We try both just to be safe.
            user_answer_idx = submission.answers.get(str(idx))
            if user_answer_idx is None:
                user_answer_idx = submission.answers.get(idx)

            # Convert string input to int if necessary
            if isinstance(user_answer_idx, str):
                try:
                    user_answer_idx = int(user_answer_idx)
                except (ValueError, TypeError):
                    user_answer_idx = None
            elif not isinstance(user_answer_idx, int):
                user_answer_idx = None

            is_correct = (user_answer_idx is not None and user_answer_idx == 0)

            if is_correct:
                base_score += 1
                weighted_score += question_points

            #if user_answer_idx is not None and user_answer_idx == 0:
                # First answer (index 0) is always the correct one in this engine
            #    score += 1

            details.append({
                "question": question,
                "user_answer": user_answer_idx,
                "correct_answer": 0,
                "answers": answer_options,
                "is_correct": user_answer_idx == 0,
            })

        # Calculate if passed (60% threshold)
        total_questions = len(questions)
        passed = (base_score / total_questions) >= 0.6 if total_questions > 0 else False

        # --- DB Operations Wrapper ---
        def db_save_attempt():
            # Create attempt
            return TestAttempt.objects.create(
                user=current_user,
                test_type=submission.test_type,
                score=base_score,
                weighted_score=round(weighted_score, 2),
                passed=passed,
                details=details,
            )

        # Execute the DB operation in a thread safe way
        test_attempt = await sync_to_async(db_save_attempt)()

        return {
            "success": True,
            "score": base_score,
            "weighted_score": round(weighted_score, 2),
            "total": total_questions,
            "percentage": (base_score / total_questions * 100) if total_questions > 0 else 0,
            "passed": passed,
            "attempt_id": test_attempt.id
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error submitting test: {str(e)}")

@router.get("/test-info/{test_type}", response_class=HTMLResponse)
async def test_info_page(request: Request, test_type:str):
    """Show test information before starting."""
    description = utils.Description()

    if test_type not in description.get_test_types():
        raise HTTPException(status_code=404, detail="Test type not found")

    test_info = description.get_test_description(test_type)
    return templates.TemplateResponse(
        "test_info.html",
        {
            "request": request,
            "test_type": test_type,
            "test_info": test_info,
        }
    )
