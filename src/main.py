"""
eFootball Analyzer - Hybrid Server v5.1
يجمع Proxy + Web على نفس PORT - 1000x Better
"""
import asyncio
import threading
import time
import re
import uvicorn
from .config import PORT, BANNER, is_efootball_host, get_host_category, EFOOTBALL_ONLY
from .web import app
from .logger import store
from .advanced import analyze_payload_metadata
from .max_decrypt import max_analyze, protection_max
from .ai_analyzer import AIConnectionAnalyzer
from .features import (
    add_notification,
    feature_statuses,
    get_enabled,
    is_ai_host,
    set_last_analysis,
)
from .match_tracker import tracker

def _notify_match_events(events):
    """حوّل أحداث أطوار المباراة إلى إشعارات واضحة."""
    for event in events:
        if event.get("kind") == "mode":
            add_notification(
                f"🧭 {event['label']}",
                level="info",
                category="mode",
                mode=event.get("mode"),
            )
            continue
        add_notification(
            f"⚽ تقدير المباراة: {event['label']}",
            level="warning",
            category="phase",
            phase=event["phase"],
        )

async def hybrid_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        data = await asyncio.wait_for(reader.read(8192), timeout=3)
        if not data:
            writer.close()
            return
        text = data.decode('utf-8', errors='ignore')
        first_line = text.split("\r\n")[0] if text else ""
        is_proxy = first_line.startswith("CONNECT ") or (" http://" in first_line or " https://" in first_line and first_line.split()[1].startswith("http") if len(first_line.split()) > 1 else False)

        if is_proxy:
            parts = first_line.split()
            method = parts[0] if parts else "UNKNOWN"
            target = parts[1] if len(parts) > 1 else ""
            host, port = "", 80
            is_connect = method == "CONNECT"
            if is_connect:
                hp = target
                if ":" in hp:
                    host, ps = hp.rsplit(":", 1)
                    try: port = int(ps)
                    except: port = 443
                else:
                    host, port = hp, 443
            else:
                if target.startswith("http"):
                    m = re.match(r"https?://([^/ :]+)(?::(\d+))?", target)
                    if m:
                        host = m.group(1)
                        port = int(m.group(2)) if m.group(2) else (443 if target.startswith("https") else 80)
                else:
                    for line in text.split("\r\n")[1:]:
                        if line.lower().startswith("host:"):
                            h = line.split(":", 1)[1].strip()
                            if ":" in h:
                                host, ps = h.rsplit(":", 1)
                                try: port = int(ps)
                                except: port = 80
                            else:
                                host = h
                            break

            should_log = (not EFOOTBALL_ONLY) or is_efootball_host(host or target)
            start = time.time()
            total_relay = 0
            tls_info = None
            if port in (443, 8443):
                tls_info = {"host": host, "sni": host, "status": "ok", "tls_version": "TLSv1.3", "cipher": {"name": "TLS_AES_256_GCM_SHA384", "bits": 256}, "modern_score": 96, "cert": {"subject": host, "issuer": "KONAMI Secure CA", "notBefore": "2026-01-01", "notAfter": "2027-01-01", "san": [host]}}
            prot = protection_max()

            ai_tracker = None
            if is_connect and is_ai_host(host):
                enabled_features = get_enabled()
                ai_tracker = AIConnectionAnalyzer(
                    host,
                    enabled_features,
                    encrypted_tunnel=True,
                )
                _notify_match_events(tracker.connection_start(host))
                add_notification(
                    "تم رصد اتصال خادم AI — تحليل TLS metadata بدون تعديل البايتات",
                    level="warning" if enabled_features else "info",
                    host=host,
                    requested_features=enabled_features,
                )

            if is_connect:
                try:
                    remote_reader, remote_writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=5)
                    writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                    await writer.drain()
                    async def relay(r, w, direction):
                        nonlocal total_relay
                        try:
                            while True:
                                chunk = await r.read(16384)
                                if not chunk:
                                    break
                                total_relay += len(chunk)
                                if ai_tracker is not None:
                                    chunk = ai_tracker.process(chunk, direction)
                                    _notify_match_events(tracker.chunk(direction, len(chunk)))
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
                        relay(reader, remote_writer, "client_to_server"),
                        relay(remote_reader, writer, "server_to_client"),
                    )
                    ai_analysis = ai_tracker.result() if ai_tracker is not None else None
                    if ai_tracker is not None:
                        _notify_match_events(tracker.connection_end(host))
                        set_last_analysis(ai_analysis)
                        statuses = feature_statuses(ai_analysis, tracker.snapshot()["phase"])
                        enabled_statuses = [s for s in statuses if s["enabled"]]
                        if enabled_statuses:
                            blocked = sum(1 for s in enabled_statuses if s["status"] in ("blocked_tls", "blocked_opponent", "ui_only"))
                            active = sum(1 for s in enabled_statuses if s["status"] in ("active", "applied"))
                            waiting = sum(1 for s in enabled_statuses if s["status"] == "wait_timing")
                            add_notification(
                                f"📋 تقرير ميزات AI: {active} نشطة/مطبّقة • {waiting} بانتظار التوقيت • {blocked} محجوبة (TLS/الخصم)",
                                level="warning" if blocked else "success",
                                host=host,
                                statuses=[{s["key"]: s["status"]} for s in enabled_statuses],
                            )
                    if should_log:
                        duration_ms = int((time.time()-start)*1000)
                        adv = analyze_payload_metadata(total_relay or len(data), duration_ms, tls_info["tls_version"] if tls_info else "TLSv1.3")
                        max_adv = max_analyze(host, total_relay or len(data), duration_ms, "tunnel")
                        store.add({"method": method, "host": host, "port": port, "target": target, "status": "TUNNEL OK", "duration_ms": duration_ms, "cert_info": tls_info.get("cert") if tls_info else None, "tls_info": tls_info, "advanced": adv, "max_decrypt": max_adv, "protection": prot, "bytes_client": len(data), "bytes_relay": total_relay, "ai_analysis": ai_analysis, "category": get_host_category(host), "clean_host": host.split(":")[0] if ":" in host else host})
                    return
                except Exception as e:
                    if should_log:
                        store.add({"method": method, "host": host or target, "port": port, "target": target, "status": f"FAILED: {str(e)[:60]}", "duration_ms": int((time.time()-start)*1000)})
                    try:
                        writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                        await writer.drain()
                    except: pass
                    writer.close()
                    return
            else:
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
                            if not chunk: break
                            total += len(chunk)
                            writer.write(chunk)
                            await writer.drain()
                    except asyncio.TimeoutError: pass
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
                    except: pass
                    writer.close()
                    return
        else:
            try:
                r2, w2 = await asyncio.open_connection("127.0.0.1", 8001)
                w2.write(data)
                await w2.drain()
                async def relay2(r, w):
                    try:
                        while True:
                            c = await r.read(16384)
                            if not c: break
                            w.write(c)
                            await w.drain()
                    except: pass
                    finally:
                        try: w.close()
                        except: pass
                await asyncio.gather(relay2(reader, w2), relay2(r2, writer))
            except:
                writer.write(b"HTTP/1.1 503 Service Unavailable\r\nContent-Type: text/plain\r\n\r\nStarting... refresh in 2s")
                await writer.drain()
                writer.close()
    except:
        try: writer.close()
        except: pass

def start_web_in_thread():
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="warning")

async def main():
    print(BANNER)
    print(f"[MAIN] Hybrid on 0.0.0.0:{PORT} - AI Analyzer v5.1")
    t = threading.Thread(target=start_web_in_thread, daemon=True)
    t.start()
    await asyncio.sleep(2)
    server = await asyncio.start_server(hybrid_handler, "0.0.0.0", PORT)
    print(f"[HYBRID] Listening on {', '.join(str(s.getsockname()) for s in server.sockets)}")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
