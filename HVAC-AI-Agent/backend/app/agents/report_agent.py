"""
📄 Report Agent
Compiles all agent outputs into a unified HVAC optimization report.
"""

from datetime import datetime


async def compile_report(
    building: str,
    address: str,
    location_data: dict,
    weather_data: dict,
    forecast_data: dict,
    diagnostic_data: dict,
) -> dict:
    """
    Merge outputs from all upstream agents into a single structured report.
    """

    # ── AI Decision Engine summary ────────────────────────────────
    energy_saving = f"{diagnostic_data.get('potential_saving_pct', 0)}%"
    recommended_temp = diagnostic_data.get("recommended_temp", 24)

    # Priority level
    score = diagnostic_data.get("efficiency_score", 50)
    if score >= 80:
        priority = "Low – System performing well"
    elif score >= 55:
        priority = "Medium – Optimizations recommended"
    else:
        priority = "High – Immediate action required"

    # Action items
    actions: list[str] = []
    if diagnostic_data.get("potential_saving_pct", 0) > 5:
        actions.append(f"Adjust set-point to {recommended_temp}°C to save ~{energy_saving}")
    if "Efficiency Degradation" in diagnostic_data.get("efficiency_status", ""):
        actions.append("Schedule preventive maintenance for compressor / chiller")
    if "Over-cooling" in diagnostic_data.get("comfort_status", ""):
        actions.append("Raise set-point temperature to avoid over-cooling")
    if "Under-cooling" in diagnostic_data.get("comfort_status", ""):
        actions.append("Lower set-point or check refrigerant levels")
    if not actions:
        actions.append("Continue current operating parameters")

    return {
        "report_id": f"RPT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "generated_at": datetime.utcnow().isoformat(),
        "building": building,
        "address": address,
        "input_occupancy": location_data.get("input_occupancy"),
        "input_indoor_temp": location_data.get("input_indoor_temp"),

        # Location
        "formatted_address": location_data.get("formatted_address", address),
        "city": location_data.get("city", address),
        "climate_zone": location_data.get("climate_zone", "Unknown"),
        "lat": location_data.get("lat"),
        "lon": location_data.get("lon"),

        # Weather
        "outdoor_temp": weather_data.get("outdoor_temp_c"),
        "humidity": weather_data.get("humidity_pct"),
        "wind_speed": weather_data.get("wind_speed_kmh"),
        "weather_condition": weather_data.get("condition"),

        # Forecast
        "cooling_load": forecast_data.get("cooling_load_kw"),
        "cooling_load_tr": forecast_data.get("cooling_load_tr"),
        "peak_load": forecast_data.get("peak_load_kw"),
        "predicted_monthly_kwh": forecast_data.get("predicted_monthly_kwh"),

        # Diagnostics
        "efficiency_status": diagnostic_data.get("efficiency_status"),
        "efficiency_score": diagnostic_data.get("efficiency_score"),
        "comfort_status": diagnostic_data.get("comfort_status"),
        "faults": diagnostic_data.get("faults", []),
        "recommended_temp": recommended_temp,
        "energy_saving": energy_saving,

        # AI Decision
        "priority": priority,
        "actions": actions,
        
        # Monthly Bill Cost Comparison
        "monthly_bill_non_optimized": forecast_data.get("monthly_bill_non_optimized"),
        "monthly_bill_optimized": forecast_data.get("monthly_bill_optimized"),
        "estimated_monthly_savings_currency": forecast_data.get("estimated_monthly_savings_currency"),
    }
