import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import APP_TITLE, VERSION
from app.routes import location_routes, forecast_routes, diagnostic_routes, report_routes, ai_routes, report_history_routes

app = FastAPI(title=APP_TITLE, version=VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(location_routes.router)
app.include_router(forecast_routes.router)
app.include_router(diagnostic_routes.router)
app.include_router(report_routes.router)
app.include_router(ai_routes.router)
app.include_router(report_history_routes.router)

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

if FRONTEND_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    async def serve_frontend():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": VERSION}