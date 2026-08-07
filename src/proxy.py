"""
محرك البروكسي الشفاف - Transparent Tunnel (READ-ONLY)
يدعم:
- HTTP Proxy (GET http://host/path)
- HTTPS Tunnel (CONNECT host:443)

الميزات:
- قراءة فقط: لا يعدل أي بايت في الطلب أو الرد
- يمرر البيانات كما هي (Tunnel) لتجنب كسر Pinning وتجنب الحظر
- يسجل Metadata + معلومات الشهادة فقط
- فلتر تلقائي: يسجل eFootball فقط عند تفعيل EFOOTBALL_ONLY

يعمل على نفس المنفذ مع FastAPI عبر التمييز:
- إذا كان الطلب Proxy (CONNECT أو absolute URL) -> عالجه كبروكسي
- إذا كان طلب عادي (GET /) -> مرره لـ FastAPI
"""
import asyncio
import time
import socket
import ssl
import re
from typing import Tuple

from .config import PORT, FETCH_CERT_INFO, CERT_TIMEOUT
from .logger import store

# لفحص الشهادة بدون تعطيل
def get_cert_info(host: str, port: int = 443) -> dict:
    """جلب معلومات الشهادة الحقيقية للسيرفر (بدون MITM)"""
    if not FETCH_CERT_INFO:
        return None
    # إزالة المنفذ إن وجد
    clean_host = host.split(":")[0].strip()
    if not clean_host or clean_host.startswith("192.168.") or clean_host.startswith("10."):
        return None
    try:
        ctx = ssl.create_default_context()
        # لا نحتاج تحقق صارم - فقط قراءة
        with socket.create_connection((clean_host, port), timeout=CERT_TIMEOUT) as sock:
            with ctx.wrap_socket(sock, server_hostname=clean_host) as ssock:
                cert = ssock.getpeercert()
                if not cert:
                    return {"host": clean_host, "status": "no cert"}
                # تحويل cert dict لمعلومات مقروءة
                issuer = ", ".join("=".join(x) for rdn in cert.get("issuer", []) for x in rdn) if cert.get("issuer") else "Unknown"
                subject = ", ".join("=".join(x) for rdn in cert.get("subject", []) for x in rdn) if cert.get("subject") else clean_host
                not_before = cert.get("notBefore", "")
                not_after = cert.get("notAfter", "")
                san = cert.get("subjectAltName", [])
                san_str = ", ".join([v for k, v in san[:3]]) if san else clean_host
                return {
                    "host": clean_host,
                    "subject": subject,
                    "issuer": issuer,
                    "notBefore": not_before,
                    "notAfter": not_after,
                    "san": san_str,
                    "status": "ok",
                }
    except Exception as e:
        return {"host": clean_host, "status": "error", "error": str(e)[:80]}

