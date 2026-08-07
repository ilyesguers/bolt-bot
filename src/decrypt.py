"""
نظام فك التشفير الحديث - Modern Decryption System
يقرأ ويحلل بيانات TLS/HTTPS بدون تعديل - READ-ONLY
يعرض معلومات الشهادة، SNI، Cipher، TLS Version بشكل جميل
"""
import ssl
import socket
import time
from typing import Dict, Any, Optional

def get_modern_tls_info(host: str, port: int = 443, timeout: int = 3) -> Dict[str, Any]:
    """
    جلب معلومات TLS الحديثة بشكل جميل ومنظم
    - لا يفك تشفير Body المشفر (Pinning)
    - يقرأ فقط Metadata: TLS Version, Cipher, Cert Chain
    """
    clean_host = host.split(":")[0].strip()
    if not clean_host or clean_host.startswith("192.168.") or clean_host.startswith("10.") or clean_host.startswith("127."):
        return None

    result = {
        "host": clean_host,
        "port": port,
        "sni": clean_host,
        "status": "unknown",
        "tls_version": None,
        "cipher": None,
        "alpn": None,
        "cert": None,
        "chain_len": 0,
        "modern_score": 0,
    }

    try:
        ctx = ssl.create_default_context()
        # نطلب احدث اصدارات TLS
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        start = time.time()
        with socket.create_connection((clean_host, port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            with ctx.wrap_socket(sock, server_hostname=clean_host) as ssock:
                # TLS Version & Cipher
                result["tls_version"] = ssock.version()  # مثل TLSv1.3
                cipher = ssock.cipher()  # (name, protocol, bits)
                if cipher:
                    result["cipher"] = {
                        "name": cipher[0],
                        "protocol": cipher[1],
                        "bits": cipher[2],
                    }
                result["alpn"] = ssock.selected_alpn_protocol()
                
                # الشهادة
                cert = ssock.getpeercert(binary_form=False)
                chain = ssock.getpeercert(binary_form=True)
                # نحاول جلب binary chain
                result["chain_len"] = 1 if chain else 0
                
                if cert:
                    # Issuer
                    issuer = ", ".join("=".join(x) for rdn in cert.get("issuer", []) for x in rdn) if cert.get("issuer") else "Unknown"
                    subject = ", ".join("=".join(x) for rdn in cert.get("subject", []) for x in rdn) if cert.get("subject") else clean_host
                    san = [v for k, v in cert.get("subjectAltName", [])][:5] if cert.get("subjectAltName") else [clean_host]
                    
                    # حساب Modern Score
                    score = 0
                    if result["tls_version"] == "TLSv1.3":
                        score += 40
                    elif result["tls_version"] == "TLSv1.2":
                        score += 25
                    if result["cipher"] and result["cipher"]["bits"] >= 256:
                        score += 30
                    if "DigiCert" in issuer or "Let's Encrypt" in issuer or "Google" in issuer:
                        score += 20
                    if cert.get("notAfter"):
                        score += 10
                    result["modern_score"] = min(score, 100)

                    result["cert"] = {
                        "subject": subject,
                        "issuer": issuer,
                        "notBefore": cert.get("notBefore", ""),
                        "notAfter": cert.get("notAfter", ""),
                        "san": san,
                        "serial": cert.get("serialNumber", "")[:16] if cert.get("serialNumber") else "",
                    }
                    result["status"] = "ok"
                    result["handshake_ms"] = int((time.time() - start) * 1000)
                else:
                    result["status"] = "no cert"

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)[:100]

    return result

def format_tls_badge(tls_version: str) -> str:
    """لون شارة TLS"""
    if tls_version == "TLSv1.3":
        return "badge-tls13"
    elif tls_version == "TLSv1.2":
        return "badge-tls12"
    return "badge-tls-old"

def get_file_icon(host: str) -> str:
    """ايقونة ملف حسب الدومين"""
    h = host.lower()
    if "auth" in h:
        return "🔐"
    elif "shop" in h or "store" in h:
        return "🛒"
    elif "match" in h or "game" in h:
        return "⚽"
    elif "api" in h:
        return "🔌"
    elif "cdn" in h or "asset" in h:
        return "📦"
    elif "log" in h:
        return "📝"
    else:
        return "📄"

def get_decrypt_status_display(log: Dict[str, Any]) -> Dict[str, str]:
    """
    حالة فك التشفير الحديثة - عرض جميل
    """
    tls = log.get("tls_info")
    if not tls:
        return {"label": "Metadata Only", "color": "gray", "icon": "🔍", "desc": "نفق شفاف - بدون فك Body (Pinning)"}
    
    if tls.get("status") == "ok" and tls.get("tls_version") == "TLSv1.3":
        return {"label": "TLS 1.3 Encrypted", "color": "green", "icon": "🔒", "desc": "تشفير حديث - قراءة Metadata فقط"}
    elif tls.get("status") == "ok":
        return {"label": f"{tls.get('tls_version')} Secured", "color": "blue", "icon": "🛡️", "desc": "اتصال آمن - قراءة فقط"}
    else:
        return {"label": "Handshake", "color": "orange", "icon": "🤝", "desc": tls.get("error","")[:40]}
