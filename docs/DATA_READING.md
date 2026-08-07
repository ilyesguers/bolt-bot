# قراءة بيانات ومحدثات السيرفر — دليل تقني مفصل

> **الهدف الحالي: قراءة فقط بدقة عالية — بدون تعديل — لتجنب الحظر**

---

## 1. ماذا نقرأ بالضبط؟

### اتصال واحد = سجل واحد

كل مرة eFootball تكلم السيرفر، نمررها شفافاً ونسجل:

```
iPhone 13 → CONNECT api.efootball.konami.net:443 → Railway → KONAMI
           ← 200 Connection Established ←
           ← نفق شفاف (بايتات كما هي) →
```

**ما نسجله:**

| الحقل | المصدر | مثال |
|-------|--------|------|
| `host` | من CONNECT | `api.efootball.konami.net` |
| `port` | من CONNECT | `443` |
| `method` | أول سطر | `CONNECT` |
| `duration_ms` | فرق وقت | `120ms` |
| `cert_info.issuer` | `ssl.getpeercert()` | `DigiCert Inc` |
| `cert_info.notAfter` | الشهادة | `2027-01-01` |
| `status` | نتيجة النفق | `TUNNEL OK` أو `FAILED` |

---

## 2. كيف نميز محدثات السيرفر؟

### خارطة دومينات eFootball (من config.py)

```python
EFOOTBALL_DOMAINS = [
  "konami.net",
  "konami.com",
  "pes.net",
  "efootball.com"
]
```

أي Host يحتوي `konami` أو `pes` أو `efootball` → يعتبر eFootball → يُسجل

### سيناريوهات القراءة

| فعل في اللعبة | الدومين المتوقع | ماذا يظهر |
|---------------|-----------------|-----------|
| فتح اللعبة | `auth.konami.net` | `CONNECT auth... 80ms` + شهادة |
| قائمة الفريق | `api.efootball.konami.net` | `TUNNEL OK 120ms` |
| متجر | `shop.konami.net` | `TUNNEL OK` |
| بدء مباراة | `match.efootball.konami.net` | `duration_ms` طويل (300ms+) |
| نتيجة | `result.konami.net` | اتصال قصير بعد المباراة |

**جرب بنفسك:** افتح اللعبة وادخل كل قسم وراقب `https://xxx.up.railway.app` — ستفهم الخريطة خلال دقائق

---

## 3. API القراءة — للتحليل المستقبلي

### جلب 50 سجل
```bash
curl https://xxx.up.railway.app/api/logs?limit=50 | jq
```

### فلترة يدوية
```bash
# فقط auth
curl -s https://xxx.up.railway.app/api/logs | jq '.logs[] | select(.host | contains("auth"))'

# فقط فشل
curl -s https://xxx.up.railway.app/api/logs | jq '.logs[] | select(.status | contains("FAILED"))'
```

### حفظ لملف
```bash
curl -s https://xxx.up.railway.app/api/logs?limit=500 > efootball_$(date +%F).json
```

---

## 4. الاستعداد للتعديل المستقبلي

الكود الحالي مهيأ — `proxy.py` فيه:

```python
# حالياً: Tunnel شفاف
writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
await relay(reader, remote_writer)

# مستقبلاً (MITM):
# 1. فك TLS بـ mitmproxy-ca
# 2. قراءة Body (protobuf/json)
# 3. تعديل ثم إعادة تشفير
# 4. إرسال
```

لكن **لن نفعل 2-4 الآن** لأن:
- يتطلب شهادة Mitmproxy + Trust + تعطيل Pinning في IPA
- أي تعديل يؤثر على مباراة أونلاين = كشف فوري

**المرحلة القادمة المقترحة:** عندما تقرر، سنبدأ بـ **تعديلات بصرية فقط** (لا تؤثر على السيرفر) مثل تغيير أطقم — آمنة ولا تكتشف

---

## 5. أين تجد البيانات الآن؟

- **موقع:** `https://xxx.up.railway.app/` → تحديث كل 3 ثواني
- **JSON:** `https://xxx.up.railway.app/api/logs`
- **Railway Logs:** Railway → Deployments → View Logs → ترى `TUNNEL OK` مباشرة

---

**ابدأ بالقراءة — اجمع 100 سجل — ستعرف كل محدثات السيرفر قبل أن نبدأ أي تعديل**
