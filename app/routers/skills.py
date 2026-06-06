"""Skills metadata API."""

from fastapi import APIRouter

from app.constants import SKILLS

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get("")
async def list_skills() -> list[dict]:
    """Return the predefined list of staff skills."""
    return SKILLS
