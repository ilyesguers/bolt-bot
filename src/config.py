"""
إعدادات المشروع - eFootball Traffic Analyzer
تكلفة $0 - Railway + iPhone 13
التحديث: 2026-08-07 - Africa/Algiers
الإصدار: v4.0 Integrated - كل الأفكار المفيدة متكاملة
"""
import os
from datetime import datetime

# التاريخ
TODAY = "2026-08-07"
VERSION = "4.0.0"
VERSION_NAME = "Integrated Professional"

# المنطقة الزمنية
TIMEZONE = "Africa/Algiers"

# المنفذ الذي تعطيه Railway (أو 8080 محلياً)
PORT = int(os.environ.get("PORT", "8080"))

# عدد السجلات المحفوظة في الذاكرة
LOG_LIMIT = int(os.environ.get("LOG_LIMIT", "800"))

# هل نعرض فقط ترافيك eFootball؟
EFOOTBALL_ONLY = os.environ.get("EFOOTBALL_ONLY", "true").lower() == "true"

# حماية اللوحة (اختياري)
DASHBOARD_TOKEN = os.environ.get("DASHBOARD_TOKEN", "").strip()

# دومينات eFootball الرسمية - أي شيء خارجها يتم تجاهله عند تفعيل الفلتر
EFOOTBALL_DOMAINS = [
    "konami.net",
    "konami.com",
    "pes.net",
    "efootball.com",
    "e-football.com",
    "konami-pes.com",
]

# كلمات مفتاحية إضافية في الـ Host للكشف
EFOOTBALL_KEYWORDS = [
    "konami",
    "pes",
    "efootball",
    "e-football",
]

# هل نفحص الشهادة لكل اتصال؟
FETCH_CERT_INFO = True

# مهلة جلب الشهادة (ثواني)
CERT_TIMEOUT = 3

# نظام فك التشفير الحديث
MODERN_DECRYPT = True
DECRYPT_MODE = "metadata"  # metadata فقط - بدون تعديل

# التخزين المستمر
PERSISTENT_STORAGE = True
DATA_DIR = os.environ.get("DATA_DIR", "data")

# التحليلات
ANALYTICS_ENABLED = True

def is_efootball_host(host: str) -> bool:
    """هل هذا Host يخص eFootball؟"""
    if not host:
        return False
    h = host.lower().strip()
    # إزالة المنفذ إن وجد
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
    """تصنيف Host لملفات منظمة"""
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

# رسالة الترحيب
BANNER = f"""
╔════════════════════════════════════════════════╗
║  eFootball Traffic Analyzer v{VERSION}        ║
║  {VERSION_NAME} - Integrated                 ║
║  Date: {TODAY} | {TIMEZONE}                  ║
║  Mode: READ-ONLY + Modern Decrypt + Storage  ║
║  Filter: eFootball Only | Live WS            ║
║  Port: {PORT} | Logs: {LOG_LIMIT}           ║
╚════════════════════════════════════════════════╝
"""
