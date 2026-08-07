"""
eFootball Traffic Analyzer - Final Edition
2026-08-08 - Africa/Algiers - iPhone 13 + Railway $0
v5.1 - AI Traffic Metadata + Feature Controls
"""
import os

TODAY = "2026-08-08"
VERSION = "5.1.0"
VERSION_NAME = "AI Traffic Metadata + Feature Controls"
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
DECRYPT_MODE = "maximum"
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
╔════════════════════════════════════════════════════╗
║  eFootball Traffic Analyzer v{VERSION}            ║
║  {VERSION_NAME}                                   ║
║  {TODAY} | {TIMEZONE} | iPhone 13 | Railway $0    ║
║  TLS Metadata + AI Feature Controls               ║
╚════════════════════════════════════════════════════╝
"""
