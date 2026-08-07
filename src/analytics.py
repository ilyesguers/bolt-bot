"""
التحليلات المتكاملة - Integrated Analytics
يحسب إحصائيات لحظية للرسم البياني والمراقبة
"""
import time
from collections import Counter, defaultdict
from typing import List, Dict

from .config import TODAY


def compute_analytics(logs: List[Dict]) -> Dict:
    if not logs:
        return {"empty": True, "today": TODAY}
    
    # توزيع حسب التصنيف
    by_cat = Counter(l.get("category","other") for l in logs)
    by_host = Counter(l.get("clean_host","unknown") for l in logs)
    by_status = Counter(l.get("status","unknown") for l in logs)
    
    # زمن الاستجابة
    durations = [l.get("duration_ms",0) for l in logs if l.get("duration_ms")]
    avg_ms = sum(durations)//len(durations) if durations else 0
    max_ms = max(durations) if durations else 0
    min_ms = min(durations) if durations else 0
    
    # نشاط بالدقائق (آخر 10 دقائق)
    now = time.time()
    per_min = defaultdict(int)
    for l in logs:
        diff = int((now - l.get("timestamp", now)) // 60)
        if diff < 10:
            per_min[f"{diff}m"] += 1
    
    # TLS
    tls13 = sum(1 for l in logs if l.get("tls_info",{}).get("tls_version")=="TLSv1.3")
    
    return {
        "total": len(logs),
        "by_category": dict(by_cat),
        "by_host": dict(by_host.most_common(5)),
        "by_status": dict(by_status),
        "avg_ms": avg_ms,
        "max_ms": max_ms,
        "min_ms": min_ms,
        "per_min": dict(per_min),
        "tls13_ratio": round(tls13/len(logs)*100) if logs else 0,
        "today": TODAY,
    }
