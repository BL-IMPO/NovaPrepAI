import asyncio
import json
from pathlib import Path
import redis
import os
from dotenv import load_dotenv

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse
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

redis_url = os.environ.get("REDIS_URL")
redis_client = redis.Redis.from_url(redis_url, decode_responses=True)

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
    if test_type not in test_ort.test_time_limits:
        raise HTTPException(status_code=404, detail="Test type not found")

    return templates.TemplateResponse("testing.html",
                                      {
                                          "request": request,
                                          "test_type": test_type,
                                          "test_name": test_type.replace('_', ' ')
                                      })


@router.get("/api/test/{test_type}")
async def get_test_data(test_type: str, current_user = Depends(get_current_user)):
    """Get test data including questions and time limit.
        Hides complexity scores from frontend"""
    try:
        cache_key = f"ort_test:{current_user.id}:{test_type}"
        cached_data = redis_client.get(cache_key)

        if cached_data:
            print(f"Returning cached test for user {current_user.id}")
            questions = json.loads(cached_data)
            total_questions = len(questions)

            time_limit = test_ort.test_time_limits.get(test_type, 60)

            async def cached_stream_generator():
                # Send metadata first
                yield json.dumps({"type": "meta", "time_limit": time_limit, "total_questions": total_questions}) + "\n"

                for idx, q_data in enumerate(questions):
                    if q_data:
                        yield json.dumps({
                            "type": "question",
                            "index": idx,
                            "question": q_data["question"],
                            "answers": q_data["options"]
                        }) + "\n"

            return StreamingResponse(cached_stream_generator(), media_type="application/x-ndjson")

        data = await test_ort.get_test_data(test_type)
        time_limit = data["time_limit"]
        tasks = data["tasks"]
        total_questions = len(tasks)

        async def stream_generator():
            # Send metadata first
            yield json.dumps({"type": "meta", "time_limit": time_limit, "total_questions": total_questions}) + "\n"

            # Prepare array to save to Redis for submission
            cached_questions = [None] * total_questions

            # as_completed yields tasks immediately as they finish (out of order!)
            for coro in asyncio.as_completed(tasks):
                try:
                    res = await coro
                    idx = res["index"]
                    cached_questions[idx] = {"question": res["question"], "options": res["answers"]}

                    yield json.dumps({
                        "type": "question",
                        "index": idx,
                        "question": res["question"],
                        "answers": res["answers"]
                    }) + "\n"
                except Exception as e:
                    print(f"Error in question stream: {e}")

            # Calculate TTL based on test time limit (convert minutes to seconds) + 10 minute grace period
            expiration_seconds = (time_limit * 60) + 600

            # Cache the test
            redis_client.setex(cache_key, expiration_seconds, json.dumps(cached_questions))

        return StreamingResponse(stream_generator(), media_type="application/x-ndjson")

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/api/test/submit")
async def submit_test(submission: schemas.TestSubmission, current_user = Depends(get_current_user)):
    try:
        test_type = submission.test_type
        cache_key = f"ort_test:{current_user.id}:{test_type}"
        cached_data = redis_client.get(cache_key)

        if not cached_data:
            raise HTTPException(status_code=400, detail="Test session expired or not found.")

        questions = json.loads(cached_data)
        redis_client.delete(cache_key)

        base_score = 0
        weighted_score = 0.0
        details = []

        marked_questions = getattr(submission, 'marked_questions', [])
        has_marks = len(marked_questions) > 0

        for idx, q_data in enumerate(questions):
            if not q_data:
                continue

            question = q_data["question"]
            options = q_data["options"]

            # Safely unpack based on how utils.py orders the metadata
            if test_type == "math_1":
                correct_index = int(options[-3])
                points = float(options[-2])
            else:
                correct_index = int(options[-1])
                points = float(options[-3])

            answer_options = options[:-3]

            user_answer_idx = submission.answers.get(str(idx), submission.answers.get(idx))
            if isinstance(user_answer_idx, str):
                try:
                    user_answer_idx = int(user_answer_idx)
                except:
                    user_answer_idx = None

            is_correct = (user_answer_idx is not None and user_answer_idx == correct_index)

            if is_correct:
                base_score += 1
                weighted_score += points

            details.append({
                "question": question,
                "user_answer": user_answer_idx,
                "correct_answer": correct_index,
                "answers": answer_options,
                "is_correct": is_correct,
                "is_marked": idx in marked_questions
            })

        total = len(questions)
        passed = (base_score / total) >= 0.6 if total > 0 else False

        # Save to DB (sync_to_async wrapper unchanged)
        def db_save():
            return TestAttempt.objects.create(
                user=current_user,
                test_type=submission.test_type,
                score=base_score,
                weighted_score=round(weighted_score, 2),
                passed=passed,
                details=details,
                mark=has_marks
            )
        test_attempt = await sync_to_async(db_save)()

        return {
            "success": True,
            "score": base_score,
            "weighted_score": round(weighted_score, 2),
            "total": total,
            "percentage": (base_score / total * 100),
            "passed": passed,
            "attempt_id": test_attempt.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
