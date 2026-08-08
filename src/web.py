"""
Web Dashboard - FastAPI - Integrated v5.2
Live WebSocket (stats + logs + notifications) + Analytics + AI Feature Engine + Auth
2026-08-08
"""
from fastapi import FastAPI, Request, Query, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import json
import asyncio
import csv
import io

from .config import EFOOTBALL_ONLY, EFOOTBALL_DOMAINS, TODAY, VERSION, VERSION_NAME
from .logger import store
from .analytics import compute_analytics
from .auth import check_auth
from .match_tracker import tracker
from .netctl import (
    active_sessions,
    get_actions,
    get_setting,
    kill_all,
    load_settings,
    record_action,
    save_settings as save_netctl,
)
from .modmenu import FEATURES as MODMENU_FEATURES
from .modmenu import config_payload, get_enabled as get_modmenu_enabled
from .modmenu import load_config, save_config as save_modmenu
from .features import (
    FEATURES,
    TARGETS,
    TIMINGS,
    add_notification,
    feature_statuses,
    get_enabled,
    get_last_analysis,
    get_notifications,
    load_features,
    load_prefs,
    save_prefs,
)

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

# خلفية ترسل تحديثات كل ثانيتين (إشعارات + حالة مباراة + سجلات)
async def ws_broadcaster():
    while True:
        await asyncio.sleep(2)
        if ws_manager.active:
            try:
                data = {
                    "type": "update",
                    "stats": store.get_stats(),
                    "logs": store.get_all(limit=10),
                    "notifications": get_notifications(),
                    "match": tracker.snapshot(),
                }
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
        "mode": "INTEGRATED - READ-ONLY + Feature Engine + Live WS + Storage",
        "version": VERSION,
        "version_name": VERSION_NAME,
        "today": TODAY,
        "features": ["Live WebSocket","Persistent Storage","Analytics Charts","File Organization","Modern Decrypt","Auto Update","CSV Export","Auth","Match Phase Estimator","Feature Status"],
    }


def _features_response():
    state = load_features()
    prefs = load_prefs()
    analysis = get_last_analysis()
    match = tracker.snapshot()
    statuses = feature_statuses(analysis, match["phase"])
    return {
        "features": FEATURES,
        "state": state,
        "targets": prefs["targets"],
        "timings": prefs["timings"],
        "enabled": [key for key, value in state.items() if value],
        "mode": "metadata_only",
        "can_modify_tls": False,
        "phase": match,
        "statuses": statuses,
        "targets_def": TARGETS,
        "timings_def": TIMINGS,
        "last_analysis": analysis,
        "notice": "CONNECT/TLS مشفر؛ ميزات التعديل تُحفظ لكن ciphertext يمر دون تعديل. ميزات الرصد (تنبيهات/أطوار/بينغ) تعمل على الميتاداتا.",
    }


@app.get("/api/features")
async def api_features(auth=Depends(check_auth)):
    return _features_response()


