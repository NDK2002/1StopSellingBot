"""Chat API route — connects to Google ADK agents."""

import uuid

from fastapi import APIRouter

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agents.orchestrator import root_agent
from app.config import get_settings, get_supabase_client
from app.models.schemas import ChatRequest, ChatResponse
import logging

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Session service for ADK
session_service = InMemorySessionService()

# Runner for the root agent
runner = Runner(
    agent=root_agent,
    app_name="1StopSellingBot",
    session_service=session_service,
)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)

@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Send a message to the chatbot and get a response."""
    session_id = req.session_id or str(uuid.uuid4())
    supabase = get_supabase_client()

    # Check if session is under staff takeover
    active_escalation = supabase.table("escalations").select("id, status").eq(
        "session_id", session_id
    ).eq("status", "in_progress").execute()
    if active_escalation.data:
        # Save user message for staff to see in DB
        supabase.table("conversations").insert(
            {"session_id": session_id, "role": "user", "content": req.message}
        ).execute()

        # Add to ADK session history so bot doesn't lose context
        try:
            from google.adk.events.event import Event
            session = await session_service.get_session(
                app_name="1StopSellingBot", 
                user_id="default_user", 
                session_id=session_id
            )
            if session:
                await session_service.append_event(
                    session,
                    Event(
                        author="user",
                        content=types.Content(role="user", parts=[types.Part(text=req.message)])
                    )
                )
        except Exception as e:
            print(f"Warning: Failed to inject user message into ADK session: {e}")

        return ChatResponse(
            reply="Nhân viên đang hỗ trợ bạn. Vui lòng chờ phản hồi.",
            session_id=session_id,
            escalated=True,
        )

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
            state={"session_id": session_id},
        )
    else:
        # Ensure session_id is always in state
        if "session_id" not in (session.state or {}):
            session.state["session_id"] = session_id

    # Create user message content
    user_content = types.Content(
        role="user",
        parts=[types.Part(text=req.message)],
    )

    # Run agent
    reply_parts = []
    escalated = False
    async for event in runner.run_async(
        user_id="default_user",
        session_id=session_id,
        new_message=user_content,
    ):
        if event.is_final_response():
            for part in event.content.parts:
                if part.text:
                    reply_parts.append(part.text)

    # Check database to see if an escalation was just created
    esc_check = supabase.table("escalations").select("id").eq(
        "session_id", session_id
    ).in_("status", ["pending", "assigned", "in_progress"]).execute()
    escalated = len(esc_check.data) > 0

    reply = "\n".join(reply_parts) if reply_parts else "Xin lỗi, tôi không thể xử lý yêu cầu này."

    # Save conversation to Supabase
    supabase.table("conversations").insert([
        {"session_id": session_id, "role": "user", "content": req.message},
        {"session_id": session_id, "role": "assistant", "content": reply},
    ]).execute()

    return ChatResponse(reply=reply, session_id=session_id, escalated=escalated)


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


@router.get("/sessions/{session_id}/debug")
async def debug_session(session_id: str):
    """Debug endpoint to view the internal memory of ADK."""
    session = await session_service.get_session(
        app_name="1StopSellingBot", 
        user_id="default_user", 
        session_id=session_id
    )
    if not session:
        return {"error": "Session is not loaded in memory (or missing)."}
    
    events = []
    for idx, e in enumerate(session.events):
        text = ""
        if e.content and e.content.parts:
            text = e.content.parts[-1].text or ""
        
        events.append({
            "index": idx,
            "author": e.author,
            "text": text,
        })
    
    return {
        "session_id": session_id,
        "event_count": len(events),
        "events": events
    }
