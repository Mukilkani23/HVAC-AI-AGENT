"""
📦 Report Storage – Single JSON File Database
All reports stored in backend/data/reports.json.
Supports: save, retrieve, soft-delete, analytics, comparison.
"""

import json
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
REPORTS_FILE = DATA_DIR / "reports.json"

_lock = Lock()


def _ensure_file():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not REPORTS_FILE.exists():
        with open(REPORTS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


def _read_all() -> list:
    _ensure_file()
    try:
        with open(REPORTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _write_all(reports: list):
    _ensure_file()
    with open(REPORTS_FILE, "w", encoding="utf-8") as f:
        json.dump(reports, f, indent=2, default=str)


def _next_id(reports: list) -> int:
    if not reports:
        return 1
    return max(r.get("report_id", 0) for r in reports) + 1


def _visible(reports: list) -> list:
    """Return only reports where is_visible is True."""
    return [r for r in reports if r.get("is_visible", True)]


# ── Building type occupancy multipliers ─────────────────────
BUILDING_MULTIPLIERS = {
    "mall": 1.3,
    "hotel": 1.1,
    "theatre": 1.2,
    "office": 1.0,
    "hospital": 1.4,
}


def _compute_efficiency_score(ikw_tr: float) -> dict:
    """Compute HVAC efficiency score from IKW/TR value."""
    if ikw_tr is None:
        return {"score": 50, "status": "Unknown", "grade": "N/A"}
    ikw = float(ikw_tr)
    if ikw < 1.1:
        score = min(100, int(95 - (ikw - 0.6) * 10))
        return {"score": max(85, score), "status": "Excellent", "grade": "A+"}
    elif ikw <= 1.3:
        score = int(82 - (ikw - 1.1) * 30)
        return {"score": max(70, score), "status": "Good", "grade": "A"}
    elif ikw <= 1.5:
        score = int(68 - (ikw - 1.3) * 40)
        return {"score": max(55, score), "status": "Moderate", "grade": "B"}
    else:
        score = int(50 - (ikw - 1.5) * 30)
        return {"score": max(20, score), "status": "Poor", "grade": "C"}


def _compute_weather_impact(outdoor_temp, humidity) -> dict:
    """Compute weather impact on cooling demand."""
    temp = float(outdoor_temp) if outdoor_temp else 25
    hum = float(humidity) if humidity else 50
    if temp > 34 or (temp > 32 and hum > 70):
        level = "HIGH"
        color = "red"
        desc = "Extreme outdoor conditions significantly increase cooling demand"
    elif temp >= 30:
        level = "MODERATE"
        color = "amber"
        desc = "Warm conditions moderately elevate cooling requirements"
    else:
        level = "LOW"
        color = "green"
        desc = "Mild conditions allow efficient cooling operation"
    return {"level": level, "color": color, "description": desc}


def _compute_system_health(efficiency_score, faults, ikw_tr) -> dict:
    """Compute HVAC system health status."""
    score = efficiency_score if efficiency_score else 50
    fault_count = len(faults) if faults else 0
    ikw = float(ikw_tr) if ikw_tr else 1.0

    if score >= 75 and fault_count == 0 and ikw <= 1.3:
        return {
            "status": "Healthy",
            "maintenance_required": False,
            "energy_efficiency": "Good",
            "color": "green",
            "icon": "✅",
        }
    elif score >= 55 or fault_count <= 1:
        return {
            "status": "Warning",
            "maintenance_required": fault_count > 0,
            "energy_efficiency": "Moderate",
            "color": "amber",
            "icon": "⚠️",
        }
    else:
        return {
            "status": "Critical",
            "maintenance_required": True,
            "energy_efficiency": "Poor – Energy Loss Detected",
            "color": "red",
            "icon": "🔴",
        }


def _generate_ai_explanation(report_data: dict) -> list:
    """Generate AI decision explanation steps."""
    explanations = []
    outdoor = report_data.get("outdoor_temp")
    humidity = report_data.get("humidity")
    occupancy = report_data.get("input_occupancy")
    indoor = report_data.get("input_indoor_temp")
    recommended = report_data.get("recommended_temp")
    cooling = report_data.get("cooling_load")

    if outdoor and float(outdoor) > 32:
        explanations.append(f"High outdoor temperature detected ({outdoor}°C)")
    elif outdoor:
        explanations.append(f"Outdoor temperature analyzed ({outdoor}°C)")

    if humidity and float(humidity) > 60:
        explanations.append(f"High humidity level detected ({humidity}%)")

    if occupancy and int(occupancy) > 80:
        explanations.append(f"High occupancy detected ({occupancy} people)")
    elif occupancy:
        explanations.append(f"Occupancy factor calculated ({occupancy} people)")

    if cooling:
        explanations.append(f"Predicted cooling load: {cooling} kW")

    if indoor and recommended:
        if float(indoor) != float(recommended):
            explanations.append(
                f"Recommended indoor temperature adjusted from {indoor}°C to {recommended}°C"
            )
        else:
            explanations.append(f"Current temperature {indoor}°C is optimal")

    if not explanations:
        explanations.append("System analysis completed with standard parameters")

    return explanations



def _generate_smart_alerts(report_data: dict) -> list:
    """Generate smart alert messages."""
    alerts = []
    eff_score = report_data.get("efficiency_score")
    ikw = report_data.get("ikw_tr") or report_data.get("ikw_tr_value")
    faults = report_data.get("faults", [])

    if eff_score and float(eff_score) < 60:
        alerts.append({
            "type": "warning",
            "message": "HVAC efficiency below optimal level",
            "action": "Schedule maintenance or adjust cooling settings",
        })

    if ikw and float(ikw) > 1.4:
        alerts.append({
            "type": "warning",
            "message": "High energy consumption per ton of refrigeration detected",
            "action": "Inspect compressor and refrigerant levels",
        })

    if faults:
        for fault in faults:
            alerts.append({
                "type": "alert",
                "message": fault,
                "action": "Address this issue to improve system performance",
            })

    if not alerts:
        alerts.append({
            "type": "success",
            "message": "All systems operating within normal parameters",
            "action": "Continue current operating parameters",
        })

    return alerts


# ═══════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════

def save_report(report_data: dict) -> dict:
    """Append a new report to reports.json."""
    with _lock:
        reports = _read_all()
        new_id = _next_id(reports)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        timestamp_short = datetime.now().strftime("%I:%M %p")

        # Extract IKW/TR for efficiency calculation
        ikw_tr = report_data.get("ikw_tr") or report_data.get("ikw_tr_value")
        eff = _compute_efficiency_score(ikw_tr)
        weather_impact = _compute_weather_impact(
            report_data.get("outdoor_temp"),
            report_data.get("humidity"),
        )
        health = _compute_system_health(
            report_data.get("efficiency_score"),
            report_data.get("faults", []),
            ikw_tr,
        )
        ai_explanation = _generate_ai_explanation(report_data)
        smart_alerts = _generate_smart_alerts(report_data)
        building_type = report_data.get("building_type", "office")

        record = {
            "report_id": new_id,
            "is_visible": True,
            "timestamp": timestamp,
            "timestamp_short": timestamp_short,
            "building_name": report_data.get("building", "Unknown"),
            "building_type": building_type,
            "district": report_data.get("address", "Unknown"),
            "address": report_data.get("formatted_address", report_data.get("address", "")),
            "latitude": report_data.get("lat"),
            "longitude": report_data.get("lon"),
            "outdoor_temperature": report_data.get("outdoor_temp"),
            "humidity": report_data.get("humidity"),
            "occupancy": report_data.get("input_occupancy"),
            "indoor_temperature": report_data.get("input_indoor_temp"),
            "predicted_cooling_load": report_data.get("cooling_load"),
            "cooling_load_tr": report_data.get("cooling_load_tr"),
            "peak_load": report_data.get("peak_load"),
            "predicted_monthly_kwh": report_data.get("predicted_monthly_kwh"),
            "recommended_temperature": report_data.get("recommended_temp"),
            "energy_savings": report_data.get("energy_saving"),
            "efficiency_score": report_data.get("efficiency_score"),
            "efficiency_status": report_data.get("efficiency_status"),
            "comfort_status": report_data.get("comfort_status"),
            "climate_zone": report_data.get("climate_zone"),
            "wind_speed": report_data.get("wind_speed"),
            "weather_condition": report_data.get("weather_condition"),
            "faults": report_data.get("faults", []),
            "priority": report_data.get("priority"),
            "actions": report_data.get("actions", []),
            # New intelligence fields
            "hvac_efficiency": eff,
            "weather_impact": weather_impact,
            "system_health": health,
            "ai_explanation": ai_explanation,
            "smart_alerts": smart_alerts,
            "system_status": health["status"],
            # Full original
            "full_report": report_data,
        }

        reports.append(record)
        _write_all(reports)

    return {
        "report_id": new_id,
        "building": record["building_name"],
        "timestamp": timestamp,
        "timestamp_short": timestamp_short,
    }


def get_report(report_id: int) -> Optional[dict]:
    reports = _read_all()
    for r in reports:
        if r.get("report_id") == report_id:
            return r
    return None


def get_all_reports() -> list[dict]:
    """Return summary list of visible reports."""
    reports = _visible(_read_all())
    summaries = []
    for r in reports:
        summaries.append({
            "report_id": r.get("report_id"),
            "building": r.get("building_name", "Unknown"),
            "building_type": r.get("building_type", ""),
            "address": r.get("district", r.get("address", "")),
            "timestamp": r.get("timestamp", ""),
            "timestamp_short": r.get("timestamp_short", ""),
            "system_status": r.get("system_status", ""),
        })
    return summaries


def get_report_count() -> int:
    return len(_visible(_read_all()))


def delete_report(report_id: int) -> bool:
    """Soft-delete: set is_visible = False."""
    with _lock:
        reports = _read_all()
        found = False
        for r in reports:
            if r.get("report_id") == report_id:
                r["is_visible"] = False
                found = True
                break
        if not found:
            return False
        _write_all(reports)
        return True


def delete_all_reports() -> int:
    """Soft-delete all: set is_visible = False on every report."""
    with _lock:
        reports = _read_all()
        count = 0
        for r in reports:
            if r.get("is_visible", True):
                r["is_visible"] = False
                count += 1
        _write_all(reports)
        return count


def get_analytics() -> dict:
    """Calculate analytics from all visible reports."""
    reports = _visible(_read_all())
    if not reports:
        return {
            "total_reports": 0,
            "avg_cooling_load": 0,
            "avg_recommended_temp": 0,
            "total_energy_saved": "0%",
            "avg_efficiency_score": 0,
            "building_types": {},
        }

    cooling_loads = [
        float(r["predicted_cooling_load"])
        for r in reports
        if r.get("predicted_cooling_load") is not None
    ]
    temps = [
        float(r["recommended_temperature"])
        for r in reports
        if r.get("recommended_temperature") is not None
    ]
    savings = []
    for r in reports:
        s = r.get("energy_savings", "0%")
        if isinstance(s, str):
            s = s.replace("%", "")
        try:
            savings.append(float(s))
        except (ValueError, TypeError):
            pass

    eff_scores = [
        float(r["efficiency_score"])
        for r in reports
        if r.get("efficiency_score") is not None
    ]

    btypes = {}
    for r in reports:
        bt = r.get("building_type", "office")
        btypes[bt] = btypes.get(bt, 0) + 1

    return {
        "total_reports": len(reports),
        "avg_cooling_load": round(sum(cooling_loads) / len(cooling_loads), 1) if cooling_loads else 0,
        "avg_recommended_temp": round(sum(temps) / len(temps), 1) if temps else 0,
        "total_energy_saved": f"{round(sum(savings) / len(savings), 1)}%" if savings else "0%",
        "avg_efficiency_score": round(sum(eff_scores) / len(eff_scores), 1) if eff_scores else 0,
        "building_types": btypes,
    }


def compare_reports(id_a: int, id_b: int) -> Optional[dict]:
    """Compare two reports side by side."""
    a = get_report(id_a)
    b = get_report(id_b)
    if not a or not b:
        return None

    def _diff(key_a, key_b=None):
        key_b = key_b or key_a
        va = a.get(key_a)
        vb = b.get(key_b)
        try:
            va_f, vb_f = float(va), float(vb)
            return {"report_a": va, "report_b": vb, "difference": round(vb_f - va_f, 2)}
        except (TypeError, ValueError):
            return {"report_a": va, "report_b": vb, "difference": "N/A"}

    return {
        "report_a_id": id_a,
        "report_b_id": id_b,
        "report_a_building": a.get("building_name"),
        "report_b_building": b.get("building_name"),
        "cooling_load": _diff("predicted_cooling_load"),
        "recommended_temp": _diff("recommended_temperature"),
        "energy_savings": _diff("energy_savings"),
        "efficiency_score": _diff("efficiency_score"),
        "outdoor_temperature": _diff("outdoor_temperature"),
        "humidity": _diff("humidity"),
    }


# by using this module we a can easily access the reports.json file and perform operations on it
