"""
Diagnostic Routes – /diagnostic
"""

from fastapi import APIRouter, Query
from app.agents.diagnostic_agent import evaluate_system

router = APIRouter(prefix="/diagnostic", tags=["Diagnostic"])


@router.get("/evaluate")
async def evaluate(
    ikw_tr: float = Query(...),
    indoor_temp: float = Query(...),
    outdoor_temp: float = Query(...),
    cooling_load_kw: float = Query(...),
    energy_kwh: float = Query(...),
    occupancy: int = Query(...),
):
    """Evaluate HVAC system health and efficiency."""
    return await evaluate_system(ikw_tr, indoor_temp, outdoor_temp, cooling_load_kw, energy_kwh, occupancy)
