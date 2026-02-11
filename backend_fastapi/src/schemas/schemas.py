from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Optional, Any


class TestDataResponse(BaseModel):
    time_limit: int
    questions: Dict[str, List[str]]


class TestSubmission(BaseModel):
    answers: Dict[str, int] # question_index -> answer_index
    test_type: str
    user_id: Optional[int] = None # Optional, will be set from auth in production


class TestAttemptResponse(BaseModel):
    id: int
    user_id: int
    user_username: str
    test_type: str
    score: int
    passed: bool
    created_at: str
    details_count: int


class HealthResponse(BaseModel):
    status: str
    database: str
    django: str