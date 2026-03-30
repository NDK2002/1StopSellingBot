"""Escalation API routes — human handoff management."""

from datetime import datetime, timezone

import jwt
from fastapi import APIRouter, HTTPException, Query

from app.config import get_settings, get_supabase_client
from app.models.schemas import (
    EscalationCreate,
    EscalationResponse,
    EscalationUpdate,
    TakeoverMessage,
    EscalationAssign,
)
from app.services.escalation import create_escalation, resolve_escalation
from app.services.telegram import send_takeover_notification, send_escalation_notification

router = APIRouter(prefix="/api/escalations", tags=["escalations"])


@router.post("", response_model=EscalationResponse)
async def request_escalation(req: EscalationCreate):
    """Create a new escalation with skill-based routing."""
    result = await create_escalation(
        session_id=req.session_id,
        reason=req.reason,
        skill_required=req.skill_required,
        customer_summary=req.customer_summary,
    )
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Escalation failed"))

    # Fetch the created escalation
    supabase = get_supabase_client()
    esc = supabase.table("escalations").select("*").eq(
        "id", result["escalation_id"]
    ).execute()
    return esc.data[0]


@router.get("", response_model=list[EscalationResponse])
async def list_escalations(
    status: str | None = None,
    staff_id: str | None = None,
    limit: int = 50,
):
    """List escalations with optional filters."""
    supabase = get_supabase_client()
    query = supabase.table("escalations").select("*")
    if status:
        query = query.eq("status", status)
    if staff_id:
        query = query.eq("staff_id", staff_id)
    result = query.order("created_at", desc=True).limit(limit).execute()
    return result.data or []


