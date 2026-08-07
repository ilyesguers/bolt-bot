"""
Web Dashboard - FastAPI
يعرض Logs الخاصة بـ eFootball فقط + معلومات الشهادة
يعمل على نفس المنفذ مع Proxy (يتم التمييز عبر Host/Path)
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import time

from .config import EFOOTBALL_ONLY, EFOOTBALL_DOMAINS
from .logger import store

app = FastAPI(
    title="eFootball Traffic Analyzer",
    description="Read-Only Proxy Dashboard - eFootball Only",
    version="3.0.0",
)

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

@app.get("/health")
async def health():
    return {"status": "ok", "mode": "read-only", "filter": "eFootball Only" if EFOOTBALL_ONLY else "all", "time": time.time()}

@app.get("/api/stats")
async def api_stats():
    return store.get_stats()

@app.get("/api/logs")
async def api_logs(limit: int = 50):
    return {"logs": store.get_all(limit=limit), "stats": store.get_stats()}

@app.post("/api/clear")
async def api_clear():
    store.clear()
    return {"status": "cleared"}

@app.get("/api/config")
async def api_config():
    return {
        "filter": "eFootball Only" if EFOOTBALL_ONLY else "All Traffic",
        "domains": EFOOTBALL_DOMAINS,
        "mode": "READ-ONLY - No Modification",
        "note": "هذا البروكسي لا يعدل أي بايت - يمرر البيانات شفافاً ويسجل Metadata فقط لتجنب الحظر",
    }

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    # Compatibility for Starlette >=0.36 (request first)
    try:
        return templates.TemplateResponse(request, "index.html", {
            "stats": store.get_stats(),
            "logs": store.get_all(limit=50),
            "is_efootball_only": EFOOTBALL_ONLY,
            "domains": EFOOTBALL_DOMAINS,
        })
    except TypeError:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "stats": store.get_stats(),
            "logs": store.get_all(limit=50),
            "is_efootball_only": EFOOTBALL_ONLY,
            "domains": EFOOTBALL_DOMAINS,
        })

@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    try:
        return templates.TemplateResponse(request, "index.html", {
            "stats": store.get_stats(),
            "logs": store.get_all(limit=100),
            "is_efootball_only": EFOOTBALL_ONLY,
            "domains": EFOOTBALL_DOMAINS,
        })
    except TypeError:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "stats": store.get_stats(),
            "logs": store.get_all(limit=100),
            "is_efootball_only": EFOOTBALL_ONLY,
            "domains": EFOOTBALL_DOMAINS,
        })
