# دليل التشغيل الكامل — كل المتغيرات والمنافذ والخطوات

> **هذا الملف يوضح كل شيء لازم تعمله عشان يشتغل المشروع 100% — من الصفر حتى قراءة بيانات السيرفر**

---

## 1. المتطلبات الأساسية ($0)

| المتطلب | التفصيل | التكلفة |
|---------|---------|---------|
| **GitHub** | مستودع Private مربوط بـ Railway | $0 |
| **Railway** | حساب مجاني (500 ساعة + 100GB) | $0 |
| **iPhone 13** | iOS 16-18 + اتصال Wi-Fi | موجود |
| **Domain** | `xxx.up.railway.app` يولد تلقائياً | $0 |
| **شهادة** | لا تحتاج — نفق شفاف | $0 |

---

## 2. كل المتغيرات (Environment Variables)

### 2.1 متغيرات Railway (تضبط تلقائياً)

| المتغير | من يضبطه | القيمة | الشرح |
|---------|----------|--------|-------|
| `PORT` | **Railway تلقائياً** | `8080` أو عشوائي | المنفذ الخارجي الوحيد — **لا تغيره يدوياً** — الكود يقرأه من `os.environ["PORT"]` |
| `RAILWAY_ENVIRONMENT` | Railway | `production` | بيئة التشغيل |
| `RAILWAY_PUBLIC_DOMAIN` | Railway | `xxx.up.railway.app` | الدومين العام — تستخدمه في iPhone |

### 2.2 متغيرات التحكم (تقدر تغيرها)

| المتغير | افتراضي | أين تغيره | التأثير |
|---------|---------|-----------|---------|
| `LOG_LIMIT` | `500` | Railway → Variables | عدد السجلات المحفوظة في الذاكرة (الأحدث أولاً) — زيادته تستهلك RAM |
| `EFOOTBALL_ONLY` | `true` | Railway → Variables | `true` = يعرض فقط `*.konami.net` / `false` = يعرض كل الترافيك (لا ينصح) |
| `PYTHONUNBUFFERED` | `1` | Dockerfile | لعرض Logs فورياً |

### 2.3 ملف `.env.example` (للتشغيل المحلي)

```env
PORT=8080
LOG_LIMIT=500
EFOOTBALL_ONLY=true
```

> **انسخه لـ `.env` محلياً فقط — لا ترفعه لـ GitHub — Railway يقرأ من Variables وليس من الملف**

---

## 3. المنافذ (Ports) — شرح دقيق

| المنفذ | أين | الوظيفة |
|--------|-----|---------|
| `PORT` (خارجي) | `0.0.0.0:$PORT` على Railway | **المنفذ الوحيد المفتوح للعالم** — يستقبل نوعين: `CONNECT` (بروكسي) + `GET /` (موقع) — الكود يميز تلقائياً |
| `8001` (داخلي) | `127.0.0.1:8001` داخل الحاوية فقط | FastAPI الداخلي — لا يظهر للعالم — Hybrid يمرر له طلبات الويب |
| `443` | iPhone → Railway | المنفذ الذي تكتبه في iPhone — Railway يحوله داخلياً لـ `$PORT` عبر TLS |

**مثال:**
- Railway يعطيك `PORT=8080` داخلياً لكن الدومين `https://xxx.up.railway.app` يفتح على `443`
- في iPhone تكتب: Host=`xxx.up.railway.app` Port=`443` (أو `8080` إذا طلب Railway)

---

## 4. خطوات التشغيل — من الصفر

### A. النشر على Railway (3 دقائق)

```bash
# 1. تأكد أن الكود مرفوع
git push origin arena/019fdca0-bolt-bot

# 2. في Railway:
# New Project → Deploy from GitHub → اختر ilyesguers/bolt-bot → فرع arena/019fdca0-bolt-bot
# Railway سيكتشف Dockerfile + railway.json تلقائياً

# 3. بعد النشر → Settings → Generate Domain → انسخ xxx.up.railway.app

# 4. (اختياري) Variables → أضف:
# LOG_LIMIT=500
# EFOOTBALL_ONLY=true
```

### B. تشغيل محلي (للاختبار قبل Railway)

```bash
git clone https://github.com/ilyesguers/bolt-bot.git
cd bolt-bot
git checkout arena/019fdca0-bolt-bot

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt

# شغل
python -m src.main
# أو
uvicorn src.web:app --port 8080  # للويب فقط

# افتح
# http://localhost:8080/ → لوحة التحكم
# http://localhost:8080/health → فحص
# http://localhost:8080/api/logs → JSON
```

### C. إعداد iPhone 13 (دقيقة واحدة)

```
الإعدادات → Wi-Fi → ⓘ بجانب شبكتك → تكوين البروكسي → يدوي
الخادم: xxx.up.railway.app
المنفذ: 443
حفظ
```

> **لا تحتاج تثبيت شهادة** — النفق شفاف

**للإيقاف:** نفس المسار → إيقاف

---

## 5. قراءة بيانات ومحدثات السيرفر — التركيز الحالي

هذا هو **جوهر المشروع** — كيف نقرأ بيانات اللعبة والسيرفر بدقة عالية:

