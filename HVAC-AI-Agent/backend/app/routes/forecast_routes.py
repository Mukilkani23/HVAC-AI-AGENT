"""
Forecast Routes – /forecast
"""

from fastapi import APIRouter, Query
from app.agents.forecast_agent import predict_cooling_load

router = APIRouter(prefix="/forecast", tags=["Forecast"])


@router.get("/predict")
async def predict(
    occupancy: int = Query(...),
    indoor_temp: float = Query(...),
    outdoor_temp: float = Query(...),
    humidity: float = Query(...),
    energy_kwh: float = Query(...),
):
    """Predict cooling load from building parameters."""
    return await predict_cooling_load(occupancy, indoor_temp, outdoor_temp, humidity, energy_kwh)
