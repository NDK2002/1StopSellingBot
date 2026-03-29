"""Escalation Engine — skill-based routing and human handoff."""

import logging
from datetime import datetime, timezone

from app.config import get_settings, get_supabase_client
from app.services.telegram import send_escalation_notification

logger = logging.getLogger(__name__)


async def create_escalation(
    session_id: str,
    reason: str = "low_confidence",
    skill_required: str | None = None,
    customer_summary: str | None = None,
) -> dict:
    """Create an escalation and route to the best available staff.

    Routing logic:
    1. Find staff with matching skill who is available.
    2. Among matches, pick the one with lowest current_load.
    3. If no skill match, pick any available staff with lowest load.
    4. Send Telegram notification.

    Returns:
        dict with escalation details.
    """
    supabase = get_supabase_client()
    settings = get_settings()

    # Step 1: Find best staff
    staff = await _find_best_staff(skill_required)

    # Step 2: Create escalation record
    escalation_data = {
        "session_id": session_id,
        "reason": reason,
        "skill_required": skill_required,
        "customer_summary": customer_summary,
        "status": "assigned" if staff else "pending",
        "staff_id": staff["id"] if staff else None,
        "assigned_at": datetime.now(timezone.utc).isoformat() if staff else None,
        "priority": _calculate_priority(reason),
    }

    result = supabase.table("escalations").insert(escalation_data).execute()
    if not result.data:
        logger.error("Failed to create escalation")
        return {"success": False, "error": "Failed to create escalation"}

    escalation = result.data[0]

    # Step 3: Update staff load
    if staff:
        supabase.table("staff").update({
            "current_load": staff["current_load"] + 1,
        }).eq("id", staff["id"]).execute()

    # Step 4: Send Telegram notification
    if staff and staff.get("telegram_chat_id"):
        # Telegram mobile blocks "localhost" URLs. Use 127.0.0.1 or a real domain (ngrok)
        deep_link = f"http://127.0.0.1:8501/?session_id={session_id}"
        await send_escalation_notification(
            chat_id=staff["telegram_chat_id"],
            session_id=session_id,
            reason=reason,
            customer_summary=customer_summary,
            deep_link=deep_link,
        )
        logger.info(f"Escalation {escalation['id']} assigned to {staff['name']}")
    else:
        logger.warning(f"Escalation {escalation['id']} pending — no staff available")

    return {
        "success": True,
        "escalation_id": escalation["id"],
        "status": escalation["status"],
        "assigned_to": staff["name"] if staff else None,
    }


async def resolve_escalation(escalation_id: str, staff_notes: str | None = None) -> dict:
    """Mark an escalation as resolved and free up staff load."""
    supabase = get_supabase_client()

    # Get escalation
    result = supabase.table("escalations").select("*").eq("id", escalation_id).execute()
    if not result.data:
        return {"success": False, "error": "Escalation not found"}

    escalation = result.data[0]
    if escalation["status"] == "resolved":
        return {"success": False, "error": "Already resolved"}

    # Update escalation
    supabase.table("escalations").update({
        "status": "resolved",
        "staff_notes": staff_notes,
        "resolved_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", escalation_id).execute()

    # Decrease staff load
    if escalation.get("staff_id"):
        staff = supabase.table("staff").select("current_load").eq(
            "id", escalation["staff_id"]
        ).execute()
        if staff.data:
            new_load = max(0, staff.data[0]["current_load"] - 1)
            supabase.table("staff").update({"current_load": new_load}).eq(
                "id", escalation["staff_id"]
            ).execute()

    return {"success": True, "escalation_id": escalation_id, "status": "resolved"}


async def _find_best_staff(skill_required: str | None = None) -> dict | None:
    """Find the best available staff member using skill-based routing.

    Priority:
    1. Staff with matching skill + lowest load + under max_concurrent
    2. Any available staff with lowest load
    """
    supabase = get_supabase_client()

    # Get all available staff
    result = supabase.table("staff").select("*").eq("is_available", True).execute()
    if not result.data:
        return None

    available = [s for s in result.data if s["current_load"] < s["max_concurrent"]]
    if not available:
        return None

    # Try skill match first
    if skill_required:
        skill_matches = [s for s in available if skill_required in (s.get("skills") or [])]
        if skill_matches:
            return min(skill_matches, key=lambda s: s["current_load"])

    # Fallback: any available staff with lowest load
    return min(available, key=lambda s: s["current_load"])


def _calculate_priority(reason: str) -> int:
    """Calculate escalation priority (higher = more urgent)."""
    priorities = {
        "complaint": 3,
        "order_issue": 2,
        "user_request": 1,
        "complex_issue": 1,
        "low_confidence": 0,
    }
    return priorities.get(reason, 0)
