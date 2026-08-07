# فك التشفير الخاص لـ eFootball + الحماية — 2026-08-07

> **اللعبة تستخدم تشفير خاص فوق TLS — هذا الدليل يوضح كيف نكتشف ما يدور بدون كسر الحماية**

---

## 1. طبقات التشفير في eFootball

```
[ بيانات اللعبة الحقيقية ]
    ↓ Protobuf + JSON + ضغط
[ طبقة التشفير الخاصة ] ← AES-GCM / XOR مخصص + HMAC
    ↓
[ TLS 1.3 ] ← تشفير النقل (SNI, Cipher)
    ↓
[ TCP ] ← نحن نراه هنا (CONNECT Tunnel)
```

**ما نراه في البروكسي الشفاف (بدون MITM):**
- ✅ TLS outer (SNI, Cipher, Cert) — نراه كاملاً
- ✅ حجم الحمولة المشفرة + Entropy + Timing
- ❌ Body الداخلي المشفر الخاص — لا نراه بدون كسر Pinning

**لذلك نستخدم تحليل غير مباشر (Inference) — نكتشف النوع بدون فك:**

---

## 2. كيف نكتشف التشفير الخاص؟

### حساب Entropy (العشوائية)
- `entropy < 4` → نص عادي (JSON)
- `4 < entropy < 7` → مضغوط أو Protobuf
- `entropy > 7.5` → مشفر قوي (AES)

### حجم الحمولة
- ` < 200 bytes` → Heartbeat / Ping
- `200 - 2000` → API call (auth, shop)
- `> 5000` → بيانات مباراة / تحميل أصول

### Timing
- ` < 50ms` → Cache
- `50-150ms` → API عادي
- `> 300ms` → عملية سيرفر ثقيلة (match result)

---

## 3. الحماية — كيف لا يكتشفنا السيرفر كبروكسي؟

| الحماية | كيف |
|---------|-----|
| **No Headers** | لا نضيف `Via`, `X-Forwarded-For`, `Proxy-Connection` — نمرر كما هو |
| **SNI Preserve** | نحافظ على SNI الأصلي `api.efootball.konami.net` بدون تغيير |
| **Timing Jitter** | لا نؤخر — نمرر فوراً (0ms extra) — أي تأخير يكشفنا |
| **TLS Passthrough** | لا نفك outer TLS — نمرر نفق شفاف — السيرفر يرى TLS الخاص باللعبة مباشرة |
| **No Body Touch** | لا نلمس Body الداخلي — حتى لو مشفر، نمرره كما هو |

**هذا يجعلنا غير قابلين للكشف كـ Proxy — نحن مجرد نفق شفاف.**

---

## 4. ماذا نعرض في اللوحة بعد التحديث؟

لكل اتصال:
- **Outer:** TLS 1.3 / Cipher / Cert / SNI
- **Inner Guess:** `Protobuf` / `JSON` / `Encrypted` (حسب الحجم + Entropy)
- **Protection:** `Stealth: ON` — لا أثر

---

**التحديث القادم: إذا أردت رؤية Body الداخلي الحقيقي، سنحتاج MITM + تعطيل Pinning في IPA — وهذا يكشفنا وسنناقشه منفصلاً.**
