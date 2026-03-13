"""
AI Routes – /ai
Main orchestration endpoint that chains all agents together.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.location_agent import resolve_location
from app.agents.weather_agent import fetch_weather
from app.agents.forecast_agent import predict_cooling_load
from app.agents.diagnostic_agent import evaluate_system
from app.agents.report_agent import compile_report
from app.database import save_analysis


router = APIRouter(prefix="/ai", tags=["AI"])


class AnalyzeRequest(BaseModel):
    building: str
    address: str
    occupancy: int
    indoor_temp: float
    energy_kwh: float
    ikw_tr: float


@router.post("/analyze")
async def analyze(req: AnalyzeRequest):
    """
    🧠 AI Decision Engine
    Orchestrates the full multi-agent pipeline:
      Location → Weather → Forecast → Diagnostic → Report
    """

    # Step 1 – Location Agent
    location = await resolve_location(req.building, req.address)
    location["input_occupancy"] = req.occupancy
    location["input_indoor_temp"] = req.indoor_temp

    # Step 2 – Weather Agent
    weather = await fetch_weather(
        lat=location["lat"],
        lon=location["lon"],
        climate_zone=location.get("climate_zone", "Warm Humid"),
    )

    # Step 3 – Forecast Agent
    forecast = await predict_cooling_load(
        occupancy=req.occupancy,
        indoor_temp=req.indoor_temp,
        outdoor_temp=weather["outdoor_temp_c"],
        humidity=weather["humidity_pct"],
        energy_kwh=req.energy_kwh,
    )

    # Step 4 – Diagnostic Agent
    diagnostic = await evaluate_system(
        ikw_tr=req.ikw_tr,
        indoor_temp=req.indoor_temp,
        outdoor_temp=weather["outdoor_temp_c"],
        cooling_load_kw=forecast["cooling_load_kw"],
        energy_kwh=req.energy_kwh,
        occupancy=req.occupancy,
    )

    # Step 4.5 – Adjust Forecast bills based on AI Diagnostic Savings
    savings_pct = diagnostic.get("potential_saving_pct", 0) / 100.0
    optimized_bill = forecast["monthly_bill_non_optimized"] * (1 - savings_pct)
    forecast["monthly_bill_optimized"] = round(optimized_bill, 2)
    forecast["estimated_monthly_savings_currency"] = round(forecast["monthly_bill_non_optimized"] - forecast["monthly_bill_optimized"], 2)


    # Step 5 – Report Agent (AI Decision Engine)
    report = await compile_report(
        building=req.building,
        address=req.address,
        location_data=location,
        weather_data=weather,
        forecast_data=forecast,
        diagnostic_data=diagnostic,
    )

    # Persist to in-memory store
    report_id = save_analysis(report)
    report["report_id"] = report_id

    return report
