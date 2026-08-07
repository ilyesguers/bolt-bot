# eFootball Traffic Analyzer — Mitmproxy + Railway

> **أداة تحليل شبكة احترافية لدراسة ترافيك eFootball على iPhone 13 — قراءة فقط (Read-Only) بدون تعديل**
>
> تكلفة $0 — تعمل على Railway + شهادة Mitmproxy المجانية — تعرض Logs خاصة بـ eFootball فقط مع معلومات الشهادة

![Status](https://img.shields.io/badge/status-production-green)
![Platform](https://img.shields.io/badge/platform-Railway%20%7C%20iPhone%2013-blue)
![Cost](https://img.shields.io/badge/cost-%240-brightgreen)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## 🎯 الفكرة

بروكسي تحليلي **آمن 100%** يمرر ترافيك eFootball عبر سيرفرك الخاص على Railway ويعرض في موقع ويب خاص بك:

- كل اتصال يفتحه eFootball (الدومين، الوقت، الحجم، زمن الاستجابة)
- معلومات شهادة TLS لكل اتصال (Issuer, Valid, Fingerprint)
- **فلتر تلقائي:** يعرض فقط دومينات eFootball ويتجاهل كل شيء آخر (واتساب، يوتيوب...)

**لا يتم تعديل أي بايت** — قراءة وتحليل فقط. هذا يجنب الحظر تماماً لأنه لا يغير منطق اللعبة ولا يرسل بيانات مزورة للسيرفر.

---

## 🏗️ المعمارية

```
iPhone 13 (Wi-Fi Manual Proxy) 
    │
    │  CONNECT api.efootball.konami.net:443
    ▼
Railway App (PORT)
    ├── Proxy Engine (CONNECT + HTTP) → يمرر البيانات شفافاً + يسجل Metadata
    └── Web Dashboard (/ , /logs , /api/logs) → يعرض Logs لحظياً
    │
    └──> KONAMI Servers (بدون تعديل)
```

**لماذا لا نفك تشفير Body؟**
eFootball تطبق Certificate Pinning. حتى مع تثبيت شهادة Mitmproxy وعمل Trust، التطبيق يرفض الشهادة المزورة. محاولة كسر Pinning تتطلب تعديل IPA وهذا يحول المشروع لـ Mod ويعرضك للحظر. لذلك نبقى على **Metadata + Certificate Info** — وهو كافٍ للدراسة وآمن تماماً.

---

## 📱 iPhone 13 — الإعداد (دقيقتان)

### 1. نشر البروكسي على Railway
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template)

أو يدوياً:
```bash
git push origin arena/019fdca0-bolt-bot  # Railway مربوط بـ GitHub
```

### 2. ضبط البروكسي على الآيفون
`الإعدادات > Wi-Fi > ⓘ بجانب شبكتك > تكوين البروكسي > يدوي`
- الخادم: `xxx.up.railway.app` (انسخه من Railway)
- المنفذ: `443` (Railway يستخدم 443 مع TLS)

> **ملاحظة Mitmproxy CA:** في هذا الإصدار (CONNECT Tunnel) لا تحتاج تثبيت شهادة Mitmproxy لأنه لا يفك التشفير — يمرر نفق TLS كما هو. هذا يجنبك خطوة Trust ويجعل الحظر مستحيلاً.

### 3. افتح موقع الـ Logs
`https://xxx.up.railway.app/` — سترى كل اتصالات eFootball لحظياً

---

## 🚀 التشغيل المحلي

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m src.main
# افتح http://localhost:8080
# اضبط بروكسي جهازك على 127.0.0.1:8080
```

---

## 📂 هيكل المشروع

```
.
├── src/
│   ├── main.py          # نقطة الدخول - يدمج Proxy + Web على نفس المنفذ
│   ├── proxy.py         # محرك البروكسي (CONNECT + HTTP) - شفاف بدون تعديل
│   ├── web.py           # FastAPI Dashboard
│   ├── config.py        # دومينات eFootball + إعدادات
│   ├── logger.py        # تخزين Logs في الذاكرة (آخر 500)
│   └── templates/
│       ├── index.html   # لوحة التحكم الرئيسية
│       └── logs.html    # صفحة Logs (بديل)
├── docs/
│   ├── KNOWLEDGE_BASE_V3_mitmproxy_railway.md
│   └── SETUP_iPhone13.md
├── requirements.txt
├── railway.json
├── Dockerfile
└── README.md
```

---

## 🔒 الأمان وتجنب الحظر

| الإجراء | الحالة |
|---------|--------|
| قراءة Metadata فقط بدون تعديل | ✅ آمن |
| عدم فك تشفير Body المشفر (Pinning) | ✅ آمن |
| فلتر يعرض eFootball فقط | ✅ يحمي الخصوصية |
| تمرير شفاف (Tunnel) بدون MITM | ✅ لا يترك بصمة |
| تعديل قيم أو تسريع | ❌ غير موجود - محظور |

**القاعدة الذهبية:** أي شيء يغير نتيجة مباراة أونلاين = كشف فوري عبر Server Reconciliation لدى KONAMI. لذلك هذا المشروع لا يحتوي على أي كود تعديل.

---

## ⚙️ الإعدادات

| متغير | وصف | افتراضي |
|-------|-----|---------|
| `PORT` | منفذ Railway | `8080` |
| `LOG_LIMIT` | عدد Logs المحفوظة | `500` |
| `EFOOTBALL_ONLY` | فلتر eFootball فقط | `true` |

---

## 📚 التوثيق

- `docs/KNOWLEDGE_BASE_V3_mitmproxy_railway.md` — القاعدة التقنية الشاملة
- `docs/SETUP_iPhone13.md` — دليل iPhone 13 خطوة بخطوة مع صور

---

## 🛠️ التطوير

```bash
pip install -r requirements.txt
uvicorn src.web:app --reload --port 8080
```

---

## 📄 الترخيص

MIT — للاستخدام الشخصي والتعليمي فقط. لا تستخدمه لتعديل ألعاب أونلاين.

---

**تم البناء باحترافية لـ iPhone 13 + Railway ($0) — قراءة فقط، بدون حظر**
