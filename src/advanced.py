"""
التحليل المتقدم للتشفير الخاص — Advanced Decrypt & Protection
يكتشف ما يدور بين السيرفر واللعبة بدون كسر — عبر Entropy + حجم + توقيت
Integrated v4.1 - 2026-08-07
"""
import math
from typing import Dict, Any

def calculate_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    freq = {}
    for b in data:
        freq[b] = freq.get(b, 0) + 1
    entropy = 0.0
    for count in freq.values():
        p = count / len(data)
        entropy -= p * math.log2(p)
    return round(entropy, 2)

def guess_inner_protocol(size: int, entropy: float, duration_ms: int) -> Dict[str, Any]:
    """
    تخمين نوع التشفير الداخلي الخاص بدون فك
    """
    if entropy > 7.5:
        proto = "Encrypted (AES-GCM)"
        color = "red"
        desc = "تشفير خاص قوي - Body مشفر"
    elif entropy > 6.0 and 200 < size < 5000:
        proto = "Protobuf"
        color = "blue"
        desc = "Protobuf مضغوط - بيانات منظمة"
    elif entropy < 4.5 and size < 2000:
        proto = "JSON"
        color = "green"
        desc = "JSON نصي - قابل للقراءة"
    elif size < 200:
        proto = "Heartbeat"
        color = "gray"
        desc = "Ping صغير - تحديث حالة"
    else:
        proto = "Mixed"
        color = "orange"
        desc = "مزيج - تحميل أصول"
    
    # حماية
    protection = "Stealth ON" if entropy < 8 else "Passthrough"
    
    return {
        "protocol_guess": proto,
        "color": color,
        "desc": desc,
        "entropy": entropy,
        "size": size,
        "duration_ms": duration_ms,
        "protection": protection,
        "stealth": True,
    }

def analyze_payload_metadata(payload_size: int, duration_ms: int, tls_version: str) -> Dict[str, Any]:
    """
    تحليل شامل لما يدور بين السيرفر واللعبة
    """
    # نحسب entropy وهمي حسب الحجم (لأننا لا نرى Body في Tunnel)
    # في Tunnel نحن نرى حجم TLS records فقط - نحسب تخمين
    fake_entropy = 7.8 if payload_size > 1000 else 5.2 if payload_size > 200 else 3.5
    guess = guess_inner_protocol(payload_size, fake_entropy, duration_ms)
    guess["outer_tls"] = tls_version
    guess["analysis"] = f"Outer {tls_version} + Inner {guess['protocol_guess']}"
    guess["risk"] = "Low - READ-ONLY" if guess["protection"]=="Stealth ON" else "Medium"
    return guess

def protection_headers() -> Dict[str, str]:
    """
    رؤوس الحماية - لا نكشف أننا بروكسي
    """
    return {
        "stealth": "ON",
        "via": "none",
        "x_forwarded": "none",
        "note": "نمرر كما هو بدون إضافة رؤوس تكشفنا",
    }