async def handle_proxy_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """معالجة عميل بروكسي واحد"""
    peer = writer.get_extra_info("peername")
    client_ip = peer[0] if peer else "unknown"
    start = time.time()
    try:
        # قراءة أول سطر
        data = await asyncio.wait_for(reader.read(8192), timeout=5)
        if not data:
            writer.close()
            return

        try:
            header_text = data.decode('utf-8', errors='ignore')
        except:
            header_text = ""

        # تحليل السطر الأول
        first_line = header_text.split("\r\n")[0] if header_text else ""
        parts = first_line.split()
        if len(parts) < 2:
            writer.close()
            return

        method = parts[0].upper()
        target = parts[1] if len(parts) > 1 else ""

        # تحديد Host والمنفذ
        host = ""
        port = 80
        is_connect = method == "CONNECT"

        if is_connect:
            # CONNECT api.efootball.konami.net:443 HTTP/1.1
            host_port = target
            if ":" in host_port:
                host, port_str = host_port.rsplit(":", 1)
                try:
                    port = int(port_str)
                except:
                    port = 443
            else:
                host = host_port
                port = 443
        else:
            # GET http://host/path  أو GET /path مع Host header
            if target.startswith("http://") or target.startswith("https://"):
                # absolute URL
                m = re.match(r"https?://([^/ :]+)(?::(\d+))?", target)
                if m:
                    host = m.group(1)
                    if m.group(2):
                        port = int(m.group(2))
                    else:
                        port = 443 if target.startswith("https://") else 80
                # المسار للتمرير سيكون path فقط، لكننا نمرر كما هو للشفافية
            else:
                # relative URL -> نحتاج Host header
                for line in header_text.split("\r\n")[1:]:
                    if line.lower().startswith("host:"):
                        h = line.split(":", 1)[1].strip()
                        if ":" in h:
                            host, port_str = h.rsplit(":", 1)
                            try:
                                port = int(port_str)
                            except:
                                port = 80
                        else:
                            host = h
                        break

        # تسجيل Log (قبل الاتصال)
        cert_info = None
        duration_ms = 0

        # جلب معلومات الشهادة في الخلفية (لا ننتظر طويلاً لتجنب التأخير)
        # نجلبه بعد إنشاء النفق لتجنب تأخير الاتصال
        # لكن نسجل مبدئياً بدون cert ثم نحدث

        entry = {
            "method": method,
            "host": host or target,
            "port": port,
            "client_ip": client_ip,
            "target": target,
            "bytes_client": len(data),
            "status": "CONNECTING",
            "cert_info": None,
        }
        # سيتم إضافته بعد معرفة إن كان eFootball
        # نحتاج نقرر هل نسجل أم لا
        from .config import is_efootball_host, EFOOTBALL_ONLY
        should_log = (not EFOOTBALL_ONLY) or is_efootball_host(host)

        if is_connect:
            # إنشاء اتصال للسيرفر الهدف
            try:
                remote_reader, remote_writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port), timeout=5
                )
                # رد للعميل: Connection Established
                writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                await writer.drain()

                # الآن النفق شفاف - نبدأ تمرير البيانات بدون تعديل
                # نسجل النجاح
                duration_ms = int((time.time() - start) * 1000)
                if should_log:
                    # جلب الشهادة الآن (سريع)
                    if port == 443:
                        cert_info = get_cert_info(host, port)
                    entry.update({
                        "status": "TUNNEL OK",
                        "duration_ms": duration_ms,
                        "cert_info": cert_info,
                    })
                    store.add(entry)

                # تمرير ثنائي الاتجاه
                async def relay(r, w):
                    try:
                        while True:
                            chunk = await r.read(16384)
                            if not chunk:
                                break
                            w.write(chunk)
                            await w.drain()
                    except:
                        pass
                    finally:
                        try:
                            w.close()
                        except:
                            pass

                await asyncio.gather(
                    relay(reader, remote_writer),
                    relay(remote_reader, writer),
                )

            except Exception as e:
                # فشل الاتصال
                if should_log:
                    entry.update({
                        "status": f"FAILED: {str(e)[:60]}",
                        "duration_ms": int((time.time() - start)*1000),
                    })
                    store.add(entry)
                try:
                    writer.write(f"HTTP/1.1 502 Bad Gateway\r\n\r\n{str(e)[:100]}".encode())
                    await writer.drain()
                except:
                    pass
                writer.close()
        else:
            # HTTP عادي (GET http://...)
            # للشفافية نمرر نفس البيانات للسيرفر الهدف
            if not host:
                writer.close()
                return
            try:
                remote_reader, remote_writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port), timeout=5
                )
                remote_writer.write(data)
                await remote_writer.drain()

                # قراءة الرد وتمريره
                # نمرر حتى ينتهي السيرفر
                total_bytes = 0
                try:
                    while True:
                        chunk = await asyncio.wait_for(remote_reader.read(16384), timeout=10)
                        if not chunk:
                            break
                        total_bytes += len(chunk)
                        writer.write(chunk)
                        await writer.drain()
                except asyncio.TimeoutError:
                    pass

                remote_writer.close()
                writer.close()

                if should_log:
                    duration_ms = int((time.time() - start) * 1000)
                    # محاولة استخراج Status Code
                    status_match = re.search(r"HTTP/\d\.\d\s+(\d+)", header_text)
                    entry.update({
                        "status": f"HTTP {total_bytes} bytes",
                        "duration_ms": duration_ms,
                    })
                    store.add(entry)

            except Exception as e:
                if should_log:
                    entry.update({
                        "status": f"HTTP FAILED: {str(e)[:60]}",
                        "duration_ms": int((time.time() - start)*1000),
                    })
                    store.add(entry)
                try:
                    writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                    await writer.drain()
                except:
                    pass
                writer.close()

    except Exception as e:
        try:
            writer.close()
        except:
            pass

async def start_proxy_server(host: str = "0.0.0.0", port: int = PORT):
    """تشغيل سيرفر البروكسي"""
    server = await asyncio.start_server(handle_proxy_client, host, port)
    addrs = ", ".join(str(s.getsockname()) for s in server.sockets)
    print(f"[PROXY] Listening on {addrs} - Mode: READ-ONLY Tunnel")
    async with server:
        await server.serve_forever()
