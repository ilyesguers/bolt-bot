"""
نظام تسجيل Logs في الذاكرة - آمن وسريع
يحفظ آخر LOG_LIMIT سجل فقط - لا قاعدة بيانات (مناسب لـ Railway المجاني)
"""
import time
import uuid
import threading
from collections import deque
from typing import List, Dict, Any
from .config import LOG_LIMIT, EFOOTBALL_ONLY, is_efootball_host

class LogStore:
    def __init__(self, limit: int = LOG_LIMIT):
        self.limit = limit
        self._logs = deque(maxlen=limit)
        self._lock = threading.Lock()
        self._total = 0
        self._efootball_count = 0
        self._other_count = 0

    def add(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """إضافة سجل جديد - يطبق الفلتر تلقائياً"""
        host = entry.get("host", "")
        is_ef = is_efootball_host(host)
        
        # إذا كان الفلتر مفعل وأي Host ليس eFootball -> تجاهل
        if EFOOTBALL_ONLY and not is_ef:
            with self._lock:
                self._other_count += 1
            return None  # تم التجاهل

        entry["id"] = str(uuid.uuid4())[:8]
        entry["timestamp"] = time.time()
        entry["time_str"] = time.strftime("%H:%M:%S", time.localtime(entry["timestamp"]))
        entry["date_str"] = time.strftime("%Y-%m-%d", time.localtime(entry["timestamp"]))
        entry["is_efootball"] = is_ef
        entry.setdefault("method", "CONNECT")
        entry.setdefault("status", "TUNNEL")
        entry.setdefault("cert_info", None)

        with self._lock:
            self._logs.appendleft(entry)  # الأحدث أولاً
            self._total += 1
            if is_ef:
                self._efootball_count += 1
            else:
                self._other_count += 1

        return entry

    def get_all(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._logs)[:limit]

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total": self._total,
                "efootball": self._efootball_count,
                "other": self._other_count,
                "stored": len(self._logs),
                "limit": self.limit,
                "filter": "eFootball Only" if EFOOTBALL_ONLY else "All",
            }

    def clear(self):
        with self._lock:
            self._logs.clear()
            self._total = 0
            self._efootball_count = 0
            self._other_count = 0

# Singleton
store = LogStore()
