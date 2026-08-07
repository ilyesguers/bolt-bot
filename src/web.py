"""
Web Dashboard - FastAPI - Professional v3.1
يعرض Logs الخاصة بـ eFootball فقط + معلومات الشهادة + تنظيم ملفات
نظام فك تشفير حديث + تحديث لحظي
التحديث: 2026-08-07
"""
from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import time

from .config import EFOOTBALL_ONLY, EFOOTBALL_DOMAINS, TODAY, VERSION, VERSION_NAME
from .logger import store

app = FastAPI(
    title="eFootball Traffic Analyzer",
    description="Professional Read-Only Proxy Dashboard - Modern Decryption",
    version=VERSION,
)

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

@app.get("/health")
async def health():
    return {"status": "ok", "mode": "read-only + modern-decrypt", "filter": "eFootball Only" if EFOOTBALL_ONLY else "all", "time": time.time(), "today": TODAY, "version": VERSION}

@app.get("/api/stats")
async def api_stats():
    return store.get_stats()

@app.get("/api/logs")
async def api_logs(limit: int = Query(50, le=200), category: str = None, search: str = None):
    return {"logs": store.get_all(limit=limit, category=category, search=search), "stats": store.get_stats(), "today": TODAY}

@app.get("/api/files")
async def api_files():
    """ملفات منظمة - كل Log كملف"""
    return {"files": store.get_files()[:100], "grouped": store.get_grouped(), "stats": store.get_stats(), "today": TODAY}

@app.get("/api/grouped")
async def api_grouped():
    return store.get_grouped()

@app.post("/api/clear")
async def api_clear():
    store.clear()
    return {"status": "cleared", "today": TODAY}

@app.get("/api/config")
async def api_config():
    return {
        "filter": "eFootball Only" if EFOOTBALL_ONLY else "All Traffic",
        "domains": EFOOTBALL_DOMAINS,
        "mode": "READ-ONLY + Modern Decryption (Metadata)",
        "version": VERSION,
        "version_name": VERSION_NAME,
        "today": TODAY,
        "decrypt": "TLS 1.3 + Certificate Chain + SNI - No Body Decryption (Safe)",
        "note": "يمرر البيانات شفافاً ويسجل Metadata + TLS Info فقط لتجنب الحظر",
    }

@app.get("/api/export")
async def api_export():
    """تصدير كل Logs كـ JSON"""
    return {"export_date": TODAY, "version": VERSION, "logs": store.get_all(limit=500), "stats": store.get_stats()}

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    try:
        return templates.TemplateResponse(request, "index.html", {
            "stats": store.get_stats(),
            "logs": store.get_all(limit=50),
            "files": store.get_files()[:50],
            "grouped": store.get_grouped(),
            "is_efootball_only": EFOOTBALL_ONLY,
            "domains": EFOOTBALL_DOMAINS,
            "today": TODAY,
            "version": VERSION,
            "version_name": VERSION_NAME,
        })
    except TypeError:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "stats": store.get_stats(),
            "logs": store.get_all(limit=50),
            "files": store.get_files()[:50],
            "grouped": store.get_grouped(),
            "is_efootball_only": EFOOTBALL_ONLY,
            "domains": EFOOTBALL_DOMAINS,
            "today": TODAY,
            "version": VERSION,
            "version_name": VERSION_NAME,
        })