@router.get("/{escalation_id}", response_model=EscalationResponse)
async def get_escalation(escalation_id: str):
    """Get escalation details."""
    supabase = get_supabase_client()
    result = supabase.table("escalations").select("*").eq("id", escalation_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Escalation not found")
    return result.data[0]


@router.post("/{escalation_id}/takeover")
async def takeover_conversation(escalation_id: str):
    """Staff takes over a conversation. Generates a JWT deep link token."""
    supabase = get_supabase_client()
    settings = get_settings()

    # Get escalation
    esc = supabase.table("escalations").select("*").eq("id", escalation_id).execute()
    if not esc.data:
        raise HTTPException(status_code=404, detail="Escalation not found")

    escalation = esc.data[0]
    if escalation["status"] != "assigned":
        raise HTTPException(status_code=400, detail="Cannot takeover — already in progress or resolved")

    # Update status to in_progress
    supabase.table("escalations").update({
        "status": "in_progress",
        "assigned_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", escalation_id).execute()

    # Generate JWT token for deep link
    token = jwt.encode(
        {
            "escalation_id": escalation_id,
            "session_id": escalation["session_id"],
            "staff_id": escalation.get("staff_id"),
            "type": "takeover",
        },
        settings.jwt_secret,
        algorithm="HS256",
    )

    # Notify via Telegram if staff has telegram_chat_id
    if escalation.get("staff_id"):
        staff = supabase.table("staff").select("name, telegram_chat_id").eq(
            "id", escalation["staff_id"]
        ).execute()
        if staff.data and staff.data[0].get("telegram_chat_id"):
            await send_takeover_notification(
                chat_id=staff.data[0]["telegram_chat_id"],
                session_id=escalation["session_id"],
                staff_name=staff.data[0]["name"],
            )

    return {
        "message": "Takeover successful",
        "escalation_id": escalation_id,
        "session_id": escalation["session_id"],
        "token": token,
        "chat_url": f"{settings.app_base_url}/api/chat/takeover?token={token}",
    }


@router.post("/{escalation_id}/reply")
async def staff_reply(escalation_id: str, msg: TakeoverMessage):
    """Staff sends a reply in a taken-over conversation."""
    supabase = get_supabase_client()

    # Verify escalation exists and is in_progress
    esc = supabase.table("escalations").select("*").eq("id", escalation_id).execute()
    if not esc.data:
        raise HTTPException(status_code=404, detail="Escalation not found")

    escalation = esc.data[0]
    if escalation["status"] == "assigned":
        # Auto-takeover when staff replies
        supabase.table("escalations").update({
            "status": "in_progress",
            "assigned_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", escalation_id).execute()
    elif escalation["status"] != "in_progress":
        raise HTTPException(status_code=400, detail="Escalation already resolved")

    # Save staff message to conversation history in DB
    supabase.table("conversations").insert({
        "session_id": msg.session_id,
        "role": "assistant",
        "content": msg.message,
        "metadata": {"source": "staff", "escalation_id": escalation_id},
    }).execute()

    # Add to ADK session history so bot knows what staff said
    try:
        from app.routers.chat import session_service
        from google.adk.events.event import Event
        from google.genai import types

        session = await session_service.get_session(
            app_name="1StopSellingBot", 
            user_id="default_user", 
            session_id=msg.session_id
        )
        if session:
            await session_service.append_event(
                session,
                Event(
                    author="user",
                    content=types.Content(
                        role="user", 
                        parts=[types.Part(text=f"[Hệ thống cập nhật: Nhân viên người thật đã vào hỗ trợ và chat nội dung sau]: {msg.message}")]
                    )
                )
            )
    except Exception as e:
        print(f"Warning: Failed to inject staff message into ADK session: {e}")

    return {"message": "Reply sent", "session_id": msg.session_id}


@router.post("/{escalation_id}/resolve")
async def resolve(escalation_id: str, update: EscalationUpdate | None = None):
    """Resolve an escalation."""
    notes = update.staff_notes if update else None
    result = await resolve_escalation(escalation_id, staff_notes=notes)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Resolve failed"))
    return result


@router.post("/{escalation_id}/assign")
async def reassign_escalation(escalation_id: str, assign_data: EscalationAssign):
    """Re-assign an escalation to a different staff member."""
    supabase = get_supabase_client()
    
    # 1. Get current escalation
    esc_result = supabase.table("escalations").select("*").eq("id", escalation_id).execute()
    if not esc_result.data:
        raise HTTPException(status_code=404, detail="Escalation not found")
    
    escalation = esc_result.data[0]
    old_staff_id = escalation.get("staff_id")
    new_staff_id = assign_data.new_staff_id
    
    if old_staff_id == new_staff_id:
        return {"success": True, "message": "Already assigned to this staff"}
        
    # 2. Get new staff details
    new_staff_result = supabase.table("staff").select("*").eq("id", new_staff_id).execute()
    if not new_staff_result.data:
        raise HTTPException(status_code=404, detail="New staff not found")
        
    new_staff = new_staff_result.data[0]
    
    # 3. Update Escalation
    supabase.table("escalations").update({
        "staff_id": new_staff_id,
        "status": "assigned",
        "assigned_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", escalation_id).execute()
    
    # 4. Decrease old staff load
    if old_staff_id:
        old_staff_res = supabase.table("staff").select("current_load").eq("id", old_staff_id).execute()
        if old_staff_res.data:
            old_load = max(0, old_staff_res.data[0]["current_load"] - 1)
            supabase.table("staff").update({"current_load": old_load}).eq("id", old_staff_id).execute()
            
    # 5. Increase new staff load
    new_load = new_staff["current_load"] + 1
    supabase.table("staff").update({"current_load": new_load}).eq("id", new_staff_id).execute()
    
    # 6. Send Telegram Notification to new staff
    if new_staff.get("telegram_chat_id"):
        deep_link = f"http://127.0.0.1:8501/?session_id={escalation['session_id']}"
        await send_escalation_notification(
            chat_id=new_staff["telegram_chat_id"],
            session_id=escalation["session_id"],
            reason=escalation["reason"],
            customer_summary=escalation["customer_summary"],
            deep_link=deep_link,
        )
        
    return {"success": True, "message": f"Escalation reassigned to {new_staff['name']}"}


@router.get("/session/{session_id}/history")
async def get_session_history(session_id: str, limit: int = 100):
    """Get conversation history for a session (used by staff during takeover)."""
    supabase = get_supabase_client()
    result = (
        supabase.table("conversations")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at")
        .limit(limit)
        .execute()
    )
    return result.data or []


@router.get("/{session_id}/messages")
async def get_escalation_messages(session_id: str):
    from app.config import get_supabase_client
    supabase = get_supabase_client()
    return supabase.table("conversations").select("*").eq("session_id", session_id).order("created_at").execute().data


from pydantic import BaseModel
class TakeoverText(BaseModel):
    message: str

@router.post("/{session_id}/takeover_message")
async def takeover_message_by_session(session_id: str, msg: TakeoverText):
    from app.config import get_supabase_client
    supabase = get_supabase_client()
    
    # Get latest active escalation for this session limit 1
    esc = supabase.table("escalations").select("*").eq("session_id", session_id).order("created_at", desc=True).limit(1).execute()
    if not esc.data:
        raise HTTPException(status_code=404, detail="No escalation found for this session")
        
    escalation_id = esc.data[0]["id"]
    
    if esc.data[0]["status"] == "assigned":
        supabase.table("escalations").update({
            "status": "in_progress",
        }).eq("id", escalation_id).execute()
        
    content_to_save = f"[Hệ thống cập nhật thông tin nội bộ]: {msg.message}"
    
    saved = supabase.table("conversations").insert({
        "session_id": session_id,
        "role": "assistant",
        "content": content_to_save,
        "metadata": {"source": "staff", "escalation_id": escalation_id},
    }).execute()
    
    from app.services.websocket import manager
    import asyncio
    if saved.data:
        asyncio.create_task(manager.broadcast_to_session(session_id, {"type": "new_message", "message": saved.data[0]}))

    return {"status": "success", "message": saved.data[0]}
