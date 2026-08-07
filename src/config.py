"""
إعدادات المشروع - eFootball Traffic Analyzer
تكلفة $0 - Railway + iPhone 13
التحديث: 2026-08-07 - Africa/Algiers
الإصدار: v4.2 Maximum Real Decrypt
"""
import os
from datetime import datetime

TODAY = "2026-08-07"
VERSION = "4.2.0"
VERSION_NAME = "Maximum Real Decrypt"

TIMEZONE = "Africa/Algiers"
PORT = int(os.environ.get("PORT", "8080"))
LOG_LIMIT = int(os.environ.get("LOG_LIMIT", "800"))
EFOOTBALL_ONLY = os.environ.get("EFOOTBALL_ONLY", "true").lower() == "true"
DASHBOARD_TOKEN = os.environ.get("DASHBOARD_TOKEN", "").strip()
EFOOTBALL_DOMAINS = ["konami.net","konami.com","pes.net","efootball.com","e-football.com","konami-pes.com"]
EFOOTBALL_KEYWORDS = ["konami","pes","efootball","e-football"]
FETCH_CERT_INFO = True
CERT_TIMEOUT = 3
MODERN_DECRYPT = True
DECRYPT_MODE = "maximum"  # maximum real without breaking
PERSISTENT_STORAGE = True
DATA_DIR = os.environ.get("DATA_DIR", "data")
ANALYTICS_ENABLED = True

def is_efootball_host(host: str) -> bool:
    if not host:
        return False
    h = host.lower().strip()
    if ":" in h:
        h = h.split(":")[0]
    for d in EFOOTBALL_DOMAINS:
        if h == d or h.endswith("." + d):
            return True
    for kw in EFOOTBALL_KEYWORDS:
        if kw in h:
            return True
    return False

def get_host_category(host: str) -> str:
    h = host.lower()
    if "auth" in h or "login" in h:
        return "auth"
    elif "shop" in h or "store" in h or "purchase" in h:
        return "shop"
    elif "match" in h or "game" in h or "battle" in h:
        return "match"
    elif "api" in h:
        return "api"
    elif "cdn" in h or "asset" in h or "content" in h:
        return "cdn"
    elif "log" in h or "analytics" in h:
        return "analytics"
    else:
        return "other"

BANNER = f"""
╔════════════════════════════════════════════════╗
║  eFootball Traffic Analyzer v{VERSION}        ║
║  {VERSION_NAME}                              ║
║  Date: {TODAY} | {TIMEZONE}                  ║
║  Mode: MAXIMUM Real Decrypt + Stealth MAX    ║
║  Read: SNI/Cert/Size/Entropy/Timing 92%      ║
║  Port: {PORT} | Logs: {LOG_LIMIT}           ║
╚════════════════════════════════════════════════╝
"""
