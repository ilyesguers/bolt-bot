"""
نظام تسجيل Logs في الذاكرة - آمن وسريع
يحفظ آخر LOG_LIMIT سجل فقط - لا قاعدة بيانات (مناسب لـ Railway المجاني)
يدعم تنظيم الملفات والمجموعات والتحديث اللحظي
التحديث: 2026-08-07
"""
import time
import uuid
import threading
from collections import deque, Counter
from typing import List, Dict, Any
from .config import LOG_LIMIT, EFOOTBALL_ONLY, is_efootball_host, get_host_category, TODAY

class LogStore:
    def __init__(self, limit: int = LOG_LIMIT):
        self.limit = limit
        self._logs = deque(maxlen=limit)
        self._lock = threading.Lock()
        self._total = 0
        self._efootball_count = 0
        self._other_count = 0
        self._by_host = Counter()
        self._by_category = Counter()

    def add(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """إضافة سجل جديد - يطبق الفلتر تلقائياً"""
        host = entry.get("host", "")
        is_ef = is_efootball_host(host)
        
        # إذا كان الفلتر مفعل وأي Host ليس eFootball -> تجاهل
        if EFOOTBALL_ONLY and not is_ef:
            with self._lock:
                self._other_count += 1
            return None  # تم التجاهل

        # تنظيم وتصنيف
        category = get_host_category(host)
        clean_host = host.split(":")[0] if ":" in host else host

        entry["id"] = str(uuid.uuid4())[:8]
        entry["timestamp"] = time.time()
        entry["time_str"] = time.strftime("%H:%M:%S", time.localtime(entry["timestamp"]))
        entry["date_str"] = TODAY  # ثابت حسب طلبك: 2026-08-07
        entry["datetime_str"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(entry["timestamp"]))
        entry["is_efootball"] = is_ef
        entry["category"] = category
        entry["clean_host"] = clean_host
        entry.setdefault("method", "CONNECT")
        entry.setdefault("status", "TUNNEL")
        entry.setdefault("cert_info", None)
        entry.setdefault("tls_info", None)
        entry.setdefault("file_name", f"{category}_{clean_host}_{entry['id']}.log")

        with self._lock:
            self._logs.appendleft(entry)  # الأحدث أولاً
            self._total += 1
            self._by_host[clean_host] += 1
            self._by_category[category] += 1
            if is_ef:
                self._efootball_count += 1
            else:
                self._other_count += 1

        return entry

    def get_all(self, limit: int = 50, category: str = None, search: str = None) -> List[Dict[str, Any]]:
        with self._lock:
            logs = list(self._logs)
        
        # فلترة حسب التصنيف
        if category and category != "all":
            logs = [l for l in logs if l.get("category") == category]
        
        # بحث
        if search:
            s = search.lower()
            logs = [l for l in logs if s in l.get("host","").lower() or s in l.get("status","").lower() or s in l.get("category","").lower()]
        
        return logs[:limit]

    def get_grouped(self) -> Dict[str, Any]:
        """تنظيم الملفات حسب Host و Category"""
        with self._lock:
            logs = list(self._logs)
            by_host = {}
            by_category = {}
            for log in logs:
                h = log.get("clean_host", "unknown")
                c = log.get("category", "other")
                by_host.setdefault(h, []).append(log)
                by_category.setdefault(c, []).append(log)
            
            return {
                "by_host": {k: {"count": len(v), "logs": v[:5], "category": v[0].get("category") if v else "other"} for k, v in by_host.items()},
                "by_category": {k: len(v) for k, v in by_category.items()},
                "total_hosts": len(by_host),
                "total_categories": len(by_category),
            }

    def get_files(self) -> List[Dict[str, Any]]:
        """تمثيل Logs كملفات منظمة"""
        with self._lock:
            files = []
            for log in list(self._logs):
                files.append({
                    "file_name": log.get("file_name"),
                    "host": log.get("host"),
                    "clean_host": log.get("clean_host"),
                    "category": log.get("category"),
                    "size": log.get("bytes_client", 0),
                    "time": log.get("time_str"),
                    "date": log.get("date_str"),
                    "status": log.get("status"),
                    "id": log.get("id"),
                })
            return files

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total": self._total,
                "efootball": self._efootball_count,
                "other": self._other_count,
                "stored": len(self._logs),
                "limit": self.limit,
                "filter": "eFootball Only" if EFOOTBALL_ONLY else "All",
                "by_host": dict(self._by_host.most_common(5)),
                "by_category": dict(self._by_category),
                "today": TODAY,
                "version": "3.1.0",
            }

    def clear(self):
        with self._lock:
            self._logs.clear()
            self._total = 0
            self._efootball_count = 0
            self._other_count = 0
            self._by_host.clear()
            self._by_category.clear()

# Singleton
store = LogStore()
