"""
Report Routes – /report
"""

from fastapi import APIRouter
from app.database import get_analysis, get_all_analyses

router = APIRouter(prefix="/report", tags=["Report"])


@router.get("/list")
async def list_reports():
    """List all generated reports."""
    return {"reports": get_all_analyses()}


@router.get("/{report_id}")
async def get_report(report_id: str):
    """Retrieve a specific report by ID."""
    result = get_analysis(report_id)
    if result is None:
        return {"error": "Report not found"}
    return result
