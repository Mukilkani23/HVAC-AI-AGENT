"""
📋 Report History Routes – /reports
API endpoints: list, get, save, soft-delete, analytics, comparison.
ADDITIVE – does NOT modify any existing routes.
"""

from fastapi import APIRouter
from app.report_storage import (
    save_report, get_report, get_all_reports,
    get_report_count, delete_report, delete_all_reports,
    get_analytics, compare_reports,
)

router = APIRouter(prefix="/reports", tags=["Report History"])


@router.get("")
async def list_reports():
    """GET /reports – list all visible reports."""
    reports = get_all_reports()
    return {"total_reports": len(reports), "reports": reports}


@router.get("/count")
async def report_count():
    """GET /reports/count"""
    return {"total_reports": get_report_count()}


@router.get("/analytics")
async def analytics_dashboard():
    """GET /reports/analytics – aggregated stats from reports.json."""
    return get_analytics()


@router.get("/compare/{id_a}/{id_b}")
async def compare_two_reports(id_a: int, id_b: int):
    """GET /reports/compare/{id_a}/{id_b}"""
    result = compare_reports(id_a, id_b)
    if result is None:
        return {"error": "One or both reports not found"}
    return result


@router.get("/{report_id}")
async def get_report_by_id(report_id: int):
    """GET /reports/{report_id}"""
    result = get_report(report_id)
    if result is None:
        return {"error": "Report not found", "report_id": report_id}
    return result


@router.post("/save")
async def save_report_entry(report_data: dict):
    """POST /reports/save – auto-save after generation."""
    summary = save_report(report_data)
    return {"status": "saved", **summary}


@router.delete("/{report_id}")
async def delete_report_by_id(report_id: int):
    """DELETE /reports/{report_id} – soft delete."""
    success = delete_report(report_id)
    if not success:
        return {"error": "Report not found", "report_id": report_id}
    return {"status": "deleted", "report_id": report_id}


@router.delete("")
async def clear_all_reports_endpoint():
    """DELETE /reports – soft delete all."""
    count = delete_all_reports()
    return {"status": "cleared", "deleted_count": count}
