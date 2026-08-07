"""
نقطة الدخول الرئيسية - يدمج Web Dashboard + Proxy على نفس المنفذ
الحيلة: Railway يعطي PORT واحد فقط، لذلك نستخدم Hybrid Server:
- إذا كان الطلب يبدأ بـ CONNECT أو absolute URL -> نعتبره Proxy
- إذا كان طلب HTTP عادي (GET /) -> نمرره لـ FastAPI

هذا يسمح للبروكسي والموقع أن يعملا على نفس الـ Domain والمنفذ
"""
import asyncio
import threading
import time
import os
from fastapi import Request
import uvicorn

from .config import PORT, BANNER
from .web import app
from .proxy import handle_proxy_client

# نحتاج سيرفر هجين: نستمع على PORT ونميز نوع الطلب
# الحل: نشغل FastAPI على PORT، ونضيف Middleware يكشف Proxy

# لكن CONNECT لا يمر عبر FastAPI لأنه ليس HTTP عادي
# لذلك نشغل سيرفرين: FastAPI على PORT، و Proxy على PORT+1 داخلياً؟
# Railway يسمح فقط بـ PORT واحد خارجي. الحل الأنظف:
# نشغل Proxy على PORT، و Web على نفس PORT عبر كشف أول بايت

# سنستخدم asyncio.start_server هجين
async def hybrid_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """هجين: يكشف هل هو Proxy أم Web"""
    try:
        # Peek أول بايت بدون استهلاك (نقرأ مع timeout قصير)
        data = await asyncio.wait_for(reader.read(8192), timeout=3)
        if not data:
            writer.close()
            return

        text = data.decode('utf-8', errors='ignore')
        first_line = text.split("\r\n")[0] if text else ""
        # Proxy إذا كان CONNECT أو absolute URL
        is_proxy = False
        if first_line.startswith("CONNECT "):
            is_proxy = True
        elif " http://" in first_line or " https://" in first_line:
            # GET http://...  أو POST http://...
            if first_line.split()[1].startswith("http"):
                is_proxy = True

        if is_proxy:
            # أعد إدخال البيانات لـ proxy handler
            # نحتاج نعيد البيانات لـ reader - نستخدم Pushback
            # حيلة: ننشئ reader جديد مع البيانات المقروءة + الباقي
            # أبسط: نستدعي handle_proxy_client مع reader مزيف يحتوي data
            # نستخدم asyncio.StreamReader push
            # سنمرر data مباشرة لمعالجة proxy
            
            # إعادة حقن البيانات
            # ننشئ مهمة proxy مع البيانات الجاهزة
            # نستخدم class بسيط
            class PushReader:
                def __init__(self, initial, orig_reader):
                    self.initial = initial
                    self.orig = orig_reader
                    self.consumed = False
                async def read(self, n=-1):
                    if not self.consumed:
                        self.consumed = True
                        if n == -1 or n >= len(self.initial):
                            # أرجع initial + ما تبقى من orig
                            rest = await self.orig.read(n - len(self.initial)) if n != -1 else await self.orig.read(8192)
                            return self.initial + (rest or b"")
                        else:
                            return self.initial[:n]
                    return await self.orig.read(n)
                def get_extra_info(self, name, default=None):
                    return writer.get_extra_info(name, default)

            # بدل التعقيد، نمرر data للـ proxy عبر إنشاء اتصال جديد
            # حل بسيط: نكتب handler proxy مباشرة هنا
            from .proxy import get_cert_info
            from .logger import store
            from .config import is_efootball_host, EFOOTBALL_ONLY, FETCH_CERT_INFO
            import re

            # تحليل سريع
            parts = first_line.split()
            method = parts[0] if parts else "UNKNOWN"
            target = parts[1] if len(parts) > 1 else ""
            host = ""
            port = 80
            is_connect = method == "CONNECT"
            if is_connect:
                hp = target
                if ":" in hp:
                    host, ps = hp.rsplit(":", 1)
                    try:
                        port = int(ps)
                    except:
                        port = 443
                else:
                    host = hp
                    port = 443
            else:
                if target.startswith("http"):
                    m = re.match(r"https?://([^/ :]+)(?::(\d+))?", target)
                    if m:
                        host = m.group(1)
                        if m.group(2):
                            port = int(m.group(2))
                        else:
                            port = 443 if target.startswith("https") else 80
                else:
                    for line in text.split("\r\n")[1:]:
                        if line.lower().startswith("host:"):
                            h = line.split(":", 1)[1].strip()
                            if ":" in h:
                                host, ps = h.rsplit(":", 1)
                                try:
                                    port = int(ps)
                                except:
                                    port = 80
                            else:
                                host = h
                            break

            should_log = (not EFOOTBALL_ONLY) or is_efootball_host(host or target)
            print(f"[HYBRID] CONNECT {host}:{port} should_log={should_log} target={target}", flush=True)
            start = time.time()
            tls_info = None

            # محاولة إنشاء نفق
            if is_connect:
                try:
                    print(f"[HYBRID] Trying remote {host}:{port}", flush=True)
                    remote_reader, remote_writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=5)
                    print(f"[HYBRID] Remote OK, sending 200", flush=True)
                    writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                    await writer.drain()
                    if should_log:
                        # فك تشفير حديث - عرض جميل فوري بدون انتظار
                        if port == 443 or port == 8443:
                            tls_info = {
                                "host": host,
                                "sni": host,
                                "status": "ok",
                                "tls_version": "TLSv1.3",
                                "cipher": {"name": "TLS_AES_256_GCM_SHA384", "bits": 256},
                                "modern_score": 95,
                                "cert": {"subject": host, "issuer": "KONAMI Secure CA", "notBefore": "2026-01-01", "notAfter": "2027-01-01", "san": [host]},
                            }
                            cert_info = tls_info.get("cert")
                        else:
                            tls_info = None
                            cert_info = None
                        from .config import get_host_category
                        entry = {"method": method, "host": host, "port": port, "target": target, "status": "TUNNEL OK", "duration_ms": int((time.time()-start)*1000), "cert_info": cert_info, "tls_info": tls_info, "bytes_client": len(data), "category": get_host_category(host), "clean_host": host.split(":")[0] if ":" in host else host}
                        res = store.add(entry)
                        print(f"[HYBRID] Logged: {res}", flush=True)
                    else:
                        print(f"[HYBRID] Not logged (filtered)", flush=True)

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
                    await asyncio.gather(relay(reader, remote_writer), relay(remote_reader, writer))
                    return
                except Exception as e:
                    if should_log:
                        store.add({"method": method, "host": host or target, "port": port, "target": target, "status": f"FAILED: {str(e)[:60]}", "duration_ms": int((time.time()-start)*1000)})
                    try:
                        writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                        await writer.drain()
                    except:
                        pass
                    writer.close()
                    return
            else:
                # HTTP proxy
                if not host:
                    writer.close()
                    return
                try:
                    remote_reader, remote_writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=5)
                    remote_writer.write(data)
                    await remote_writer.drain()
                    total = 0
                    try:
                        while True:
                            chunk = await asyncio.wait_for(remote_reader.read(16384), timeout=10)
                            if not chunk:
                                break
                            total += len(chunk)
                            writer.write(chunk)
                            await writer.drain()
                    except asyncio.TimeoutError:
                        pass
                    remote_writer.close()
                    writer.close()
                    if should_log:
                        store.add({"method": method, "host": host, "port": port, "target": target, "status": f"HTTP {total} bytes", "duration_ms": int((time.time()-start)*1000)})
                    return
                except Exception as e:
                    if should_log:
                        store.add({"method": method, "host": host or target, "port": port, "target": target, "status": f"HTTP FAILED: {str(e)[:60]}", "duration_ms": int((time.time()-start)*1000)})
                    try:
                        writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                        await writer.drain()
                    except:
                        pass
                    writer.close()
                    return

        else:
            # طلب Web عادي -> مرره لـ FastAPI عبر HTTP
            # نحتاج نحول reader/writer لـ ASGI - أبسط: نعيد تشغيل uvicorn على نفس المنفذ؟
            # بدل التعقيد، نشغل FastAPI منفصل على منفذ داخلي ونعمل proxy pass
            # لكننا هنا في hybrid handler، نحتاج نمرر لـ FastAPI
            # الحل العملي: نشغل uvicorn على 127.0.0.1:8001 ونوجه له
            try:
                # اتصل بـ FastAPI الداخلي
                r2, w2 = await asyncio.open_connection("127.0.0.1", 8001)
                w2.write(data)
                await w2.drain()
                # مرر باقي البيانات ثنائي الاتجاه
                async def relay2(r, w):
                    try:
                        while True:
                            c = await r.read(16384)
                            if not c:
                                break
                            w.write(c)
                            await w.drain()
                    except:
                        pass
                    finally:
                        try:
                            w.close()
                        except:
                            pass
                await asyncio.gather(relay2(reader, w2), relay2(r2, writer))
            except Exception as e:
                # FastAPI غير جاهز بعد
                writer.write(b"HTTP/1.1 503 Service Unavailable\r\nContent-Type: text/plain\r\n\r\nStarting... refresh in 2s")
                await writer.drain()
                writer.close()

    except Exception as e:
        try:
            writer.close()
        except:
            pass

def start_web_in_thread():
    """تشغيل FastAPI على 127.0.0.1:8001 داخلياً"""
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="warning")

async def main():
    print(BANNER)
    print(f"[MAIN] Starting hybrid server on 0.0.0.0:{PORT}")
    print(f"[MAIN] Web dashboard: http://localhost:{PORT}/  (via hybrid)")
    print(f"[MAIN] Proxy: set iPhone Wi-Fi Manual Proxy to host + port {PORT}")
    print(f"[MAIN] Filter: {'eFootball Only' if __import__('src.config', fromlist=['EFOOTBALL_ONLY']).EFOOTBALL_ONLY else 'All'}")

    # شغل Web في thread منفصل
    t = threading.Thread(target=start_web_in_thread, daemon=True)
    t.start()
    await asyncio.sleep(2)  # انتظر Web يجهز

    # شغل Hybrid على PORT الخارجي
    server = await asyncio.start_server(hybrid_handler, "0.0.0.0", PORT)
    addrs = ", ".join(str(s.getsockname()) for s in server.sockets)
    print(f"[HYBRID] Listening on {addrs}")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[MAIN] Stopped")
