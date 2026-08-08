# ⚡ eFootball Traffic Analyzer — v5.4

<div align="center">

![Version](https://img.shields.io/badge/version-5.4.0-00E676?style=for-the-badge)
![Build](https://img.shields.io/badge/build-passing-2962FF?style=for-the-badge)
![Platform](https://img.shields.io/badge/platform-Railway%20%7C%20iPhone%2013-0A1433?style=for-the-badge)
![Date](https://img.shields.io/badge/date-2026--08--08-FFCA28?style=for-the-badge)

**Proxy passthrough + Dashboard + AI-host traffic metadata + Feature Engine (target/timing) + Live Match Phase + Real Notifications + Proxy-Only Network Controls**

</div>

---

## ما الجديد في v5.4 — تحكم شبكي عبر البروكسي فقط

- **🎛️ لوحة "تحكم الشبكة"**: تعمل دون أي تعديل على جهازك (لا IPA، لا مود مينو):
  - 🔌 **قطع كل الاتصالات** النشطة مع اللعبة فوراً (`POST /api/netctl/kill`)
  - 🐌 **تحديد سرعة المرور** (حد أقصى KB/s لكل اتصال)
  - 🛡️ **قائمة حجب النطاقات** (مطابقة لاحقة — مثلاً `konami.net`)
  - 🛑 **منع رفع النتيجة** (تجريبي): يُسقط اتصالات خادم AI بعد نهاية المباراة
- **سجل إجراءات الشبكة** + Toast فوري لكل إجراء (لا إجراءات صامتة).
- **الصدق الكامل في الواجهة**: كل تحكم مكتوب مع أثره الحقيقي — لا شيء يدّعي
  أنه يغيّر ذكاء AI أو النتيجة، لأن ذلك مستحيل عبر بروكسي (الآفلان محسوب على
  جهازك، والأونلاين مشفر ومتحقق منه السيرفر). التفاصيل: `docs/NETWORK_CONTROLS.md`.
- الإعدادات محفوظة في `data/netctl.json`.

## ما الجديد في v5.3 (مسار اختياري — يتطلب IPA معدل)

- 🛠️ مود مينو Client-Side (إنهاء فوراً/فوز تلقائي...) + كشف نمط المباراة
  (آفلان/أونلاين) + قالب dylib. **غير متاح إذا كنت تستخدم بروكسي فقط** —
  راجع `docs/OFFLINE_MOD_MENU.md`.

- **فهم الوضع الصحيح للمباريات الآفلانية (ضد AI)**: المباراة ضد الكمبيوتر تُلعب بالكامل على جهازك — لا يمر شيء منها عبر البروكسي. لهذا الميزات "الأسطورية" (إنهاء فوراً، فوز تلقائي...) تنفذ **داخل التطبيق المعدّل (Client-Side)** وليس عبر البروكسي.
- **🛠️ لوحة تحكم مود مينو** (`src/modmenu.py`): 6 مفاتيح Client-Side (إنهاء المباراة فوراً، فوز تلقائي، إبطاء AI محلي، AI يخطئ، ستامينا، قيم 99) تُحفظ في `data/modmenu.json`، والتطبيق المعدّل يقرأها من `GET /api/modmenu/config`.
- **🧭 كشف نمط المباراة** (تقدير من شكل الترافيك): `آفلان ضد AI` (حركة قليلة/مزامنة) مقابل `أونلاين` (حركة كثيفة) — يظهر في شريط المباراة + إشعار عند كل تصنيف.
- **قالب dylib جاهز** في `modmenu/ios_dylib/ModMenu.m` يقرأ الإعدادات ويطبّقها محلياً، مع وثيقة `docs/OFFLINE_MOD_MENU.md` كاملة (البروتوكول + البناء + المخاطر).
- **إشعارات فورية**: عند حفظ المود مينو أو تغيّر نمط المباراة تصلك Toast مباشرة.

## ما الجديد في v5.2

- **إشعارات حقيقية تصل فعلاً**: `WS /ws/live` أصبح يدفع الإشعارات + حالة المباراة كل ثانيتين، واللوحة تعرض Toast منبثقة لأي إشعار جديد — لن تفوتك أي معلومة بعد الآن.
- **تقرير ميزات لكل اتصال AI**: عند كل اتصال بخادم AI يظهر إشعار ملخص (نشطة/بانتظار التوقيت/محجوبة) + جدول "حالة كل ميزة" يشرح سبب التطبيق أو الحجب (TLS مشفر / الخصم خارج جهازك / التوقيت).
- **`src/match_tracker.py`**: متتبع أطوار المباراة تقديرياً من شكل الترافيك (بداية → شوط أول → استراحة → شوط ثاني → نهاية) مع أحداث في الخط الزمني وإشعارات عند كل انتقال.
- **هدف وتوقيت لكل ميزة**: `عليك / على الخصم / كلاهما` و`فوراً / بدري / متأخر` — يُحفظان في `data/features.json` ويقودان نافذة تفعيل الميزة فعلياً.
- **4 ميزات رصد جديدة تعمل داخل CONNECT** (بدون لمس البايتات): تنبيه بداية المباراة ⚽، تنبيه نهاية المباراة 🏁، متابعة المباراة الحية 📡، قياس بينغ الخادم 📶.
- `GET /api/match`: طور المباراة الحالي + الخط الزمني + حالة الميزات.

## حدود تقنية مهمة (اقرأها قبل أن تطلب "ميزات أسطورية")

اتصال HTTPS عبر `CONNECT` هو **نفق TLS مشفّر**. البروكسي يستطيع رؤية المضيف، الحجم، التوقيت وشكل ciphertext، لكنه **لا يرى حقول اللعب أو قرار AI**، و**لا يستطيع تعديلها بأمان**:

- في TLS 1.3، تعديل أي بايت في ciphertext يفشل تحقق AEAD ويقطع الاتصال فوراً → المباراة تنتهي بفصل، لا بفوز.
- **لا يمكن تعديل أي شيء على جهاز الخصم من بروكسيك**: الخصم له اتصال مستقل بسيرفر KONAMI، والسيرفر هو المرجع النهائي لكل القيم (Server-Side Verified). أي "ميزة على الخصم" من جهازك مستحيلة فيزيائياً — هذا ليس عيب برمجي.
- لذلك ميزات **التعديل** (إبطاء AI، ستامينا، تسديد يخطئ، AI لا يضغط) تُحفظ وتُحلل وتُطبَّق على عينات مفكوكة/Offline فقط، وتظهر حالتها الحقيقية (`محجوبة — TLS مشفر`) في لوحة "حالة كل ميزة".
- **المباريات الآفلانية (ضد AI)** تُلعب على جهازك بالكامل — لا تمر عبر البروكسي إطلاقاً. تعديلها ممكن لكن **Client-Side** فقط (لعبة معدّلة تقرأ لوحة المود مينو من `/api/modmenu/config`)؛ البروكسي نفسه لا يلمسها. راجع `docs/OFFLINE_MOD_MENU.md`.
- ميزات **الرصد** (تنبيه البداية/النهاية، متابعة المباراة، البينغ، نمط المباراة) تعمل فعلاً على الميتاداتا (أحجام، توقيت، فجوات) وتوصّل إشعارات حقيقية.
- "أطوار المباراة" و"نمط المباراة" **تقدير** مبني على شكل الترافيك، وليس قراءة لبروتوكول KONAMI الداخلي.
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
| `GET /api/features` | تعريفات الميزات + الحالة + الأهداف + التوقيتات + أطوار المباراة |
| `POST /api/features` | حفظ `{"features":{...},"targets":{...},"timings":{...}}` |
| `GET /api/notifications` | آخر عشرة إشعارات AI |
| `GET /api/match` | طور المباراة التقديري + نمطه + الخط الزمني + حالة الميزات |
| `GET /api/modmenu` | تعريفات المود مينو وحالته |
| `POST /api/modmenu` | حفظ مفاتيح المود مينو (`{"features":{...}}`) |
| `GET /api/modmenu/config` | صيغة خفيفة للتطبيق المعدّل (dylib) |
| `GET /api/netctl` | إعدادات التحكم الشبكي + الجلسات + سجل الإجراءات |
| `POST /api/netctl` | حفظ إعدادات التحكم الشبكي |
| `POST /api/netctl/kill` | قطع كل الاتصالات النشطة |
| `WS /ws/live` | تحديثات مباشرة (إحصائيات + سجلات + إشعارات + طور/نمط المباراة) |
| `GET /api/export/csv` | تصدير CSV |

مثال:

```bash
curl -X POST http://localhost:8080/api/features \
  -H 'content-type: application/json' \
  -d '{"features":{"slow_ai":true,"match_end_alert":true},"targets":{"slow_ai":"me"},"timings":{"slow_ai":"late","match_end_alert":"late"}}'
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
  match_tracker.py    Match phase/mode estimator (heuristic) + timing gate
  features.py         Preferences, targets/timings, per-feature status + notifications
  modmenu.py          Client-side mod menu config for offline AI matches (optional IPA path)
  netctl.py           Proxy-only network controls: kill / throttle / block / result-guard
  web.py              FastAPI + feature/modmenu/netctl APIs
  templates/index.html
modmenu/ios_dylib/    ObjC template client (dylib) for the modified game (optional)
```
