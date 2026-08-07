# قاعدة المعلومات النهائية V3 - مشروع دراسة ترافيك eFootball عبر Mitmproxy + Railway
**التوجه النهائي المعتمد:** A - Mitmproxy بشهادته المجانية + موقع Logs يعرض بيانات eFootball فقط
**الهدف:** دراسة وتحليل فقط (Read-Only) - بدون تعديل قيم السيرفر
**البيئة:** iPhone 13 + Railway ($0) + GitHub + شهادة Mitmproxy المجانية + Trust

---

## 1. الفكرة النهائية بدقة (حسب تأكيدك)

> **لا تعديل، فقط دراسة.** نستخدم Mitmproxy كبروكسي تحليلي. شهادته المجانية تثبت على iPhone ويعمل لها Trust. كل ترافيك eFootball يمر عبر Railway ويظهر كـ Logs في موقع ويب خاص بك، يعرض معلومات الشهادة وبيانات الطلبات الخاصة بـ eFootball فقط.

هذا هو **المسار الآمن والقانوني الوحيد** الذي لا يخالف شروط KONAMI إذا بقي Read-Only.

---

## 2. كيف تعمل شهادة Mitmproxy المجانية؟

Mitmproxy لا يحتاج شراء شهادة. هو يولدها محلياً:

```bash
# عند أول تشغيل يولد تلقائياً:
~/.mitmproxy/mitmproxy-ca-cert.pem  # للسيرفر
~/.mitmproxy/mitmproxy-ca-cert.cer  # للآيفون
~/.mitmproxy/mitmproxy-ca-cert.p12  # بديل
```

**خطوات التثبيت على iPhone 13:**
1. شغل Mitmproxy على Railway (أو محلي للاختبار)
2. على iPhone: الإعدادات > Wi-Fi > اضغط ⓘ بجانب شبكتك > تكوين البروكسي > يدوي
   - الخادم: `xxx.up.railway.app` (أو IP Railway)
   - المنفذ: `8080` (أو المنفذ الذي يحدده Railway PORT)
3. افتح Safari وادخل `http://mitm.it` -> حمل `Apple` profile
4. الإعدادات > عام > VPN وإدارة الأجهزة > ثبت ملف mitmproxy
5. **الخطوة الأهم:** الإعدادات > عام > حول > إعدادات الثقة بالشهادات > فعل **Full Trust** لشهادة mitmproxy

بدون الخطوة 5، كل مواقع HTTPS ستفشل.

---

## 3. المعمارية النهائية المقترحة ($0)

```
┌─────────────┐  Wi-Fi Manual Proxy  ┌─────────────────────────┐  HTTPS  ┌──────────────┐
│ iPhone 13   │ ────────────────────>│ Railway - Mitmproxy     │────────>│ KONAMI       │
│ eFootball   │                      │  - mitmproxy addon .py  │         │ Servers      │
│             │ <────────────────────│  - Web Dashboard        │<────────│              │
└─────────────┘   Logs via WSS       └──────────┬──────────────┘         └──────────────┘
                                                │
                                                │ WebSocket / Polling
                                                ▼
                                     ┌──────────────────┐
                                     │ موقع ال Logs     │
                                     │ your-app.up.     │
                                     │ railway.app/logs │
                                     │ - يظهر فقط       │
                                     │   eFootball      │
                                     │ - معلومات الشهادة│
                                     └──────────────────┘
```

**لماذا Railway مناسب هنا؟**
- استخدام شخصي = استهلاك قليل جداً (eFootball يستهلك ~20-50MB/ساعة لعب)
- Railway يعطيك Domain مجاني + HTTPS تلقائي
- الخطة المجانية: 500 ساعة + 100GB - كافية لشخص واحد لشهر كامل
- لا تحتاج IP ثابت - iPhone يتصل بالـ Domain

**مشكلة Railway مع Mitmproxy وحلها:**
Railway يتوقع خدمة HTTP على `PORT`، بينما Mitmproxy هو TCP Proxy. الحل:
- نشغل `mitmweb` (واجهة Mitmproxy الويب) على `PORT` الرسمي + `mitmdump` كبروكسي على منفذ داخلي
- أو نشغل **HTTP Proxy بسيط بـ Python (mitmproxy addon)** يستمع على `PORT` مباشرة ويدعم `CONNECT`
- نستخدم `Cloudflare Tunnel` كبديل إذا لم يعمل المنفذ (مجاني)