### 5.1 ماذا نقرأ الآن (READ-ONLY)

| البيانات | كيف نقرأها | أين تظهر |
|----------|------------|----------|
| **الدومين والمسار** | `CONNECT api.efootball.konami.net:443` | موقع Logs → Host |
| **معلومات الشهادة** | `ssl.getpeercert()` مباشرة من سيرفر KONAMI | Cert Info → Issuer/Valid |
| **زمن الاستجابة** | `duration_ms` بين CONNECT و 200 OK | Logs → ⏱️ |
| **حجم البيانات** | عد البايتات المارة | Logs → bytes |
| **وقت الاتصال** | `time.time()` | Logs → Time |
| **عدد الاتصالات** | عداد في `logger.py` | Stats → Total/eFootball |

### 5.2 كيف تكتشف محدثات السيرفر

افتح eFootball واعمل:

1. **تسجيل دخول** → سترى اتصال لـ `auth.konami.net` أو `login`
2. **فتح المتجر** → اتصال لـ `shop` أو `store`
3. **بدء مباراة** → اتصال `match` أو `game` مع `duration_ms` أطول
4. **نهاية مباراة** → اتصال `result` أو `reward`

**كل هذه تظهر لحظياً في `https://xxx.up.railway.app/` مع تحديث كل 3 ثواني**

### 5.3 API للقراءة البرمجية

```bash
# كل Logs
curl https://xxx.up.railway.app/api/logs?limit=50

# الإحصائيات
curl https://xxx.up.railway.app/api/stats

# الإعدادات
curl https://xxx.up.railway.app/api/config

# فحص الصحة
curl https://xxx.up.railway.app/health
```

**مثال رد:**
```json
{
  "host": "api.efootball.konami.net",
  "port": 443,
  "status": "TUNNEL OK",
  "duration_ms": 120,
  "cert_info": {
    "issuer": "DigiCert Inc",
    "subject": "api.efootball.konami.net",
    "notBefore": "Jan 1 00:00:00 2026 GMT",
    "notAfter": "Jan 1 00:00:00 2027 GMT"
  }
}
```

### 5.4 مستقبلاً: التعديل (Mod Menu)

> **حالياً: قراءة فقط — آمن 100%**
> 
> مستقبلاً إذا أردت التعديل، ستحتاج:
> - IPA معدل (حقن Dylib) + إعادة توقيع بشهادة مجانية
> - تعطيل Pinning داخل الكود
> - `addon.py` سيتحول من `TUNNEL` إلى `MITM` لفك Body
>
> **تحذير:** أي تعديل يؤثر على نتيجة مباراة أونلاين سيكتشف عبر Server Reconciliation لدى KONAMI — لذلك سنبدأ بميزات **بصرية فقط** (أطقم/ملعب) عند تلك المرحلة.

الكود الحالي مهيأ: `proxy.py` فيه مكان `cert_info` و `status` جاهز ليتحول لـ MITM لاحقاً بدون تغيير الهيكل.

---

## 6. فحص أن كل شيء يعمل

| الفحص | الأمر | النتيجة المتوقعة |
|-------|-------|-----------------|
| Web يعمل | `curl https://xxx.up.railway.app/health` | `{"status":"ok"}` |
| Proxy يعمل | `curl -x xxx.up.railway.app:443 http://example.com -I` | `HTTP/1.1 200` |
| فلتر يعمل | `curl -x ... http://google.com` → افحص `/api/logs` | لا يظهر (مفلتر) |
| eFootball يظهر | افتح اللعبة → `/api/logs` | يظهر `konami.net` |

---

## 7. ملفات المشروع ومسؤولية كل واحد

| الملف | المسؤولية |
|-------|-----------|
| `src/main.py` | Hybrid Server — يدمج Proxy + Web على نفس PORT |
| `src/proxy.py` | نفق CONNECT شفاف + جلب cert_info |
| `src/web.py` | FastAPI Dashboard + API |
| `src/config.py` | `EFOOTBALL_DOMAINS` + `is_efootball_host()` |
| `src/logger.py` | تخزين 500 سجل في الذاكرة |
| `Dockerfile` | بناء Railway |
| `railway.json` | إعدادات النشر |
| `requirements.txt` | fastapi + uvicorn |

---

## 8. ماذا تفعل إذا لم يعمل؟

| المشكلة | الحل |
|---------|------|
| Railway نائم (502) | افتح الموقع مرة — ينهض خلال 5 ثواني (Free tier) |
| iPhone لا يتصفح | تأكد من كتابة Domain بدون `https://` — فقط `xxx.up.railway.app` |
| لا يظهر ترافيك | تأكد أن `EFOOTBALL_ONLY=true` وأن اللعبة مفتوحة فعلاً |
| تريد كل الترافيك | غير `EFOOTBALL_ONLY=false` في Railway Variables → Redeploy |

---

**كل شيء مذكور هنا — انسخ المتغيرات كما هي وسيعمل فوراً. التركيز الحالي: قراءة بيانات ومحدثات السيرفر بدقة — والتعديل مرحلة قادمة منفصلة.**
