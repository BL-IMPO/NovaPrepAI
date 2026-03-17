from pathlib import Path

from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from asgiref.sync import sync_to_async

from src.tasks_generation import  ai_chat_response
from ..schemas.schemas import ChatRequest, ChatResponse

# Now import Django models
try:
    from django.contrib.auth import get_user_model
    from main.models import TestAttempt, ChatThread, ChatMessage
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

@router.get("/api/chat/history")
async def get_chat_history(attempt_id: int, task_id: str):
    """
    Called when the user opens the sidebar for a specific question.
    Returns previous messages so the chat UI isn't empty on reopen.
    """
    try:
        def db_get_chat_history():
            thread = ChatThread.objects.get(attempt_id=attempt_id, task_id=task_id)

            messages = thread.messages.all().order_by('created_at')

            return [{"role": msg.role, "content": msg.content} for msg in messages]

        formated_messages = await sync_to_async(db_get_chat_history)()

    except ChatThread.DoesNotExist:
        formated_messages = []

    return {
        "messages": formated_messages
    }

@router.post("/api/chat/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Called every time the user clicks "Send" in the sidebar.
    Handles the 10-message limit and AI generation.
    """

    def db_prepare_chat():
        thread_db, created = ChatThread.objects.get_or_create(
            attempt_id=request.attempt_id,
            task_id=request.task_id
        )

        messages = thread_db.messages.all().order_by('created_at')

        formatted_msgs = [{"role": msg.role, "content": msg.content} for msg in messages]

        return thread_db, formatted_msgs

    thread, old_messages = await sync_to_async(db_prepare_chat)()

    msg_count = len(old_messages)

    if msg_count >= 10:
        # Stop processing and tell the frontend to trigger the popup
        return ChatResponse(
            status="limit_reached",
            reply=None,
            thread_id=thread.id,
            message_count=msg_count
        )

    def db_save_user_message():
        thread.messages.create(
            role='user',
            content=request.user_message
        )

    await sync_to_async(db_save_user_message)()

    old_messages.append({"role": "user", "content": request.user_message})

    ai_response = await ai_chat_response(request.task_context, old_messages)

    def db_save_ai_response():
        thread.messages.create(
            role='assistant',
            content=ai_response
        )

    await sync_to_async(db_save_ai_response)()

    return ChatResponse(
        status="success",
        reply=ai_response,
        thread_id=thread.id,
        message_count=msg_count+2
    )


@router.get("/api/chat/{thread_id}/export")
async def export_chat(thread_id: int):
    """
    Returns clean text block for the user to copy.
    """

    def db_get_chat_history():
        messages = ChatMessage.objects.filter(thread_id=thread_id).order_by('created_at')
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    formatted_messages = await sync_to_async(db_get_chat_history)()

    clean_transcript = ""
    for message in formatted_messages:
        # Improved formatting for readability (e.g., "User: Hello" instead of "user\nHello")
        speaker = message["role"].capitalize()
        clean_transcript += f"{speaker}: {message['content']}\n\n"

    return {
        "clipboard_text": clean_transcript.strip()
    }


