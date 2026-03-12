from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Optional, Any


class TestDataResponse(BaseModel):
    time_limit: int
    questions: Dict[str, List[str]]


class TestSubmission(BaseModel):
    answers: Dict[str, int] # question_index -> answer_index
    test_type: str
    marked_questions: list[int] = []
    user_id: Optional[int] = None # Optional, will be set from auth in production


class TestAttemptResponse(BaseModel):
    id: int
    user_id: int
    user_username: str
    test_type: str

    score: int
    weighted_score: float

    passed: bool
    created_at: str
    details_count: int


class ChatRequest(BaseModel):
    attempt_id: int
    task_id: str
    user_message: str
    task_context: str

class ChatResponse(BaseModel):
    status: str
    reply: Optional[str] = None
    thread_id: int
    message_count: int


class HealthResponse(BaseModel):
    status: str
    database: str
    django: str