---

## 4. موقع ال Logs - ماذا سيعرض بالضبط؟

الموقع سيكون صفحة واحدة بسيطة `https://xxx.up.railway.app` تعرض:

**فلتر تلقائي:** يعرض فقط الدومينات الخاصة بـ eFootball:
```
*.konami.net
*.konami.com
*.pes.net
*.efootball.com
```
أي ترافيك آخر (يوتيوب، واتساب...) يتم تجاهله ولا يحفظ.

**لكل طلب سيعرض:**
- ⏰ الوقت والتاريخ
- 🌐 الدومين والمسار (مثلاً: `api.efootball.konami.net/v1/user`)
- 📜 معلومات الشهادة: Issuer, Valid From/To, Fingerprint
- 📦 Method + Status Code + حجم البيانات
- ⏱️ زمن الاستجابة
- 🔒 هل تم فك التشفير بنجاح أم لا (بسبب Pinning)

**ما لن يعرضه (حتى لا نكسر Pinning):**
- body المشفر إذا كان التطبيق يستخدم Pinning - سيظهر كـ `Encrypted / Pinned - Metadata Only`
- هذا يحافظ على كون المشروع Read-Only وآمن

**التقنية:** Python + FastAPI + WebSocket للتحديث اللحظي + صفحة HTML بسيطة (لا تحتاج قاعدة بيانات - Logs في الذاكرة وآخر 500 طلب فقط)

---

## 5. لماذا دراسة فقط بدون فك Pinning؟

eFootball يستخدم **Certificate Pinning**. هذا يعني:
- حتى مع تثبيت شهادة mitmproxy وعمل Trust، التطبيق سيرفضها لأنه يقارنها بشهادة KONAMI المضمنة داخل الكود
- النتيجة: الطلبات ستظهر في Mitmproxy لكن كـ `502 Bad Gateway` أو `TLS Handshake Failed`

**الحلول النظرية (لن نطبقها لأنها تعديل):**
- تعديل IPA لتعطيل Pinning = يعتبر Mod ويحتاج إعادة توقيع + يخالف ToS

**لذلك في V3 سنبقى على:**
- تسجيل **Metadata فقط** (الدومين، الوقت، حجم البيانات، معلومات الشهادة) بدون محاولة فك Body المشفر
- هذا كافٍ لدراسة: متى تتصل اللعبة، كم مرة، ما هي الدومينات، هل الشهادة صالحة، قياس التأخير
- إذا أردت لاحقاً دراسة Body، ستحتاج بيئة اختبار منفصلة وليس حسابك الأساسي

---

## 6. هيكل المستودع الجديد المقترح

بعد المسح، سيكون هكذا:

```
/README.md
/railway.json          # إعدادات النشر على Railway
/requirements.txt      # mitmproxy + fastapi + uvicorn
/Dockerfile            # لتشغيل mitmproxy على Railway
/src
  ├── addon.py         # فلتر eFootball + إرسال Logs
  ├── web.py           # FastAPI - موقع عرض ال Logs
  └── templates/
      └── logs.html    # صفحة ال Logs اللحظية
/docs
  ├── KNOWLEDGE_BASE_V3_mitmproxy_railway.md (هذا الملف)
  └── SETUP_iPhone13.md # دليل تثبيت الشهادة خطوة بخطوة
/.gitignore
```

**التكلفة:** كل الملفات مجانية ومفتوحة المصدر

---

## 7. خطوات التنفيذ - 3 مراحل

**المرحلة 1 - POC محلي (بدون Railway):**
- تشغيل mitmproxy على كمبيوتر محلي + توصيل iPhone بنفس Wi-Fi + اختبار mitm.it

**المرحلة 2 - النشر على Railway:**
- رفع الكود إلى GitHub -> ربط Railway -> نشر تلقائي -> اختبار Proxy عبر Domain

**المرحلة 3 - الفلترة والعرض:**
- تفعيل فلتر eFootball فقط + صفحة Logs + معلومات الشهادة

---

## 8. ما نحتاجه منك الآن

1. **هل توافق على أن يكون الموقع يعرض Metadata فقط (بدون فك Body المشفر) في البداية؟**
2. **هل تريد أن أمسح المستودع الحالي بالكامل الآن وأبدأ الهيكل الجديد؟**

قل: `نفذ المسح وابدأ الهيكل V3` وسأبدأ فوراً. لن أفتح PR حتى تأمر.
