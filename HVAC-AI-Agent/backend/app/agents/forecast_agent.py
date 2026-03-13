"""
📊 Forecast Agent
Predicts cooling load and energy demand based on building parameters and weather.
"""

import math


async def predict_cooling_load(
    occupancy: int,
    indoor_temp: float,
    outdoor_temp: float,
    humidity: float,
    energy_kwh: float,
    area_sqft: float = 5000.0,
) -> dict:
    """
    Estimate the cooling load (kW) using a simplified CLTD-based model.

    Parameters
    ----------
    occupancy : int       – Number of occupants
    indoor_temp : float   – Desired indoor temperature (°C)
    outdoor_temp : float  – Current outdoor temperature (°C)
    humidity : float      – Outdoor relative humidity (%)
    energy_kwh : float    – Current monthly energy consumption (kWh)
    area_sqft : float     – Approximate conditioned floor area (sq ft)
    """

    delta_t = max(outdoor_temp - indoor_temp, 0)

    envelope_load = area_sqft * 0.035 * delta_t
    occupant_load = occupancy * 250
    equipment_load = area_sqft * 1.5
    ventilation_load = occupancy * 20 * delta_t * (humidity / 50)

    total_btu = envelope_load + occupant_load + equipment_load + ventilation_load
    cooling_load_kw = round(total_btu / 3412.14, 1)
    cooling_load_tr = round(cooling_load_kw / 3.517, 2)

    predicted_daily_kwh = round(cooling_load_kw * 10, 1)
    monthly_predicted = round(predicted_daily_kwh * 30, 0)
    deviation_pct = round(((monthly_predicted - energy_kwh) / max(energy_kwh, 1)) * 100, 1)

    peak_load_kw = round(cooling_load_kw * 1.15, 1)

    # Monthly Electricity Bill Calculation (Assume 10 hours/day, 30 days/month, ₹8 per kWh)
    tariff = 8
    monthly_energy_consumption = cooling_load_kw * 10 * 30
    monthly_bill_non_optimized = round(monthly_energy_consumption * tariff, 2)

    return {
        "agent": "ForecastAgent",
        "status": "success",
        "cooling_load_kw": cooling_load_kw,
        "cooling_load_tr": cooling_load_tr,
        "peak_load_kw": peak_load_kw,
        "predicted_monthly_kwh": monthly_predicted,
        "current_monthly_kwh": energy_kwh,
        "deviation_pct": deviation_pct,
        "delta_t": round(delta_t, 1),
        "monthly_bill_non_optimized": monthly_bill_non_optimized,
        # We start with the same bill, to be adjusted later by the AI Decision Engine
        "monthly_bill_optimized": monthly_bill_non_optimized,
        "estimated_monthly_savings_currency": 0.0
    }