@app.post("/api/features")
async def api_features_update(request: Request, auth=Depends(check_auth)):
    try:
        payload = await request.json()
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail="JSON body مطلوب")

    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="يجب إرسال JSON object")

    # الصيغة الجديدة: {"features": {...}, "targets": {...}, "timings": {...}}
    # الصيغة القديمة: {"slow_ai": true, ...}
    if "features" in payload and isinstance(payload["features"], dict):
        features_raw = payload.get("features")
        targets_raw = payload.get("targets", {})
        timings_raw = payload.get("timings", {})
    else:
        features_raw = payload
        targets_raw = {}
        timings_raw = {}

    if not isinstance(features_raw, dict):
        raise HTTPException(status_code=422, detail="features يجب أن تكون object")

    unknown = sorted(set(features_raw) - set(FEATURES))
    if unknown:
        raise HTTPException(
            status_code=422,
            detail={"message": "ميزات غير معروفة", "keys": unknown},
        )
    invalid = sorted(key for key, value in features_raw.items() if type(value) is not bool)
    if invalid:
        raise HTTPException(
            status_code=422,
            detail={"message": "قيم الميزات يجب أن تكون true/false", "keys": invalid},
        )

    if targets_raw:
        if not isinstance(targets_raw, dict):
            raise HTTPException(status_code=422, detail="targets يجب أن تكون object")
        unknown_t = sorted(set(targets_raw) - set(FEATURES))
        if unknown_t:
            raise HTTPException(status_code=422, detail={"message": "أهداف غير معروفة", "keys": unknown_t})
        invalid_t = sorted(key for key, value in targets_raw.items() if value not in TARGETS)
        if invalid_t:
            raise HTTPException(status_code=422, detail={"message": "قيم أهداف غير صالحة", "keys": invalid_t})

    if timings_raw:
        if not isinstance(timings_raw, dict):
            raise HTTPException(status_code=422, detail="timings يجب أن تكون object")
        unknown_ti = sorted(set(timings_raw) - set(FEATURES))
        if unknown_ti:
            raise HTTPException(status_code=422, detail={"message": "توقيتات غير معروفة", "keys": unknown_ti})
        invalid_ti = sorted(key for key, value in timings_raw.items() if value not in TIMINGS)
        if invalid_ti:
            raise HTTPException(status_code=422, detail={"message": "قيم توقيت غير صالحة", "keys": invalid_ti})

    saved = save_prefs(features=features_raw, targets=targets_raw, timings=timings_raw)
    enabled_names = [FEATURES[key]["name"] for key, value in saved["features"].items() if value]
    add_notification(
        "تم حفظ تفضيلات ميزات AI"
        + (f": {', '.join(enabled_names)}" if enabled_names else " — جميعها متوقفة"),
        level="success",
        enabled=get_enabled(),
    )
    return _features_response()


@app.get("/api/notifications")
async def api_notifications(auth=Depends(check_auth)):
    items = get_notifications()
    return {"notifications": items, "count": len(items)}


@app.get("/api/match")
async def api_match(auth=Depends(check_auth)):
    analysis = get_last_analysis()
    return {
        "match": tracker.snapshot(),
        "last_ai_analysis": analysis,
        "statuses": feature_statuses(analysis, tracker.snapshot()["phase"]),
    }


def _modmenu_response():
    cfg = load_config()
    return {
        "features": MODMENU_FEATURES,
        "state": cfg["features"],
        "enabled": get_modmenu_enabled(),
        "updated_at": cfg["updated_at"],
        "protocol": cfg["protocol"],
        "notice": (
            "المباراة ضد الكمبيوتر تُلعب على جهازك — هذه الإعدادات يقرأها "
            "التطبيق المعدّل (IPA + dylib) ويطبّقها محلياً. البروكسي لا يعدّل "
            "أي شيء لأن المباراة ليست على الشبكة."
        ),
    }


@app.get("/api/modmenu")
async def api_modmenu(auth=Depends(check_auth)):
    return _modmenu_response()


@app.post("/api/modmenu")
async def api_modmenu_update(request: Request, auth=Depends(check_auth)):
    try:
        payload = await request.json()
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail="JSON body مطلوب")

    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="يجب إرسال JSON object")

    values = payload.get("features", payload)
    if not isinstance(values, dict):
        raise HTTPException(status_code=422, detail="features يجب أن تكون object")

    unknown = sorted(set(values) - set(MODMENU_FEATURES))
    if unknown:
        raise HTTPException(
            status_code=422,
            detail={"message": "ميزات مود مينو غير معروفة", "keys": unknown},
        )
    invalid = sorted(key for key, value in values.items() if type(value) is not bool)
    if invalid:
        raise HTTPException(
            status_code=422,
            detail={"message": "قيم الميزات يجب أن تكون true/false", "keys": invalid},
        )

    saved = save_modmenu(values)
    enabled_names = [MODMENU_FEATURES[key]["name"] for key, value in saved["features"].items() if value]
    add_notification(
        "🛠️ تم حفظ إعدادات المود مينو"
        + (f": {', '.join(enabled_names)}" if enabled_names else " — جميعها متوقفة"),
        level="success",
        enabled=get_modmenu_enabled(),
    )
    return _modmenu_response()


