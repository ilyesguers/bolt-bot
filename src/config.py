"""
إعدادات المشروع - eFootball Traffic Analyzer
تكلفة $0 - Railway + iPhone 13
"""
import os

# المنفذ الذي تعطيه Railway (أو 8080 محلياً)
PORT = int(os.environ.get("PORT", "8080"))

# عدد السجلات المحفوظة في الذاكرة
LOG_LIMIT = int(os.environ.get("LOG_LIMIT", "500"))

# هل نعرض فقط ترافيك eFootball؟
EFOOTBALL_ONLY = os.environ.get("EFOOTBALL_ONLY", "true").lower() == "true"

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

# رسالة الترحيب
BANNER = """
╔════════════════════════════════════════════╗
║  eFootball Traffic Analyzer v3.0           ║
║  Mode: READ-ONLY (No Modification)        ║
║  Filter: eFootball Only                   ║
║  Port: {port} | Logs: {limit}             ║
╚════════════════════════════════════════════╝
""".format(port=PORT, limit=LOG_LIMIT)
