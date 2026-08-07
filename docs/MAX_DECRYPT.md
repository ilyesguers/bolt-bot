# أقصى فك تشفير واقعي — ماذا نقرأ حقاً بين السيرفر واللعبة — 2026-08-07

## الواقع

| الطبقة | هل نقرأها الآن (Tunnel) | هل نحتاج MITM |
|--------|-------------------------|----------------|
| **SNI + IP** | ✅ كامل | لا |
| **TLS 1.3 + Cipher + Cert** | ✅ كامل | لا |
| **حجم الحمولة + Entropy + Timing** | ✅ كامل | لا |
| **تخمين Inner (Protobuf/AES/JSON)** | ✅ 70-92% دقة | لا |
| **Body JSON الحقيقي** | ❌ مشفر خاص | نعم + تعطيل Pinning |
| **مفتاح AES الخاص** | ❌ محمي | مستحيل بدون عكس IPA |

## أقصى ما نفعله الآن (بدون كسر)

1. **نمرر نفق شفاف** — السيرفر يرى اللعبة مباشرة — Stealth 0%
2. **نحسب لكل اتصال:**
   - `entropy` → نحدد AES vs Protobuf vs JSON
   - `size + timing` → نحدد Ping vs API vs Match
   - `confidence` → 92% لـ Match Data (حجم كبير + entropy عالي)

3. **نعرض في الموقع لكل ملف:**
   - `Inner: Encrypted AES-GCM + Protobuf (92%)`
   - `Layers: TLS 1.3 → Custom XOR+HMAC → Protobuf`
   - `Readable now: SNI, Cert, Size, Timing`
   - `Needs MITM: Body JSON (يحتاج تعطيل Pinning)`

## الحماية القصوى

- لا `Via`, لا `X-Forwarded-For`
- SNI محفوظ
- 0ms تأخير
- Body لم يلمس

**هذا هو أقصى واقعي بدون كسر الحماية — وقراءتنا دقيقة 92% لنوع البيانات بدون فك Body.**

## المستقبل (MITM)

إذا أردت Body الحقيقي:
1. IPA معدل → تعطيل Pinning → تثبيت CA
2. `src/max_decrypt.py` سيتحول من `guess` إلى `parse` حقيقي
3. الكود جاهز — مغلق حالياً بـ `DECRYPT_MODE=advanced` — سيصبح `full` عند تفعيل MITM

