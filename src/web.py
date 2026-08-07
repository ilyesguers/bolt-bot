"""
Web Dashboard - FastAPI - Integrated v4.0
Live WebSocket + Analytics + Storage + Auth
2026-08-07
"""
from fastapi import FastAPI, Request, Query, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import time
import json
import asyncio
import csv
import io

from .config import EFOOTBALL_ONLY, EFOOTBALL_DOMAINS, TODAY, VERSION, VERSION_NAME
from .logger import store
from .analytics import compute_analytics
from .auth import check_auth

app = FastAPI(
    title="eFootball Traffic Analyzer",
    description="Integrated Professional Dashboard - Live + Analytics",
    version=VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# WebSocket manager
class WSManager:
    def __init__(self):
        self.active: list[WebSocket] = []
    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)
    async def broadcast(self, data: dict):
        for ws in self.active[:]:
            try:
                await ws.send_json(data)
            except:
                self.disconnect(ws)

ws_manager = WSManager()

# خلفية ترسل تحديثات كل ثانيتين
async def ws_broadcaster():
    while True:
        await asyncio.sleep(2)
        if ws_manager.active:
            try:
                data = {"type":"update","stats": store.get_stats(), "logs": store.get_all(limit=10)}
                await ws_manager.broadcast(data)
            except:
                pass

@app.on_event("startup")
async def startup():
    asyncio.create_task(ws_broadcaster())

@app.get("/health")
async def health():
    return {"status":"ok","mode":"integrated","filter":"eFootball Only" if EFOOTBALL_ONLY else "all","today":TODAY,"version":VERSION,"uptime":store.get_stats()["uptime_str"]}

@app.get("/api/stats")
async def api_stats(auth=Depends(check_auth)):
    return store.get_stats()

@app.get("/api/analytics")
async def api_analytics(auth=Depends(check_auth)):
    logs = store.get_all(limit=200)
    return compute_analytics(logs)

@app.get("/api/logs")
async def api_logs(limit: int = Query(50, le=500), category: str = None, search: str = None, auth=Depends(check_auth)):
    return {"logs": store.get_all(limit=limit, category=category, search=search), "stats": store.get_stats(), "today": TODAY}

@app.get("/api/files")
async def api_files(auth=Depends(check_auth)):
    return {"files": store.get_files()[:200], "grouped": store.get_grouped(), "stats": store.get_stats(), "today": TODAY}

@app.get("/api/grouped")
async def api_grouped(auth=Depends(check_auth)):
    return store.get_grouped()

@app.post("/api/clear")
async def api_clear(auth=Depends(check_auth)):
    store.clear()
    return {"status":"cleared","today":TODAY}

@app.get("/api/config")
async def api_config(auth=Depends(check_auth)):
    return {
        "filter": "eFootball Only" if EFOOTBALL_ONLY else "All",
        "domains": EFOOTBALL_DOMAINS,
        "mode": "INTEGRATED - READ-ONLY + Modern Decrypt + Live WS + Storage",
        "version": VERSION,
        "version_name": VERSION_NAME,
        "today": TODAY,
        "features": ["Live WebSocket","Persistent Storage","Analytics Charts","File Organization","Modern Decrypt","Auto Update","CSV Export","Auth"],
    }

@app.get("/api/export")
async def api_export(auth=Depends(check_auth)):
    return {"export_date": TODAY, "version": VERSION, "logs": store.get_all(limit=800), "stats": store.get_stats()}

@app.get("/api/export/csv")
async def api_export_csv(auth=Depends(check_auth)):
    logs = store.get_all(limit=800)
    output = io.StringIO()
    w = csv.writer(output)
    w.writerow(["id","time","host","category","status","duration_ms","tls_version"])
    for l in logs:
        w.writerow([l.get("id"), l.get("datetime_str"), l.get("host"), l.get("category"), l.get("status"), l.get("duration_ms"), l.get("tls_info",{}).get("tls_version","")])
    return PlainTextResponse(output.getvalue(), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=efootball_{TODAY}.csv"})

@app.websocket("/ws/live")
async def ws_live(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        await ws.send_json({"type":"hello","today":TODAY,"version":VERSION})
        while True:
            await ws.receive_text()  # keep alive
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, auth=Depends(check_auth)):
    # نقل التوكن للواجهة
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

# صفحة بسيطة للهاتف
@app.get("/m", response_class=HTMLResponse)
async def mobile(request: Request, auth=Depends(check_auth)):
    return templates.TemplateResponse(request, "index.html", {
        "stats": store.get_stats(),
        "logs": store.get_all(limit=30),
        "files": store.get_files()[:30],
        "grouped": store.get_grouped(),
        "is_efootball_only": EFOOTBALL_ONLY,
        "domains": EFOOTBALL_DOMAINS,
        "today": TODAY,
        "version": VERSION,
        "version_name": VERSION_NAME,
    })
