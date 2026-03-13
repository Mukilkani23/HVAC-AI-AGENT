"""HVAC AI Agent – In-Memory Database
Lightweight data store for hackathon demo (no external DB required)."""

from datetime import datetime

analysis_history: list[dict] = []
report_cache: dict[str, dict] = {}


def save_analysis(data: dict) -> str:
    """Persist an analysis result and return its ID."""
    record_id = f"RPT-{len(analysis_history) + 1:04d}"
    record = {
        "id": record_id,
        "timestamp": datetime.utcnow().isoformat(),
        **data,
    }
    analysis_history.append(record)
    report_cache[record_id] = record
    return record_id


def get_analysis(record_id: str) -> dict | None:
    return report_cache.get(record_id)


def get_all_analyses() -> list[dict]:
    return list(analysis_history)