@app.get("/api/modmenu/config")
async def api_modmenu_config(auth=Depends(check_auth)):
    """صيغة خفيفة للتطبيق المعدّل — يقرأها الـ dylib كل بضع ثوانٍ."""
    return config_payload()


def _netctl_response():
    settings = load_settings()
    return {
        "settings": settings,
        "sessions": active_sessions(),
        "actions": get_actions(),
        "mode": "proxy_only",
        "notice": (
            "تحكمات شبكية بحتة تعمل عبر البروكسي فقط. لا يمكنها تغيير ذكاء AI "
            "أو النتيجة داخل اللعبة (الآفلان محسوب على جهازك، والأونلاين مشفر "
            "ومتحقق منه السيرفر). قطع الاتصال قد يُحتسب هزيمة أو إلغاء حسب "
            "سياسة اللعبة."
        ),
    }


@app.get("/api/netctl")
async def api_netctl(auth=Depends(check_auth)):
    return _netctl_response()


@app.post("/api/netctl")
async def api_netctl_update(request: Request, auth=Depends(check_auth)):
    try:
        payload = await request.json()
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail="JSON body مطلوب")

    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="يجب إرسال JSON object")

    values = payload.get("settings", payload)

    if "throttle_kbps" in values:
        try:
            throttle = int(values["throttle_kbps"])
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail="throttle_kbps يجب أن يكون رقماً")
        if not (0 <= throttle <= 200_000):
            raise HTTPException(status_code=422, detail="throttle_kbps بين 0 و 200000")

    if "block_hosts" in values:
        if not isinstance(values["block_hosts"], list):
            raise HTTPException(status_code=422, detail="block_hosts يجب أن تكون قائمة")
        if len(values["block_hosts"]) > 50:
            raise HTTPException(status_code=422, detail="block_hosts بحد أقصى 50 نطاقاً")

    if "result_guard" in values and type(values["result_guard"]) is not bool:
        raise HTTPException(status_code=422, detail="result_guard يجب أن يكون true/false")

    saved = save_netctl(values)
    add_notification(
        "🎛️ حُدّثت إعدادات التحكم الشبكي",
        level="info",
        settings={k: saved[k] for k in ("throttle_kbps", "block_hosts", "result_guard")},
    )
    return _netctl_response()


@app.post("/api/netctl/kill")
async def api_netctl_kill(auth=Depends(check_auth)):
    count = kill_all("طلب يدوي من اللوحة")
    if count:
        add_notification(f"🔌 قُطعت {count} اتصال نشط من لوحة التحكم", level="warning", killed=count)
    return {"killed": count, "sessions": active_sessions()}


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

def _dashboard_context():
    return {
        "stats": store.get_stats(),
        "logs": store.get_all(limit=50),
        "files": store.get_files()[:50],
        "grouped": store.get_grouped(),
        "is_efootball_only": EFOOTBALL_ONLY,
        "domains": EFOOTBALL_DOMAINS,
        "today": TODAY,
        "version": VERSION,
        "version_name": VERSION_NAME,
        "ai_features": FEATURES,
        "enabled_features": load_features(),
        "targets_def": TARGETS,
        "timings_def": TIMINGS,
        "prefs": load_prefs(),
        "match": tracker.snapshot(),
        "notifications": get_notifications(),
        "modmenu_features": MODMENU_FEATURES,
        "modmenu_state": load_config()["features"],
        "netctl_settings": load_settings(),
        "netctl_sessions": active_sessions(),
        "netctl_actions": get_actions(),
    }

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, auth=Depends(check_auth)):
    return templates.TemplateResponse(request, "index.html", _dashboard_context())

# صفحة بسيطة للهاتف
@app.get("/m", response_class=HTMLResponse)
async def mobile(request: Request, auth=Depends(check_auth)):
    return templates.TemplateResponse(request, "index.html", _dashboard_context())
