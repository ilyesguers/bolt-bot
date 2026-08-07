# ⚡ eFootball Traffic Analyzer — v5.1

<div align="center">

![Version](https://img.shields.io/badge/version-5.1.0-00E676?style=for-the-badge)
![Build](https://img.shields.io/badge/build-passing-2962FF?style=for-the-badge)
![Platform](https://img.shields.io/badge/platform-Railway%20%7C%20iPhone%2013-0A1433?style=for-the-badge)
![Date](https://img.shields.io/badge/date-2026--08--08-FFCA28?style=for-the-badge)

**Proxy passthrough + Dashboard + AI-host traffic metadata + persistent feature preferences**

</div>

---

## ما الجديد في v5.1

- `src/ai_analyzer.py`: اكتشاف `pes22-game.cs.konami.net`، عينة محدودة إلى 1024 بايت، Entropy وإحصاءات الاتجاهين.
- `src/features.py`: خمس تفضيلات AI محفوظة ذرياً في `data/features.json` مع إشعارات محدودة في الذاكرة.
- تحليل اتصال AI في مساري التشغيل الفعليين: `src/main.py` و`src/proxy.py`.
- `GET/POST /api/features` و`GET /api/notifications` مع تحقق من المدخلات والحماية الحالية للوحة.
- لوحة عربية متجاوبة فيها خمسة checkboxes وزر حفظ وإشعارات مباشرة.

## حدود تقنية مهمة

اتصال HTTPS عبر `CONNECT` هو **نفق TLS مشفّر**. البروكسي الحالي يستطيع رؤية المضيف، الحجم، التوقيت وشكل ciphertext، لكنه لا يرى حقول اللعب أو قرار AI. في TLS 1.3، تعديل بايت عشوائي في ciphertext يفشل تحقق AEAD ويؤدي إلى إنهاء الاتصال؛ لذلك:

- حركة CONNECT تمر byte-for-byte من دون تعديل.
- تصنيف `AI Match Data / BehaviorTree / Config` تخمين مبني على الحجم وEntropy، وليس إثباتاً لبروتوكول داخلي.
- اختيارات لوحة AI تُحفظ وتظهر في التحليل، لكنها لا تُطبّق على TLS ciphertext.
- `modify_ai_payload()` موجود فقط لعينات مفكوكة/Offline؛ الـoffsets التجريبية ليست مخططاً موثقاً لبروتوكول KONAMI.
- لا توجد مطالبة بأن التشغيل أو الحساب محميان من الحظر؛ استخدام أدوات طرف ثالث يجب أن يراعي شروط الخدمة.

---

## المعمارية

```text
iPhone 13 (Manual HTTP Proxy over Wi-Fi)
    │
    ▼
Railway TCP Proxy domain:generated-port ──► Hybrid service:$PORT
                                              ├── CONNECT passthrough ──► destination
                                              └── HTTP dashboard ──────► FastAPI:8001
                                                     ├── Logs/Analytics
                                                     ├── AI metadata
                                                     └── Feature preferences
```

`*.up.railway.app` هو نطاق HTTP للوحة. للوصول إلى خادم البروكسي كـraw TCP يجب تفعيل **Railway TCP Proxy** على المنفذ الداخلي نفسه واستخدام النطاق والمنفذ اللذين يولدهما Railway.

---

## التشغيل

### محلياً

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m src.main
```

- Dashboard: `http://localhost:8080`
- Proxy: `localhost:8080`

### Railway

1. انشر الفرع المطلوب من GitHub.
2. أنشئ Public Domain للوحة، موجهاً إلى `$PORT`.
3. من **Settings → Networking → TCP Proxy**، أنشئ TCP Proxy للمنفذ الداخلي `$PORT`.
4. على iPhone: `الإعدادات → Wi‑Fi → ⓘ → تكوين البروكسي → يدوي`.
5. استخدم `RAILWAY_TCP_PROXY_DOMAIN` و`RAILWAY_TCP_PROXY_PORT`، وليس نطاق لوحة HTTP مع المنفذ 443.

> إعداد HTTP Proxy في iOS خاص بشبكة Wi‑Fi. بعض التطبيقات التي تستخدم networking مخصصاً قد لا تحترم إعداد النظام.

### متغيرات البيئة

| المتغير | الافتراضي | الوصف |
|---|---:|---|
| `PORT` | `8080` | منفذ الخدمة الداخلي |
| `DASHBOARD_TOKEN` | فارغ | حماية API واللوحة عند ضبطه |
| `DATA_DIR` | `data` | مسار logs وfeature preferences |
| `FEATURES_FILE` | `$DATA_DIR/features.json` | مسار مخصص للتفضيلات |
| `EFOOTBALL_ONLY` | `true` | تسجيل نطاقات eFootball فقط |

للاستمرار بعد إعادة نشر Railway، اربط Volume واضبط `DATA_DIR` إلى مساره؛ نظام ملفات الحاوية وحده ليس تخزيناً دائماً مضموناً.

---

## API

| Endpoint | الوصف |
|---|---|
| `GET /` | لوحة التحكم |
| `GET /health` | Health + uptime |
| `GET /api/logs` | السجلات والبحث |
| `GET /api/analytics` | التحليلات |
| `GET /api/files` | الملفات والمجموعات |
| `GET /api/features` | تعريفات الميزات وحالتها |
| `POST /api/features` | حفظ قيم `true/false` |
| `GET /api/notifications` | آخر عشرة إشعارات AI |
| `WS /ws/live` | تحديثات مباشرة |
| `GET /api/export/csv` | تصدير CSV |

مثال:

```bash
curl -X POST http://localhost:8080/api/features \
  -H 'content-type: application/json' \
  -d '{"features":{"slow_ai":true,"show_ai":false,"no_press":false,"stamina":false,"ai_miss":false}}'
```

---

## الاختبار

```bash
python3 -m py_compile src/*.py
python3 -m unittest discover -s tests -v
```

## الملفات الأساسية

```text
src/
  main.py             Hybrid entry point
  proxy.py            Standalone proxy handler
  ai_analyzer.py      Bounded AI-host metadata analyzer
  features.py         Preferences + notifications
  web.py              FastAPI + feature APIs
  templates/index.html
```
