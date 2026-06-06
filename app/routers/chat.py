"""Chat API route — connects to Google ADK agents."""

import uuid

from fastapi import APIRouter

from google.adk.events.event import Event
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


APP_NAME = "1StopSellingBot"
USER_ID = "default_user"
STAFF_CONTEXT_PREFIX = "[Hệ thống cập nhật: Nhân viên người thật đã vào hỗ trợ và chat nội dung sau]: "


async def get_or_create_session(session_id: str):
    """Load an ADK session, replaying persisted conversation history when needed."""
    session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
    )
    if session is None:
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id,
            state={"session_id": session_id},
        )
        await hydrate_session_from_conversations(session, session_id)
    elif "session_id" not in (session.state or {}):
        session.state["session_id"] = session_id
    return session


async def hydrate_session_from_conversations(session, session_id: str, limit: int = 40) -> None:
    """Replay saved messages so InMemorySessionService survives page refresh/server reloads."""
    supabase = get_supabase_client()
    result = (
        supabase.table("conversations")
        .select("role, content, metadata, created_at")
        .eq("session_id", session_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    rows = list(reversed(result.data or []))
    for row in rows:
        content = row.get("content") or ""
        if not content:
            continue

        role = row.get("role", "user")
        metadata = row.get("metadata") or {}
        if role == "user":
            author = "user"
            content_role = "user"
            text = content
        elif metadata.get("source") == "staff":
            author = "user"
            content_role = "user"
            text = f"{STAFF_CONTEXT_PREFIX}{content}"
        else:
            author = root_agent.name
            content_role = "model"
            text = content

        await session_service.append_event(
            session,
            Event(
                author=author,
                content=types.Content(role=content_role, parts=[types.Part(text=text)]),
            ),
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
        new_msg = supabase.table("conversations").insert(
            {"session_id": session_id, "role": "user", "content": req.message}
        ).execute()

        from app.services.websocket import manager
        import asyncio
        if new_msg.data:
            asyncio.create_task(manager.broadcast_to_session(session_id, {"type": "new_message", "message": new_msg.data[0]}))
        # Add to ADK session history so bot doesn't lose context
        try:
            session = await get_or_create_session(session_id)
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
    await get_or_create_session(session_id)

    # Create user message content
    user_content = types.Content(
        role="user",
        parts=[types.Part(text=req.message)],
    )

    # Run agent
    reply_parts = []
    escalated = False
    async for event in runner.run_async(
        user_id=USER_ID,
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
            app_name=APP_NAME,
            user_id=USER_ID,
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
        app_name=APP_NAME,
        user_id=USER_ID,
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
