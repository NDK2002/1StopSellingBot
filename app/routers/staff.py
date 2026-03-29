"""Staff management API routes."""

from fastapi import APIRouter, HTTPException

from app.config import get_supabase_client
from app.models.schemas import StaffCreate, StaffResponse, StaffUpdate

router = APIRouter(prefix="/api/staff", tags=["staff"])


@router.post("", response_model=StaffResponse)
async def create_staff(staff: StaffCreate):
    """Create a new staff member."""
    supabase = get_supabase_client()
    result = supabase.table("staff").insert(staff.model_dump()).execute()
    if not result.data:
        raise HTTPException(status_code=400, detail="Failed to create staff")
    return result.data[0]


@router.get("", response_model=list[StaffResponse])
async def list_staff(available_only: bool = False):
    """List all staff members."""
    supabase = get_supabase_client()
    query = supabase.table("staff").select("*")
    if available_only:
        query = query.eq("is_available", True)
    result = query.order("name").execute()
    return result.data or []


@router.get("/{staff_id}", response_model=StaffResponse)
async def get_staff(staff_id: str):
    """Get a single staff member."""
    supabase = get_supabase_client()
    result = supabase.table("staff").select("*").eq("id", staff_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Staff not found")
    return result.data[0]


@router.put("/{staff_id}", response_model=StaffResponse)
async def update_staff(staff_id: str, staff: StaffUpdate):
    """Update a staff member."""
    supabase = get_supabase_client()
    data = staff.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = supabase.table("staff").update(data).eq("id", staff_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Staff not found")
    return result.data[0]


@router.delete("/{staff_id}")
async def delete_staff(staff_id: str):
    """Delete a staff member."""
    supabase = get_supabase_client()
    result = supabase.table("staff").delete().eq("id", staff_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Staff not found")
    return {"message": "Staff deleted", "id": staff_id}
