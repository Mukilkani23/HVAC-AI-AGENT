"""
Location Routes – /location
"""

from fastapi import APIRouter, Query
from app.agents.location_agent import resolve_location

router = APIRouter(prefix="/location", tags=["Location"])


@router.get("/resolve")
async def resolve(building: str = Query(...), address: str = Query(...)):
    """Resolve building address to geographic coordinates."""
    return await resolve_location(building, address)
