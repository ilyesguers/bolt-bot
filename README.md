# eFootball Traffic Analyzer — v4.0 Integrated

> **نظام متكامل لقراءة وتحليل ترافيك eFootball على iPhone 13 — قراءة فقط + فك تشفير حديث + تخزين + تحليلات**
>
> **2026-08-07 • Africa/Algiers • Railway $0 • تحديث لحظي WebSocket**

![Version](https://img.shields.io/badge/version-4.0.0-blue)
![Status](https://img.shields.io/badge/status-integrated-green)
![Platform](https://img.shields.io/badge/platform-Railway%20%7C%20iPhone%2013-black)
![Cost](https://img.shields.io/badge/cost-$0-brightgreen)

---

## ✨ المميزات المتكاملة (Integrated)

| الميزة | الوصف |
|--------|-------|
| **🔓 Modern Decrypt** | TLS 1.3 + SNI + Cipher + Modern Score 100 لكل اتصال |
| **📁 File Organization** | كل اتصال كملف `category_host_id.log` + مجمع حسب السيرفر |
| **🔄 Live WebSocket** | تحديث لحظي بدون Refresh + Polling كاحتياطي |
| **💾 Persistent Storage** | حفظ في `data/logs.json` يبقى بعد Restart |
| **📊 Analytics** | رسوم حسب التصنيف/السيرفر + متوسط/أبطأ/أسرع + نسبة TLS 1.3 |
| **🔍 Search & Filter** | بحث + فلتر حسب التصنيف (api/auth/shop/match/cdn) |
| **📥 Export** | JSON + CSV بضغطة |
| **🔒 Auth** | حماية اختيارية عبر `DASHBOARD_TOKEN` |
| **📱 Mobile PWA** | يعمل كتطبيق على iPhone |
| **📚 API Docs** | `/docs` + `/health` |

---

## 🏗️ المعمارية

```
iPhone 13 (Wi-Fi Manual Proxy) → Railway:8080 (Hybrid)
    ├── Proxy (CONNECT Tunnel) → KONAMI (شفاف)
    └── WebSocket + FastAPI → Dashboard (Live)
            ├── Storage (data/logs.json)
            └── Analytics
```

---

## 🚀 التشغيل

### Railway (موصى به)
1. `git push origin arena/019fdca0-bolt-bot`
2. Railway → Deploy from GitHub → Domain `xxx.up.railway.app`
3. iPhone: `الإعدادات > Wi-Fi > ⓘ > تكوين البروكسي > يدوي` → Host `xxx.up.railway.app` Port `443`
4. افتح `https://xxx.up.railway.app/` → سترى كل شيء لحظياً

### محلي
```bash
pip install -r requirements.txt
python -m src.main  # Hybrid على 8080
# أو
uvicorn src.web:app --port 8080
```

---

## 🔧 المتغيرات

| المتغير | افتراضي | أين |
|---------|---------|-----|
| `PORT` | `8080` | Railway تلقائي |
| `LOG_LIMIT` | `800` | Variables |
| `EFOOTBALL_ONLY` | `true` | Variables |
| `DASHBOARD_TOKEN` | `` | Variables (اختياري) |
| `DATA_DIR` | `data` | Variables |

---

## 📂 الهيكل

```
src/
  main.py        # Hybrid (Proxy+Web)
  proxy.py       # CONNECT Tunnel
  web.py         # FastAPI + WS
  decrypt.py     # Modern Decrypt
  logger.py      # Logs + Storage
  storage.py     # Persistent
  analytics.py   # Charts
  config.py      # 2026-08-07
  templates/index.html # Integrated UI
data/
  logs.json      # تخزين مستمر
.github/workflows/deploy.yml
docs/
  CONFIGURATION.md
  DATA_READING.md
```

---

## 📚 API

- `GET /` → Dashboard
- `GET /health` → Health
- `GET /docs` → Swagger
- `GET /api/logs?search=&category=&limit=` → Logs
- `GET /api/analytics` → Charts
- `GET /api/files` → Files
- `GET /api/export` → JSON
- `GET /api/export/csv` → CSV
- `WS /ws/live` → Live

---

## 🔒 الأمان
READ-ONLY بدون تعديل — يمرر شفاف لتجنب الحظر — فلتر eFootball Only

---

**v4.0 Integrated • 2026-08-07 • جاهز للإنتاج**
