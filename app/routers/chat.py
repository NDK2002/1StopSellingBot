"""Chat API route — connects to Google ADK agents."""

import uuid

from fastapi import APIRouter

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agents.orchestrator import root_agent
from app.config import get_settings, get_supabase_client
from app.models.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Session service for ADK
session_service = InMemorySessionService()

# Runner for the root agent
runner = Runner(
    agent=root_agent,
    app_name="1StopSellingBot",
    session_service=session_service,
)

@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Send a message to the chatbot and get a response."""
    session_id = req.session_id or str(uuid.uuid4())

    # Get or create session
    session = await session_service.get_session(
        app_name="1StopSellingBot",
        user_id="default_user",
        session_id=session_id,
    )
    if session is None:
        session = await session_service.create_session(
            app_name="1StopSellingBot",
            user_id="default_user",
            session_id=session_id,
        )

    # Create user message content
    user_content = types.Content(
        role="user",
        parts=[types.Part(text=req.message)],
    )

    # Run agent
    reply_parts = []
    async for event in runner.run_async(
        user_id="default_user",
        session_id=session_id,
        new_message=user_content,
    ):
        if event.is_final_response():
            for part in event.content.parts:
                if part.text:
                    reply_parts.append(part.text)

    reply = "\n".join(reply_parts) if reply_parts else "Xin lỗi, tôi không thể xử lý yêu cầu này."

    # Save conversation to Supabase
    supabase = get_supabase_client()
    supabase.table("conversations").insert([
        {"session_id": session_id, "role": "user", "content": req.message},
        {"session_id": session_id, "role": "assistant", "content": reply},
    ]).execute()

    return ChatResponse(reply=reply, session_id=session_id)


@router.delete("/sessions/{session_id}")
async def reset_session(session_id: str):
    """Reset a chat session."""
    try:
        await session_service.delete_session(
            app_name="1StopSellingBot",
            user_id="default_user",
            session_id=session_id,
        )
    except Exception:
        pass

    # Also clean up conversation history
    supabase = get_supabase_client()
    supabase.table("conversations").delete().eq("session_id", session_id).execute()

    return {"message": "Session reset", "session_id": session_id}
