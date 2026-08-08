"""فحص حي: الإنهاء يحجب اللعبة فقط واللوحـة تبقى متاحة."""
import socket
import time
import urllib.request
import json

BASE = "http://127.0.0.1:8080"


def open_connect(host, port=443):
    s = socket.create_connection(("127.0.0.1", 8080), timeout=5)
    s.sendall(f"CONNECT {host}:{port} HTTP/1.1\r\nHost: {host}:{port}\r\n\r\n".encode())
    resp = s.recv(4096).decode(errors="ignore")
    return s, resp


def post(path, body=None):
    data = json.dumps(body).encode() if body is not None else b"{}"
    req = urllib.request.Request(BASE + path, data=data, headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode())


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=10) as r:
        return r.status, r.read().decode(errors="ignore")


game_sock, game_resp = open_connect("pes22-game.cs.konami.net")
yt_sock, yt_resp = open_connect("www.youtube.com")
dash_sock, dash_resp = open_connect("bolt-bot-production-629c.up.railway.app")
print("tunnels:", game_resp.splitlines()[0], "|", yt_resp.splitlines()[0], "|", dash_resp.splitlines()[0])
time.sleep(0.5)

result = post("/api/netctl/finish", {"cooldown_sec": 60})
print("killed:", result["killed"])
print("blocked_hosts:", result["blocked_hosts"])
assert result["killed"] == 1, "يجب قطع جلسة اللعبة فقط"
assert "pes22-game.cs.konami.net" in result["blocked_hosts"]
assert "www.youtube.com" not in result["blocked_hosts"]
assert "bolt-bot-production-629c.up.railway.app" not in result["blocked_hosts"]

# اللوحة تبقى متاحة (لا 403 على دوميننا)
status, _ = get("/")
print("dashboard status after finish:", status)
assert status == 200

# يوتيوب غير محجوب أثناء الكولداون؛ اللعبة محجوبة
s_yt, r_yt = open_connect("www.youtube.com")
print("youtube after finish:", r_yt.splitlines()[0])
assert "200" in r_yt.splitlines()[0]
s_game, r_game = open_connect("pes22-game.cs.konami.net")
print("game after finish:", r_game.splitlines()[0])
assert "403" in r_game.splitlines()[0]
s_dash, r_dash = open_connect("bolt-bot-production-629c.up.railway.app")
print("dashboard-domain after finish:", r_dash.splitlines()[0])
assert "403" not in r_dash.splitlines()[0]

# الإشعارات: نفس إشعار الحجب لا يتكرر
time.sleep(0.3)
with urllib.request.urlopen(BASE + "/api/notifications", timeout=10) as r:
    notifs = json.loads(r.read().decode())["notifications"]
block_notifs = [n for n in notifs if n["msg"].startswith("🛡️ حُجب الاتصال بـ pes22-game")]
print("block notifications count:", len(block_notifs))
assert len(block_notifs) == 1

print("ALL LIVE CHECKS PASSED")
