"""
BOLT ⚡ — Internationalization
🌍 Arabic / English / Vietnamese / Hindi
"""

from __future__ import annotations
import database as D

LANGS = {
    "ar": "🇸🇦 العربية",
    "en": "🇬🇧 English",
    "vi": "🇻🇳 Tiếng Việt",
    "hi": "🇮🇳 हिन्दी",
}

_S: dict[str, dict[str, str]] = {

    # ═══ LANGUAGE SELECTION ═════════════════════════════════════════════════

    "welcome_select_lang": {
        "ar": "<b>⚡ مرحباً بك في BOLT!</b>\n\n️ بوت <b>مجاني 100%</b>\n🔐 توكنك مشفر بأمان\n🏆 أدوات احترافية\n\n🌍 <b>اختر لغتك المفضلة:</b>",
        "en": "<b>⚡ Welcome to BOLT!</b>\n\n🛡️ <b>100% free</b>\n Token encrypted\n🏆 Pro tools\n\n🌍 <b>Choose language:</b>",
        "vi": "<b>⚡ Chào mừng đến BOLT!</b>\n\n🛡️ <b>100% miễn phí</b>\n🔐 Token mã hóa\n\n🌍 <b>Chọn ngôn ngữ:</b>",
        "hi": "<b>⚡ BOLT में स्वागत!</b>\n\n🛡️ <b>100% मुफ़्त</b>\n🔐 Token एन्क्रिप्टेड\n\n🌍 <b>भाषा चुनें:</b>",
    },
    "lang_selected": {
        "ar": "✅ <b>تم اختيار اللغة!</b>\n\n📱 اختر نوع جهازك:",
        "en": "✅ <b>Language selected!</b>\n\n📱 Choose device:",
        "vi": "✅ <b>Đã chọn ngôn ngữ!</b>\n\n📱 Chọn thiết bị:",
        "hi": "✅ <b>भाषा चुनी गई!</b>\n\n📱 डिवाइस चुनें:",
    },

    # ═══ TUTORIAL ════════════════════════════════════════════════════════════

    "tutorial_title": {
        "ar": "<b>📱 كيف تحصل على التوكن؟</b>",
        "en": "<b>📱 How to get the token?</b>",
        "vi": "<b> Cách lấy token?</b>",
        "hi": "<b>📱 Token कैसे प्राप्त करें?</b>",
    },

    "tutorial_android_steps": {
        "ar": (
            "━━━━━━━━━━━━━━━━━━━\n"
            "<b>🤖 خطوات أندرويد:</b>\n\n"
            "<b>1️⃣ افتح Chrome واذهب إلى:</b>\n"
            "<code>discstore.recargajogo.com.br</code>\n\n"
            "<b>2️⃣ سجّل دخول</b>\n"
            "اضغط Google واختر حسابك\n\n"
            "<b>3️⃣ ستظهر صفحة خطأ زرقاء</b>\n"
            "مكتوب فيها <b>setting_error</b>\n"
            "⚠️ <b>لا تغلقها!</b>\n\n"
            "<b>4️⃣ افتح السجل</b>\n"
            "اضغط ⋮ (النقاط الثلاث)\n"
            "اختر <b>السجل</b>\n\n"
            "<b>5️⃣ انسخ الرابط الأول</b>\n"
            "اسمه <b>Discount Store</b>\n"
            "اضغط مطولاً → <b>نسخ الرابط</b>\n\n"
            "<b>6️⃣ أرسله هنا مباشرة!</b>\n"
            "🤖 البوت سيستخرج التوكن تلقائياً\n"
            "لا تحتاج لنسخ التوكن يدوياً\n\n"
            "⚠️ <b>الفيديو غير متوفر حالياً</b>\n"
            "سنضيفه قريباً. اتبع الخطوات أعلاه"
        ),
        "en": (
            "━━━━━━━━━━━━━━━━━━━\n"
            "<b>🤖 Android Steps:</b>\n\n"
            "<b>1️⃣ Open Chrome and go to:</b>\n"
            "<code>discstore.recargajogo.com.br</code>\n\n"
            "<b>2️ Login</b>\n"
            "Tap Google and choose your account\n\n"
            "<b>3️⃣ Blue error page appears</b>\n"
            "It says <b>setting_error</b>\n"
            "⚠️ <b>Don't close it!</b>\n\n"
            "<b>4️⃣ Open History</b>\n"
            "Tap  (three dots)\n"
            "Select <b>History</b>\n\n"
            "<b>5️⃣ Copy the first link</b>\n"
            "Named <b>Discount Store</b>\n"
            "Long press → <b>Copy link</b>\n\n"
            "<b>6️⃣ Send it here directly!</b>\n"
            "🤖 Bot will extract token automatically\n"
            "No need to copy token manually\n\n"
            "️ <b>Video not available yet</b>\n"
            "We'll add it soon. Follow steps above"
        ),
        "vi": (
            "━━━━━━━━━━━━━━━━━━━\n"
            "<b>🤖 Các bước Android:</b>\n\n"
            "<b>1️ Mở Chrome và truy cập:</b>\n"
            "<code>discstore.recargajogo.com.br</code>\n\n"
            "<b>2️⃣ Đăng nhập</b>\n"
            "Nhấn Google và chọn tài khoản\n\n"
            "<b>3️⃣ Trang lỗi xanh hiện ra</b>\n"
            "Ghi <b>setting_error</b>\n"
            "⚠️ <b>Đừng đóng!</b>\n\n"
            "<b>4️⃣ Mở Lịch sử</b>\n"
            "Nhấn ⋮ (ba chấm)\n"
            "Chọn <b>Lịch sử</b>\n\n"
            "<b>5️⃣ Sao chép link đầu tiên</b>\n"
            "Tên <b>Discount Store</b>\n"
            "Nhấn giữ → <b>Sao chép link</b>\n\n"
            "<b>6️⃣ Gửi vào đây trực tiếp!</b>\n"
            " Bot sẽ tự động lấy token\n"
            "Không cần copy thủ công\n\n"
            "️ <b>Video chưa có sẵn</b>\n"
            "Sẽ thêm sớm. Làm theo các bước trên"
        ),
        "hi": (
            "━━━━━━━━━━━━━━━━━━━\n"
            "<b>🤖 Android कदम:</b>\n\n"
            "<b>1️⃣ Chrome खोलें और जाएं:</b>\n"
            "<code>discstore.recargajogo.com.br</code>\n\n"
            "<b>2️⃣ लॉगिन करें</b>\n"
            "Google दबाएं और अकाउंट चुनें\n\n"
            "<b>3️⃣ नीली एरर पेज दिखेगी</b>\n"
            "लिखा <b>setting_error</b>\n"
            "️ <b>बंद न करें!</b>\n\n"
            "<b>4️ हिस्ट्री खोलें</b>\n"
            "⋮ (तीन बिंदु) दबाएं\n"
            "<b>हिस्ट्री</b> चुनें\n\n"
            "<b>5️⃣ पहला लिंक कॉपी करें</b>\n"
            "नाम <b>Discount Store</b>\n"
            "लंबा दबाएं → <b>लिंक कॉपी</b>\n\n"
            "<b>6️⃣ यहाँ सीधे भेजें!</b>\n"
            "🤖 बॉट खुद token निकाल लेगा\n"
            "मैन्युअल कॉपी की ज़रूरत नहीं\n\n"
            "⚠️ <b>वीडियो अभी उपलब्ध नहीं</b>\n"
            "जल्द आएगा। ऊपर के कदम फॉलो करें"
        ),
    },

    "tutorial_ios_steps": {
        "ar": (
            "━━━━━━━━━━━━━━━━━━━\n"
            "<b>🍎 خطوات آيفون:</b>\n\n"
            "<b>1️ افتح Safari واذهب إلى:</b>\n"
            "<code>discstore.recargajogo.com.br</code>\n\n"
            "<b>2️⃣ سجّل دخول</b>\n"
            "اضغط Google واختر حسابك\n\n"
            "<b>3️⃣ ستظهر صفحة خطأ زرقاء</b>\n"
            "مكتوب فيها <b>setting_error</b>\n"
            "️ <b>لا تغلقها!</b>\n\n"
            "<b>4️ افتح السجل</b>\n"
            "اضغط 📖 (أيقونة الكتاب)\n"
            "اختر <b>السجل</b>\n\n"
            "<b>5️⃣ انسخ الرابط الأول</b>\n"
            "اسمه <b>Discount Store</b>\n"
            "اضغط مطولاً → <b>نسخ</b>\n\n"
            "<b>6️⃣ أرسله هنا مباشرة!</b>\n"
            " البوت سيستخرج التوكن تلقائياً\n"
            "لا تحتاج لنسخ التوكن يدوياً\n\n"
            "️ <b>الفيديو غير متوفر حالياً</b>\n"
            "سنضيفه قريباً. اتبع الخطوات أعلاه"
        ),
        "en": (
            "━━━━━━━━━━━━━━━━━━━\n"
            "<b>🍎 iPhone Steps:</b>\n\n"
            "<b>1️⃣ Open Safari and go to:</b>\n"
            "<code>discstore.recargajogo.com.br</code>\n\n"
            "<b>2️⃣ Login</b>\n"
            "Tap Google and choose your account\n\n"
            "<b>3️⃣ Blue error page appears</b>\n"
            "It says <b>setting_error</b>\n"
            "⚠️ <b>Don't close it!</b>\n\n"
            "<b>4️⃣ Open History</b>\n"
            "Tap 📖 (book icon)\n"
            "Select <b>History</b>\n\n"
            "<b>5️ Copy the first link</b>\n"
            "Named <b>Discount Store</b>\n"
            "Long press → <b>Copy</b>\n\n"
            "<b>6️⃣ Send it here directly!</b>\n"
            "🤖 Bot will extract token automatically\n"
            "No need to copy token manually\n\n"
            "⚠️ <b>Video not available yet</b>\n"
            "We'll add it soon. Follow steps above"
        ),
        "vi": (
            "━━━━━━━━━━━━━━━━━━━\n"
            "<b>🍎 Các bước iPhone:</b>\n\n"
            "<b>1️⃣ Mở Safari và truy cập:</b>\n"
            "<code>discstore.recargajogo.com.br</code>\n\n"
            "<b>2️⃣ Đăng nhập</b>\n"
            "Nhấn Google và chọn tài khoản\n\n"
            "<b>3️⃣ Trang lỗi xanh hiện ra</b>\n"
            "Ghi <b>setting_error</b>\n"
            "⚠️ <b>Đừng đóng!</b>\n\n"
            "<b>4️⃣ Mở Lịch sử</b>\n"
            "Nhấn  (biểu tượng sách)\n"
            "Chọn <b>Lịch sử</b>\n\n"
            "<b>5️⃣ Sao chép link đầu tiên</b>\n"
            "Tên <b>Discount Store</b>\n"
            "Nhấn giữ → <b>Sao chép</b>\n\n"
            "<b>6️⃣ Gửi vào đây trực tiếp!</b>\n"
            "🤖 Bot sẽ tự động lấy token\n"
            "Không cần copy thủ công\n\n"
            "⚠️ <b>Video chưa có sẵn</b>\n"
            "Sẽ thêm sớm. Làm theo các bước trên"
        ),
        "hi": (
            "━━━━━━━━━━━━━━━━━━━\n"
            "<b> iPhone कदम:</b>\n\n"
            "<b>1️⃣ Safari खोलें और जाएं:</b>\n"
            "<code>discstore.recargajogo.com.br</code>\n\n"
            "<b>2️⃣ लॉगिन करें</b>\n"
            "Google दबाएं और अकाउंट चुनें\n\n"
            "<b>3️⃣ नीली एरर पेज दिखेगी</b>\n"
            "लिखा <b>setting_error</b>\n"
            "⚠️ <b>बंद न करें!</b>\n\n"
            "<b>4️⃣ हिस्ट्री खोलें</b>\n"
            "📖 (बुक आइकन) दबाएं\n"
            "<b>हिस्ट्री</b> चुनें\n\n"
            "<b>5️⃣ पहला लिंक कॉपी करें</b>\n"
            "नाम <b>Discount Store</b>\n"
            "लंबा दबाएं → <b>कॉपी</b>\n\n"
            "<b>6️⃣ यहाँ सीधे भेजें!</b>\n"
            "🤖 बॉट खुद token निकाल लेगा\n"
            "मैन्युअल कॉपी की ज़रूरत नहीं\n\n"
            "⚠️ <b>वीडियो अभी उपलब्ध नहीं</b>\n"
            "जल्द आएगा। ऊपर के कदम फॉलो करें"
        ),
    },

    "btn_show_video": {"ar": "▶️ عرض الشرح", "en": "▶️ Show Tutorial", "vi": "▶️ Xem", "hi": "▶️ देखें"},
    "btn_skip_tutorial": {"ar": "️ تخطي", "en": "️ Skip", "vi": "⏭️ Bỏ qua", "hi": "⏭️ छोड़ें"},
    "btn_retry_tutorial": {"ar": "🔄 إعادة الشرح", "en": "🔄 Retry", "vi": "🔄 Xem lại", "hi": "🔄 फिर से"},

    "ask_token": {
        "ar": "<b>🔐 أرسل الرابط الآن:</b>\n\n━━━━━━━━━━━━━━━━━━━\n🤖 <b>البوت سيستخرج التوكن تلقائياً</b>\nلا تحتاج لنسخ التوكن يدوياً\n\n فقط الصق الرابط وأرسله",
        "en": "<b>🔐 Send the link now:</b>\n\n━━━━━━━━━━━━━━━━━━━\n🤖 <b>Bot extracts token automatically</b>\nNo need to copy token manually\n\n Just paste and send",
        "vi": "<b>🔐 Gửi link ngay:</b>\n\n━━━━━━━━━━━━━━━━━━━\n <b>Bot tự động lấy token</b>\n\n📩 Dán và gửi",
        "hi": "<b>🔐 लिंक भेजें:</b>\n\n━━━━━━━━━━━━━━━━━━━\n🤖 <b>बॉट खुद token निकालेगा</b>\n\n📩 पेस्ट करें और भेजें",
    },

    "token_saved": {
        "ar": "<b>✅ تم حفظ التوكن بنجاح!</b>\n\n مشفر بـ <b>AES-256</b>\n📊 +10 نقاط\n\n🎯 الآن يمكنك استخدام جميع الأدوات!",
        "en": "<b>✅ Token saved!</b>\n\n🔐 <b>AES-256</b> encrypted\n +10 points\n\n🎯 You can now use all tools!",
        "vi": "<b>✅ Token đã lưu!</b>\n\n Mã hóa <b>AES-256</b>\n📊 +10 điểm",
        "hi": "<b>✅ Token सेव!</b>\n\n🔐 <b>AES-256</b> एन्क्रिप्टेड\n📊 +10 पॉइंट",
    },

    "token_invalid": {
        "ar": "<b>❌ الرابط/التوكن غير صالح!</b>\n\n تأكد من:\n• الرابط من discstore.recargajogo.com.br\n• لم تنتهِ صلاحيته\n\n📩 أرسل الرابط مرة أخرى:",
        "en": "<b>❌ Invalid link/token!</b>\n\n💡 Check:\n• Link from discstore.recargajogo.com.br\n• Not expired\n\n📩 Send again:",
        "vi": "<b>❌ Link/token không hợp lệ!</b>\n\n📩 Gửi lại:",
        "hi": "<b>❌ अमान्य लिंक/token!</b>\n\n फिर से भेजें:",
    },

    # ═══ HOME ════════════════════════════════════════════════════════════════

    "home_title": {"ar": "<b>⚡ BOLT</b> — إدارة حسابات FF", "en": "<b> BOLT</b> — FF Manager", "vi": "<b>⚡ BOLT</b> — Quản lý FF", "hi": "<b> BOLT</b> — FF प्रबंधक"},
    "home_subtitle": {"ar": "🛡️ محمي • مجاني • احترافي", "en": "🛡️ Protected • Free • Pro", "vi": "🛡️ Bảo mật • Miễn phí", "hi": "️ सुरक्षित • मुफ़्त"},

    "home_stats": {
        "ar": "📊 العمليات: <b>{ops}/{max}</b>\n🔥 السلسلة: <b>{streak}</b> يوم\n🏆 المستوى: <b>{level}</b>",
        "en": "📊 Today: <b>{ops}/{max}</b>\n🔥 Streak: <b>{streak}</b>\n🏆 Level: <b>{level}</b>",
        "vi": "📊 Hôm nay: <b>{ops}/{max}</b>\n🔥 Chuỗi: <b>{streak}</b>",
        "hi": "📊 आज: <b>{ops}/{max}</b>\n🔥 स्ट्रीक: <b>{streak}</b>",
    },
    "home_token_status": {"ar": " التوكن: <b>{status}</b>", "en": "🔐 Token: <b>{status}</b>", "vi": "🔐 Token: <b>{status}</b>", "hi": "🔐 Token: <b>{status}</b>"},
    "token_active": {"ar": "✅ مُفعّل", "en": "✅ Active", "vi": "✅ Hoạt động", "hi": "✅ सक्रिय"},
    "token_none": {"ar": "❌ غير مُضاف", "en": "❌ Not set", "vi": "❌ Chưa thêm", "hi": "❌ नहीं जोड़ा"},
    "home_choose": {"ar": "️ <b>اختر:</b>", "en": "⬇️ <b>Choose:</b>", "vi": "⬇️ <b>Chọn:</b>", "hi": "⬇️ <b>चुनें:</b>"},

    # ═══ BUTTONS ═════════════════════════════════════════════════════════════

    "btn_tools": {"ar": " الأدوات", "en": "🔧 Tools", "vi": "🔧 Công cụ", "hi": "🔧 टूल्स"},
    "btn_add": {"ar": "➕ إضافة حساب", "en": "➕ Add", "vi": "➕ Thêm", "hi": "➕ जोड़ें"},
    "btn_card": {"ar": "🃏 بطاقتي", "en": "🃏 My Card", "vi": "🃏 Thẻ", "hi": "🃏 कार्ड"},
    "btn_rewards": {"ar": "🏆 المكافآت", "en": "🏆 Rewards", "vi": "🏆 Thưởng", "hi": "🏆 इनाम"},
    "btn_daily": {"ar": "🎁 هدية يومية", "en": "🎁 Daily", "vi": "🎁 Quà", "hi": " रोज़ाना"},
    "btn_support": {"ar": "💬 الدعم", "en": "💬 Support", "vi": " Hỗ trợ", "hi": "💬 सहायता"},
    "btn_leaderboard": {"ar": "📊 المتصدرون", "en": "📊 Top", "vi": " Top", "hi": "📊 टॉप"},
    "btn_lang": {"ar": "🌍 اللغة", "en": "🌍 Lang", "vi": "🌍 Ngôn ngữ", "hi": "🌍 भाषा"},
    "btn_admin": {"ar": "👑 الإدارة", "en": "👑 Admin", "vi": "👑 Admin", "hi": "👑 एडमिन"},
    "btn_back": {"ar": "🔙 رجوع", "en": "🔙 Back", "vi": "🔙 Lại", "hi": " वापस"},
    "btn_home": {"ar": "🏠 الرئيسية", "en": "🏠 Home", "vi": " Trang chủ", "hi": "🏠 मुख्य"},
    "btn_cancel": {"ar": "❌ إلغاء", "en": "❌ Cancel", "vi": "❌ Huỷ", "hi": "❌ रद्द"},

    # ══ TOOLS ═══════════════════════════════════════════════════════════════

    "tools_title": {
        "ar": "<b>🔧 أدوات الحساب</b>\n\n🛡️ آمنة ومباشرة\n⬇️ <b>اختر:</b>",
        "en": "<b> Tools</b>\n\n🛡️ Safe & direct\n⬇️ <b>Choose:</b>",
        "vi": "<b> Công cụ</b>\n\n🛡️ An toàn\n⬇️ <b>Chọn:</b>",
        "hi": "<b> टूल्स</b>\n\n️ सुरक्षित\n⬇️ <b>चुनें:</b>",
    },

    "btn_nickname": {"ar": " تغيير الاسم", "en": "🎭 Name", "vi": "🎭 Tên", "hi": "🎭 नाम"},
    "btn_player_info": {"ar": "👤 معلوماتي", "en": "👤 Info", "vi": "👤 Info", "hi": "👤 जानकारी"},
    "btn_check_token": {"ar": "🔍 فحص التوكن", "en": "🔍 Check", "vi": "🔍 Kiểm tra", "hi": "🔍 जांच"},
    "btn_bind_info": {"ar": "📡 الربط", "en": "📡 Bind", "vi": "📡 Liên kết", "hi": " बाइंड"},
    "btn_change_bind": {"ar": "🔄 تغيير البريد", "en": "🔄 Email", "vi": "🔄 Email", "hi": "🔄 ईमेल"},
    "btn_unbind": {"ar": " فك الربط", "en": "🔓 Unbind", "vi": "🔓 Hủy", "hi": "🔓 अनबाइंड"},
    "btn_cancel_bind": {"ar": "🚫 إلغاء", "en": " Cancel", "vi": "🚫 Huỷ", "hi": "🚫 रद्द"},
    "btn_bind_new": {"ar": "📩 بريد جديد", "en": "📩 Email", "vi": " Email", "hi": "📩 ईमेल"},
    "btn_check_links": {"ar": "🌐 المنصات", "en": "🌐 Links", "vi": "🌐 Links", "hi": "🌐 लिंक"},
    "btn_revoke": {"ar": "🗑 إبطال", "en": "🗑 Revoke", "vi": "🗑 Thu hồi", "hi": " रद्द"},
    "btn_history": {"ar": "📋 السجل", "en": "📋 History", "vi": " Lịch sử", "hi": "📋 इतिहास"},

    "loading": {"ar": "⏳ جاري...", "en": "⏳ Loading...", "vi": " Đang...", "hi": "⏳ लोड..."},
    "success": {"ar": "✅ <b>تم!</b>", "en": "✅ <b>Done!</b>", "vi": "✅ <b>Xong!</b>", "hi": "✅ <b>हो गया!</b>"},

    "send_new_name": {"ar": "🎭 أرسل <b>الاسم الجديد</b>:", "en": "🎭 Send <b>new name</b>:", "vi": "🎭 Gửi <b>tên</b>:", "hi": "🎭 <b>नाम</b> भेजें:"},
    "name_changed": {"ar": "✅ <b>تم!</b>\n🎭 الاسم: <b>{name}</b>\n +5 نقاط", "en": "✅ <b>Done!</b>\n🎭 Name: <b>{name}</b>\n +5 pts", "vi": "✅ <b>Xong!</b>\n Tên: <b>{name}</b>", "hi": "✅ <b>हो गया!</b>\n🎭 नाम: <b>{name}</b>"},

    "daily_claimed": {"ar": "🎁✅ +<b>{pts}</b> نقطة!\n🔥 السلسلة: <b>{streak}</b>\n🏆 المستوى: <b>{level}</b>", "en": "🎁✅ +<b>{pts}</b> pts!\n🔥 Streak: <b>{streak}</b>\n🏆 Level: <b>{level}</b>", "vi": "🎁✅ +<b>{pts}</b> điểm!\n🔥 Chuỗi: <b>{streak}</b>", "hi": "🎁✅ +<b>{pts}</b> पॉइंट!\n🔥 स्ट्रीक: <b>{streak}</b>"},
    "daily_already": {"ar": "⏰ حصلت عليها اليوم!\n💡 عد غداً", "en": "⏰ Already claimed!\n💡 Tomorrow", "vi": "⏰ Đã nhận!\n💡 Ngày mai", "hi": " आज मिल गया!\n💡 कल"},

    # ═══ ADMIN ═══════════════════════════════════════════════════════════════

    "admin_title": {"ar": "<b>👑 لوحة الإدارة</b>", "en": "<b>👑 Admin Panel</b>", "vi": "<b> Admin</b>", "hi": "<b> एडमिन</b>"},
    "btn_stats": {"ar": "📈 إحصائيات", "en": "📈 Stats", "vi": "📈 Thống kê", "hi": "📈 आँकड़े"},
    "btn_broadcast": {"ar": " بث", "en": "📢 Broadcast", "vi": "📢 Phát", "hi": "📢 प्रसारण"},
    "btn_backup": {"ar": "💾 نسخة", "en": "💾 Backup", "vi": "💾 Sao lưu", "hi": "💾 बैकअप"},
    "btn_ban": {"ar": "🚫 حظر", "en": "🚫 Ban", "vi": "🚫 Cấm", "hi": "🚫 प्रतिबंध"},
    "btn_audit": {"ar": " السجل", "en": "📋 Audit", "vi": "📋 Nhật ký", "hi": "📋 लॉग"},
    "btn_tickets": {"ar": "💬 تذاكر", "en": "💬 Tickets", "vi": "💬 Vé", "hi": "💬 टिकट"},
    "btn_sec_stats": {"ar": "🛡️ الحماية", "en": "🛡️ Security", "vi": "🛡️ Bảo mật", "hi": "🛡️ सुरक्षा"},
    "btn_admins": {"ar": " الأدمن", "en": " Admins", "vi": "👥 Admin", "hi": "👥 एडमिन"},
    "btn_tutorials": {"ar": "📹 الفيديوهات", "en": " Videos", "vi": "📹 Video", "hi": "📹 वीडियो"},
    "btn_view_tokens": {"ar": " التوكنات", "en": " Tokens", "vi": "🔐 Token", "hi": "🔐 टोकन"},

    "stats_text": {"ar": "<b>📊 إحصائيات</b>\n\n👥 المستخدمون: <b>{users}</b>\n🔐 توكن: <b>{with_token}</b>\n⚡ العمليات: <b>{ops}</b>", "en": "<b>📊 Stats</b>\n\n Users: <b>{users}</b>\n🔐 Token: <b>{with_token}</b>\n⚡ Ops: <b>{ops}</b>", "vi": "<b>📊 Thống kê</b>\n\n👥 Users: <b>{users}</b>", "hi": "<b>📊 आँकड़े</b>\n\n👥 Users: <b>{users}</b>"},

    "not_auth": {"ar": "⛔️ <b>غير مصرح!</b>", "en": "️ <b>Unauthorized!</b>", "vi": "⛔️ <b>Không có quyền!</b>", "hi": "⛔️ <b>अनाधिकृत!</b>"},
    "ban_ask_id": {"ar": "🚫 أرسل <b>معرف المستخدم</b>:", "en": "🚫 Send <b>user ID</b>:", "vi": "🚫 Gửi <b>ID</b>:", "hi": " <b>ID</b> भेजें:"},
    "ban_done": {"ar": "🚫 <b>تم حظر {uid}!</b>", "en": "🚫 <b>Banned {uid}!</b>", "vi": "🚫 <b>Đã cấm {uid}!</b>", "hi": "🚫 <b>{uid} प्रतिबंधित!</b>"},
    "broadcast_ask": {"ar": "📢 أرسل الرسالة:", "en": "📢 Send message:", "vi": "📢 Gửi:", "hi": "📢 भेजें:"},
    "broadcast_done": {"ar": " <b>تم!</b>\n✅ نجح: <b>{ok}</b>\n❌ فشل: <b>{fail}</b>", "en": "📢 <b>Done!</b>\n✅ OK: <b>{ok}</b>\n Fail: <b>{fail}</b>", "vi": "📢 <b>Xong!</b>\n✅ OK: <b>{ok}</b>\n❌ Fail: <b>{fail}</b>", "hi": "📢 <b>पूरा!</b>\n✅ OK: <b>{ok}</b>\n❌ Fail: <b>{fail}</b>"},
    "backup_ready": {"ar": "💾 <b>جاهزة!</b>", "en": "💾 <b>Ready!</b>", "vi": "💾 <b>Sẵn sàng!</b>", "hi": "💾 <b>तैयार!</b>"},

    # ═══ MISC ════════════════════════════════════════════════════════════════

    "ratelimited": {"ar": "⏳ انتظر <b>{sec}</b> ثانية", "en": "⏳ Wait <b>{sec}</b>s", "vi": "⏳ Đợi <b>{sec}</b>s", "hi": "⏳ <b>{sec}</b> सेकंड रुकें"},
    "ops_exhausted": {"ar": "⚠️ <b>انتهت عملياتك!</b>\n💡 عد غداً", "en": "⚠️ <b>Daily limit!</b>\n💡 Tomorrow", "vi": "⚠️ <b>Hết lượt!</b>\n💡 Ngày mai", "hi": "⚠️ <b>सीमा पूरी!</b>\n💡 कल"},
    "user_banned": {"ar": "⛔️ <b>محظور</b>", "en": "⛔️ <b>Banned</b>", "vi": "⛔️ <b>Bị cấm</b>", "hi": "⛔️ <b>प्रतिबंधित</b>"},
    "cancel_done": {"ar": "✅ تم الإلغاء", "en": "✅ Cancelled", "vi": "✅ Đã huỷ", "hi": "✅ रद्द"},
    "unknown": {"ar": "❓ /start", "en": "❓ /start", "vi": "❓ /start", "hi": "❓ /start"},
}


def t(user_id: int, key: str, **fmt) -> str:
    lang = D.get_lang(user_id)
    entry = _S.get(key)
    if not entry:
        return key
    text = entry.get(lang, entry.get("ar", key))
    if fmt:
        try:
            text = text.format(**fmt)
        except (KeyError, IndexError):
            pass
    return text
