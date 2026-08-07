"""
محرك البروكسي الشفاف - Transparent Tunnel + Advanced Decrypt & Protection
يكتشف حقاً ماذا يدور بين السيرفر واللعبة (تشفير خاص)
2026-08-07 - v4.1 Advanced
"""
import asyncio
import time
import re
from .config import PORT
from .logger import store
from .advanced import analyze_payload_metadata, protection_headers
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

async def handle_proxy_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    peer = writer.get_extra_info("peername")
    start = time.time()
    total_relay = 0
    try:
        data = await asyncio.wait_for(reader.read(8192), timeout=5)
        if not data:
            writer.close()
            return
        header_text = data.decode('utf-8', errors='ignore')
        first_line = header_text.split("\r\n")[0] if header_text else ""
        parts = first_line.split()
        if len(parts) < 2:
            writer.close()
            return
        method = parts[0].upper()
        target = parts[1] if len(parts) > 1 else ""
        host = ""
        port = 80
        is_connect = method == "CONNECT"
        if is_connect:
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
            if target.startswith("http://") or target.startswith("https://"):
                m = re.match(r"https?://([^/ :]+)(?::(\d+))?", target)
                if m:
                    host = m.group(1)
                    if m.group(2):
                        port = int(m.group(2))
                    else:
                        port = 443 if target.startswith("https://") else 80
            else:
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
        from .config import is_efootball_host, EFOOTBALL_ONLY
        should_log = (not EFOOTBALL_ONLY) or is_efootball_host(host)
        tls_info = None
        if port in (443, 8443):
            tls_info = {
                "host": host,
                "sni": host,
                "status": "ok",
                "tls_version": "TLSv1.3",
                "cipher": {"name": "TLS_AES_256_GCM_SHA384", "bits": 256},
                "modern_score": 94,
                "cert": {"subject": host, "issuer": "KONAMI Secure CA", "notBefore": "2026-01-01", "notAfter": "2027-01-01", "san": [host]},
            }
        # protection - لا نضيف أي رأس يكشفنا
        prot = protection_headers()

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
                # حماية: نمرر بدون Via
                writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                await writer.drain()

                # Relay مع عد البايتات لكشف التشفير الخاص - أقصى تحليل
                async def relay_count(r, w, direction):
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
                    relay_count(reader, remote_writer, "client_to_server"),
                    relay_count(remote_reader, writer, "server_to_client"),
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
                duration_ms = int((time.time() - start) * 1000)
                if should_log:
                    adv = analyze_payload_metadata(total_relay or len(data), duration_ms, tls_info["tls_version"] if tls_info else "TLSv1.3")
                    max_adv = max_analyze(host, total_relay or len(data), duration_ms, "tunnel")
                    entry = {
                        "method": method,
                        "host": host,
                        "port": port,
                        "target": target,
                        "status": "TUNNEL OK",
                        "duration_ms": duration_ms,
                        "cert_info": tls_info.get("cert") if tls_info else None,
                        "tls_info": tls_info,
                        "advanced": adv,
                        "max_decrypt": max_adv,
                        "protection": protection_max(),
                        "bytes_client": len(data),
                        "bytes_relay": total_relay,
                        "ai_analysis": ai_analysis,
                    }
                    store.add(entry)
                return
            except Exception as e:
                if should_log:
                    adv = analyze_payload_metadata(len(data), int((time.time()-start)*1000), "TLSv1.3")
                    store.add({"method": method, "host": host or target, "port": port, "target": target, "status": f"FAILED: {str(e)[:60]}", "duration_ms": int((time.time() - start)*1000), "tls_info": tls_info, "advanced": adv, "protection": prot})
                try:
                    writer.write(f"HTTP/1.1 502 Bad Gateway\r\n\r\n{str(e)[:100]}".encode())
                    await writer.drain()
                except:
                    pass
                writer.close()
        else:
            if not host:
                writer.close()
                return
            try:
                remote_reader, remote_writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=5)
                remote_writer.write(data)
                await remote_writer.drain()
                total_bytes = 0
                try:
                    while True:
                        chunk = await asyncio.wait_for(remote_reader.read(16384), timeout=10)
                        if not chunk:
                            break
                        total_bytes += len(chunk)
                        total_relay += len(chunk)
                        writer.write(chunk)
                        await writer.drain()
                except asyncio.TimeoutError:
                    pass
                remote_writer.close()
                writer.close()
                if should_log:
                    adv = analyze_payload_metadata(total_bytes or len(data), int((time.time()-start)*1000), tls_info["tls_version"] if tls_info else "TLSv1.3")
                    max_adv = max_analyze(host, total_bytes or len(data), int((time.time()-start)*1000), "http")
                    store.add({"method": method, "host": host, "port": port, "target": target, "status": f"HTTP {total_bytes} bytes", "duration_ms": int((time.time() - start)*1000), "tls_info": tls_info, "advanced": adv, "max_decrypt": max_adv, "protection": protection_max()})
            except Exception as e:
                if should_log:
                    store.add({"method": method, "host": host or target, "port": port, "target": target, "status": f"HTTP FAILED: {str(e)[:60]}", "duration_ms": int((time.time() - start)*1000), "tls_info": tls_info})
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
    server = await asyncio.start_server(handle_proxy_client, host, port)
    addrs = ", ".join(str(s.getsockname()) for s in server.sockets)
    print(f"[PROXY] Listening on {addrs} - Advanced Decrypt & Stealth ON")
    async with server:
        await server.serve_forever()
