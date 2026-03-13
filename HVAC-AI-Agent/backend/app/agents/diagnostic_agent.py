"""
⚙ Diagnostic Agent
Evaluates HVAC system health, efficiency, and fault conditions.
"""

from app.config import IDEAL_IKW_TR, MAX_ACCEPTABLE_IKW_TR, COMFORT_TEMP_MIN, COMFORT_TEMP_MAX


async def evaluate_system(
    ikw_tr: float,
    indoor_temp: float,
    outdoor_temp: float,
    cooling_load_kw: float,
    energy_kwh: float,
    occupancy: int,
) -> dict:
    """
    Run a multi-factor diagnostic on the HVAC system.

    Checks
    ------
    1. IKW/TR efficiency rating
    2. Temperature set-point appropriateness
    3. Load-to-consumption ratio
    4. Over-cooling / under-cooling detection
    """

    # ── 1. Efficiency classification ──────────────────────────────
    if ikw_tr <= IDEAL_IKW_TR:
        efficiency_status = "Optimal"
        efficiency_score = 95
    elif ikw_tr <= MAX_ACCEPTABLE_IKW_TR:
        efficiency_status = "Acceptable"
        efficiency_score = 75
    elif ikw_tr <= 1.5:
        efficiency_status = "Efficiency Degradation"
        efficiency_score = 55
    else:
        efficiency_status = "Critical – Immediate Maintenance Required"
        efficiency_score = 30

    # ── 2. Comfort analysis ───────────────────────────────────────
    if indoor_temp < COMFORT_TEMP_MIN:
        comfort_status = "Over-cooling detected"
    elif indoor_temp > COMFORT_TEMP_MAX:
        comfort_status = "Under-cooling detected"
    else:
        comfort_status = "Within comfort range"

    # ── 3. Fault detection ────────────────────────────────────────
    faults: list[str] = []
    if ikw_tr > MAX_ACCEPTABLE_IKW_TR:
        faults.append("High IKW/TR – possible compressor degradation")
    if outdoor_temp - indoor_temp > 18:
        faults.append("Excessive ΔT – review insulation and load")
    if occupancy > 0 and cooling_load_kw / max(occupancy, 1) > 8:
        faults.append("Abnormally high per-capita cooling load")
    if energy_kwh > 0 and cooling_load_kw * 300 / energy_kwh > 1.5:
        faults.append("Energy consumption significantly exceeds predicted load")


    # ── 4. Recommendations & AI Intelligence ───────────────────────
    
    # Base recommendation starts with current indoor temp
    recommended_temp = indoor_temp

    # Logic: High occupancy -> reduce indoor temp slightly for comfort
    if occupancy > 50:
        recommended_temp -= 1.0
    # Logic: Low occupancy -> increase recommended temperature for energy savings
    elif occupancy < 10:
        recommended_temp += 2.0
    # Logic: High outdoor temp -> ensure we don't over-cool but maintain comfort
    elif outdoor_temp > 38:
        recommended_temp = max(recommended_temp, 24.0)
    
    # Clip to comfort range
    recommended_temp = max(COMFORT_TEMP_MIN, min(recommended_temp, COMFORT_TEMP_MAX))

    # Calculate potential savings based on efficiency and recommended temp change
    temp_diff_savings = max(0, (recommended_temp - indoor_temp) * 3.0) # 3% per degree roughly
    efficiency_savings = max(0, (ikw_tr - IDEAL_IKW_TR) / ikw_tr * 100 * 0.7)
    
    potential_saving_pct = round(temp_diff_savings + efficiency_savings, 1)

    return {
        "agent": "DiagnosticAgent",
        "status": "success",
        "efficiency_status": efficiency_status,
        "efficiency_score": efficiency_score,
        "comfort_status": comfort_status,
        "faults": faults,
        "recommended_temp": round(recommended_temp, 1),
        "potential_saving_pct": potential_saving_pct,
        "ikw_tr_actual": ikw_tr,
        "ikw_tr_ideal": IDEAL_IKW_TR,
    }
