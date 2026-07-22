"""
BOLT ⚡ — Internationalization
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Arabic / English / Vietnamese / Hindi
📖 Full tutorials for each language
"""

from __future__ import annotations
import database as D

LANGS = {
    "ar": "🇸🇦 العربية",
    "en": "🇬 English",
    "vi": "🇻🇳 Tiếng Việt",
    "hi": "🇮🇳 हिन्दी",
}

_S: dict[str, dict[str, str]] = {

    # ═══════════════════════════════════════════════════════════════════
    #  LANGUAGE SELECTION (First Screen)
    # ═══════════════════════════════════════════════════════════════════

    "welcome_select_lang": {
        "ar": (
            "<b>⚡ مرحباً بك في BOLT!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "🛡️ بوت <b>مجاني 100%</b> لإدارة حسابات فري فاير\n"
            "🔐 توكنك مشفر بأمان تام\n"
            "🏆 أدوات احترافية تؤثر فعلياً على حسابك\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "🌍 <b>اختر لغتك المفضلة:</b>"
        ),
        "en": (
            "<b>⚡ Welcome to BOLT!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "🛡️ <b>100% free</b> Free Fire account manager\n"
            "🔐 Your token is fully encrypted\n"
            " Professional tools that affect your account\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "🌍 <b>Choose your language:</b>"
        ),
        "vi": (
            "<b>⚡ Chào mừng đến BOLT!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "🛡️ <b>100% miễn phí</b>\n"
            "🔐 Token mã hóa hoàn toàn\n"
            "🏆 Công cụ chuyên nghiệp\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "🌍 <b>Chọn ngôn ngữ:</b>"
        ),
        "hi": (
            "<b>⚡ BOLT में स्वागत!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "️ <b>100% मुफ़्त</b>\n"
            " टोकन पूर्ण रूप से एन्क्रिप्टेड\n"
            "🏆 पेशेवर उपकरण\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            " <b>अपनी भाषा चुनें:</b>"
        ),
    },

    "lang_selected": {
        "ar": "✅ <b>تم اختيار اللغة!</b>\n\n جاري تحميل الشرح...",
        "en": "✅ <b>Language selected!</b>\n\n Loading tutorial...",
        "vi": "✅ <b>Đã chọn ngôn ngữ!</b>\n\n Đang tải hướng dẫn...",
        "hi": "✅ <b>भाषा चुनी गई!</b>\n\n ट्यूटोरियल लोड हो रहा है...",
    },

    # ═══════════════════════════════════════════════════════════════════
    #  TUTORIAL SCREEN
    # ═══════════════════════════════════════════════════════════════════

    "tutorial_title": {
        "ar": "<b>📱 كيف تحصل على Access Token?</b>",
        "en": "<b>📱 How to Get Access Token?</b>",
        "vi": "<b>📱 Cách lấy Access Token?</b>",
        "hi": "<b>📱 Access Token कैसे प्राप्त करें?</b>",
    },

    "tutorial_subtitle": {
        "ar": "━━━━━━━━━━━━━━━━━━━\n📖 اتبع الخطوات بعناية",
        "en": "━━━━━━━━━━━━━━━━━━━\n📖 Follow steps carefully",
        "vi": "━━━━━━━━━━━━━━━━━━━\n📖 Làm theo từng bước",
        "hi": "━━━━━━━━━━━━━━━━━━━\n📖 सावधानी से पालन करें",
    },

    "tutorial_what_is": {
        "ar": (
            "<b>❓ ما هو Access Token؟</b>\n\n"
            "هو رمز سري يربط البوت بحسابك في Free Fire.\n"
            "بدونه لا يمكن استخدام أي أداة.\n\n"
            "⚠️ <b>تحذيرات مهمة:</b>\n"
            "• 🔐 البوت يشفر التوكن ويحميه\n"
            "• ❌ لا تشارك التوكن مع أي شخص\n"
            "• ️ التوكن محمي بتشفير AES-256"
        ),
        "en": (
            "<b>❓ What is Access Token?</b>\n\n"
            "It's a secret key connecting the bot to your Free Fire account.\n"
            "Without it, no tool can work.\n\n"
            "️ <b>Important:</b>\n"
            "• 🔐 The bot encrypts your token\n"
            "• ❌ Never share it with anyone\n"
            "• ️ Protected with AES-256"
        ),
        "vi": (
            "<b>❓ Access Token là gì?</b>\n\n"
            "Là khóa bí mật kết nối bot với tài khoản Free Fire.\n"
            "Không có nó, không thể sử dụng công cụ nào.\n\n"
            "⚠️ <b>Quan trọng:</b>\n"
            "• 🔐 Bot mã hóa token của bạn\n"
            "• ❌ Không chia sẻ với ai\n"
            "• 🛡️ Bảo vệ bằng AES-256"
        ),
        "hi": (
            "<b>❓ Access Token क्या है?</b>\n\n"
            "यह एक गुप्त कुंजी है जो बॉट को आपके Free Fire खाते से जोड़ती है।\n"
            "इसके बिना कोई टूल काम नहीं कर सकता।\n\n"
            "️ <b>महत्वपूर्ण:</b>\n"
            "• 🔐 बॉट आपके टोकन को एन्क्रिप्ट करता है\n"
            "• ❌ किसी के साथ साझा न करें\n"
            "• ️ AES-256 से सुरक्षित"
        ),
    },

    "tutorial_choose_platform": {
        "ar": (
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "<b>📱 اختر نوع جهازك:</b>"
        ),
        "en": (
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "<b>📱 Choose your device:</b>"
        ),
        "vi": (
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "<b>📱 Chọn thiết bị của bạn:</b>"
        ),
        "hi": (
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "<b> अपना डिवाइस चुनें:</b>"
        ),
    },

    "tutorial_android_title": {
        "ar": " أندرويد",
        "en": "🤖 Android",
        "vi": "🤖 Android",
        "hi": " Android",
    },

    "tutorial_ios_title": {
        "ar": " آيفون",
        "en": "🍎 iPhone",
        "vi": " iPhone",
        "hi": " iPhone",
    },

    "tutorial_android_steps": {
        "ar": (
            "<b>🤖 خطوات أندرويد:</b>\n\n"
            "1️⃣ افتح متصفح <b>Chrome</b>\n\n"
            "2️ اذهب إلى الموقع:\n"
            "<code>discstore.recargajogo.com.br</code>\n\n"
            "3️ سجّل دخول بحساب Garena الخاص بك\n\n"
            "4️⃣ اتبع الخطوات في الفيديو أعلاه\n\n"
            "5️⃣ انسخ Access Token\n\n"
            "6️⃣ عد إلى البوت وأدخل التوكن"
        ),
        "en": (
            "<b>🤖 Android Steps:</b>\n\n"
            "1️⃣ Open <b>Chrome</b> browser\n\n"
            "2️⃣ Go to website:\n"
            "<code>discstore.recargajogo.com.br</code>\n\n"
            "3️ Login with your Garena account\n\n"
            "4️⃣ Follow steps in video above\n\n"
            "5️⃣ Copy Access Token\n\n"
            "6️⃣ Return to bot and enter token"
        ),
        "vi": (
            "<b>🤖 Các bước Android:</b>\n\n"
            "1️⃣ Mở trình duyệt <b>Chrome</b>\n\n"
            "2️ Truy cập:\n"
            "<code>discstore.recargajogo.com.br</code>\n\n"
            "3️⃣ Đăng nhập tài khoản Garena\n\n"
            "4️⃣ Làm theo video ở trên\n\n"
            "5️⃣ Sao chép Access Token\n\n"
            "6️⃣ Quay lại bot và nhập token"
        ),
        "hi": (
            "<b>🤖 Android कदम:</b>\n\n"
            "1️ <b>Chrome</b> ब्राउज़र खोलें\n\n"
            "2️⃣ वेबसाइट पर जाएं:\n"
            "<code>discstore.recargajogo.com.br</code>\n\n"
            "3️⃣ Garena अकाउंट से लॉगिन करें\n\n"
            "4️⃣ ऊपर दिए गए वीडियो का पालन करें\n\n"
            "5️⃣ Access Token कॉपी करें\n\n"
            "6️ बॉट पर वापस आएं और टोकन दर्ज करें"
        ),
    },

    "tutorial_ios_steps": {
        "ar": (
            "<b> خطوات آيفون:</b>\n\n"
            "1️⃣ افتح متصفح <b>Safari</b>\n\n"
            "2️⃣ اذهب إلى الموقع:\n"
            "<code>discstore.recargajogo.com.br</code>\n\n"
            "3️⃣ سجّل دخول بحساب Garena الخاص بك\n\n"
            "4️⃣ اتبع الخطوات في الفيديو أعلاه\n\n"
            "5️⃣ انسخ Access Token\n\n"
            "6️⃣ عد إلى البوت وأدخل التوكن"
        ),
        "en": (
            "<b> iPhone Steps:</b>\n\n"
            "1️⃣ Open <b>Safari</b> browser\n\n"
            "2️ Go to website:\n"
            "<code>discstore.recargajogo.com.br</code>\n\n"
            "3️⃣ Login with your Garena account\n\n"
            "4️⃣ Follow steps in video above\n\n"
            "5️⃣ Copy Access Token\n\n"
            "6️ Return to bot and enter token"
        ),
        "vi": (
            "<b> Các bước iPhone:</b>\n\n"
            "1️⃣ Mở trình duyệt <b>Safari</b>\n\n"
            "2️⃣ Truy cập:\n"
            "<code>discstore.recargajogo.com.br</code>\n\n"
            "3️ Đăng nhập tài khoản Garena\n\n"
            "4️⃣ Làm theo video ở trên\n\n"
            "5️⃣ Sao chép Access Token\n\n"
            "6️⃣ Quay lại bot và nhập token"
        ),
        "hi": (
            "<b>🍎 iPhone कदम:</b>\n\n"
            "1️⃣ <b>Safari</b> ब्राउज़र खोलें\n\n"
            "2️ वेबसाइट पर जाएं:\n"
            "<code>discstore.recargajogo.com.br</code>\n\n"
            "3️⃣ Garena अकाउंट से लॉगिन करें\n\n"
            "4️ ऊपर दिए गए वीडियो का पालन करें\n\n"
            "5️ Access Token कॉपी करें\n\n"
            "6️⃣ बॉट पर वापस आएं और टोकन दर्ज करें"
        ),
    },

    "btn_show_video": {
        "ar": "▶️ عرض فيديو الشرح",
        "en": "▶️ Watch Tutorial Video",
        "vi": "▶️ Xem Video Hướng Dẫn",
        "hi": "▶️ ट्यूटोरियल वीडियो देखें",
    },

    "btn_skip_tutorial": {
        "ar": "⏭️ تخطي الشرح",
        "en": "⏭️ Skip Tutorial",
        "vi": "️ Bỏ qua Hướng dẫn",
        "hi": "⏭️ ट्यूटोरियल छोड़ें",
    },

    "btn_retry_tutorial": {
        "ar": "🔄 عرض الشرح مرة أخرى",
        "en": "🔄 Show Tutorial Again",
        "vi": "🔄 Xem lại Hướng dẫn",
        "hi": "🔄 ट्यूटोरियल फिर से देखें",
    },

    # ═══════════════════════════════════════════════════════════════════
    #  TOKEN INPUT
    # ═══════════════════════════════════════════════════════════════════

    "ask_token": {
        "ar": (
            "<b>🔐 أدخل Access Token الخاص بك:</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "📏 <b>الشروط:</b>\n"
            "✅ 20+ حرف\n"
            "✅ بدون مسافات\n"
            "✅ صالح (غير منتهي)\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "📩 <b>أرسل التوكن الآن:</b>"
        ),
        "en": (
            "<b> Enter your Access Token:</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "📏 <b>Requirements:</b>\n"
            "✅ 20+ characters\n"
            "✅ No spaces\n"
            "✅ Valid (not expired)\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            " <b>Send token now:</b>"
        ),
        "vi": (
            "<b>🔐 Nhập Access Token:</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "📏 <b>Yêu cầu:</b>\n"
            "✅ 20+ ký tự\n"
            "✅ Không khoảng trắng\n"
            "✅ Còn hiệu lực\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "📩 <b>Gửi token:</b>"
        ),
        "hi": (
            "<b>🔐 अपना Access Token दर्ज करें:</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "📏 <b>आवश्यकताएं:</b>\n"
            "✅ 20+ अक्षर\n"
            "✅ कोई स्पेस नहीं\n"
            "✅ सक्रिय होना चाहिए\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            " <b>टोकन भेजें:</b>"
        ),
    },

    "token_saved": {
        "ar": (
            "<b>✅ تم حفظ التوكن بنجاح!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            " مشفر بـ <b>AES-256</b>\n"
            " +10 نقاط مكافأة\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "🎯 الآن يمكنك استخدام جميع الأدوات!"
        ),
        "en": (
            "<b>✅ Token saved successfully!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "🔐 Encrypted with <b>AES-256</b>\n"
            "📊 +10 reward points\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "🎯 You can now use all tools!"
        ),
        "vi": (
            "<b>✅ Token đã lưu thành công!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            " Mã hóa bằng <b>AES-256</b>\n"
            "📊 +10 điểm thưởng\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "🎯 Bạn có thể sử dụng tất cả công cụ!"
        ),
        "hi": (
            "<b>✅ टोकन सफलतापूर्वक सेव!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "🔐 <b>AES-256</b> से एन्क्रिप्टेड\n"
            "📊 +10 पुरस्कार पॉइंट\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "🎯 अब आप सभी टूल्स उपयोग कर सकते हैं!"
        ),
    },

    "token_invalid": {
        "ar": (
            "<b>❌ توكن غير صالح!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "💡 <b>تأكد من:</b>\n"
            "• التوكن صحيح\n"
            "• لم ينتهِ صلاحيته\n"
            "• تم نسخه بالكامل\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "📩 <b>حاول مرة أخرى:</b>"
        ),
        "en": (
            "<b>❌ Invalid token!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "💡 <b>Check:</b>\n"
            "• Token is correct\n"
            "• Not expired\n"
            "• Copied completely\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "📩 <b>Try again:</b>"
        ),
        "vi": (
            "<b>❌ Token không hợp lệ!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "💡 <b>Kiểm tra:</b>\n"
            "• Token đúng\n"
            "• Chưa hết hạn\n"
            "• Sao chép đầy đủ\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "📩 <b>Thử lại:</b>"
        ),
        "hi": (
            "<b>❌ अमान्य टोकन!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "💡 <b>जांचें:</b>\n"
            "• टोकन सही है\n"
            "• समाप्त नहीं हुआ\n"
            "• पूरी तरह कॉपी किया गया\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "📩 <b>फिर से कोशिश करें:</b>"
        ),
    },

    "token_short": {
        "ar": (
            "<b>❌ التوكن قصير جداً!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            " يجب أن يكون <b>20 حرف أو أكثر</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            " <b>أرسل توكن صالح:</b>"
        ),
        "en": (
            "<b>❌ Token too short!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "📏 Must be <b>20+ characters</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "📩 <b>Send valid token:</b>"
        ),
        "vi": (
            "<b>❌ Token quá ngắn!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "📏 Phải có <b>20+ ký tự</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "📩 <b>Gửi token hợp lệ:</b>"
        ),
        "hi": (
            "<b> टोकन बहुत छोटा!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "📏 <b>20+ अक्षर</b> होने चाहिए\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "📩 <b>मान्य टोकन भेजें:</b>"
        ),
    },

    # ═══════════════════════════════════════════════════════════════════
    #  HOME SCREEN
    # ═══════════════════════════════════════════════════════════════════

    "home_title": {
        "ar": "<b>⚡ BOLT — إدارة حسابات Free Fire</b>",
        "en": "<b>⚡ BOLT — Free Fire Account Manager</b>",
        "vi": "<b>⚡ BOLT — Quản lý tài khoản FF</b>",
        "hi": "<b> BOLT — Free Fire खाता प्रबंधक</b>",
    },

    "home_subtitle": {
        "ar": "🛡️ محمي • مجاني • احترافي",
        "en": "🛡️ Protected • Free • Professional",
        "vi": "🛡️ Bảo mật • Miễn phí • Chuyên nghiệp",
        "hi": "🛡️ सुरक्षित • मुफ़्त • पेशेवर",
    },

    "home_stats": {
        "ar": (
            "━━━━━━━━━━━━━━━━━━━\n\n"
            " العمليات اليوم: <b>{ops}/{max}</b>\n"
            "🔥 السلسلة: <b>{streak}</b> يوم\n"
            "🏆 المستوى: <b>{level}</b>"
        ),
        "en": (
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "📊 Today: <b>{ops}/{max}</b>\n"
            "🔥 Streak: <b>{streak}</b> days\n"
            "🏆 Level: <b>{level}</b>"
        ),
        "vi": (
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "📊 Hôm nay: <b>{ops}/{max}</b>\n"
            "🔥 Chuỗi: <b>{streak}</b> ngày\n"
            "🏆 Cấp độ: <b>{level}</b>"
        ),
        "hi": (
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "📊 आज: <b>{ops}/{max}</b>\n"
            " स्ट्रीक: <b>{streak}</b> दिन\n"
            "🏆 स्तर: <b>{level}</b>"
        ),
    },

    "home_token_status": {
        "ar": "🔐 التوكن: <b>{status}</b>",
        "en": "🔐 Token: <b>{status}</b>",
        "vi": "🔐 Token: <b>{status}</b>",
        "hi": "🔐 टोकन: <b>{status}</b>",
    },

    "token_active": {"ar": "✅ مُفعّل", "en": "✅ Active", "vi": "✅ Hoạt động", "hi": "✅ सक्रिय"},
    "token_none": {"ar": "❌ غير مُضاف", "en": "❌ Not set", "vi": "❌ Chưa thêm", "hi": " नहीं जोड़ा"},

    "home_choose": {
        "ar": "⬇️ <b>اختر من القائمة:</b>",
        "en": "⬇️ <b>Choose:</b>",
        "vi": "️ <b>Chọn:</b>",
        "hi": "⬇️ <b>चुनें:</b>",
    },

    # ═══════════════════════════════════════════════════════════════════
    #  BUTTONS
    # ═══════════════════════════════════════════════════════════════════

    "btn_tools": {"ar": "🔧 الأدوات", "en": "🔧 Tools", "vi": "🔧 Công cụ", "hi": "🔧 टूल्स"},
    "btn_add": {"ar": "➕ إضافة حساب", "en": "➕ Add Account", "vi": "➕ Thêm TK", "hi": "➕ खाता जोड़ें"},
    "btn_card": {"ar": "🃏 بطاقتي", "en": "🃏 My Card", "vi": "🃏 Thẻ của tôi", "hi": "🃏 मेरा कार्ड"},
    "btn_rewards": {"ar": "🏆 المكافآت", "en": "🏆 Rewards", "vi": "🏆 Phần thưởng", "hi": " पुरस्कार"},
    "btn_daily": {"ar": "🎁 هدية يومية", "en": "🎁 Daily Gift", "vi": "🎁 Quà hàng ngày", "hi": "🎁 दैनिक उपहार"},
    "btn_support": {"ar": "💬 الدعم", "en": "💬 Support", "vi": "💬 Hỗ trợ", "hi": "💬 सहायता"},
    "btn_leaderboard": {"ar": "📊 المتصدرون", "en": " Leaderboard", "vi": " Bảng xếp hạng", "hi": "📊 लीडरबोर्ड"},
    "btn_lang": {"ar": "🌍 اللغة", "en": "🌍 Language", "vi": "🌍 Ngôn ngữ", "hi": " भाषा"},
    "btn_admin": {"ar": "👑 الإدارة", "en": "👑 Admin", "vi": " Quản trị", "hi": " एडमिन"},
    "btn_back": {"ar": "🔙 رجوع", "en": "🔙 Back", "vi": " Quay lại", "hi": " वापस"},
    "btn_home": {"ar": "🏠 الرئيسية", "en": "🏠 Home", "vi": "🏠 Trang chủ", "hi": "🏠 मुख्य"},
    "btn_cancel": {"ar": "❌ إلغاء", "en": "❌ Cancel", "vi": "❌ Huỷ", "hi": " रद्द"},

    # ══════════════════════════════════════════════════════════════════
    #  TOOLS MENU
    # ═══════════════════════════════════════════════════════════════════

    "tools_title": {
        "ar": (
            "<b>🔧 أدوات الحساب</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "🛡️ جميع العمليات آمنة ومباشرة\n"
            " بدون طرف ثالث — Garena فقط\n\n"
            "⬇️ <b>اختر العملية:</b>"
        ),
        "en": (
            "<b> Account Tools</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "️ All operations safe & direct\n"
            "🔐 No third-party — Garena only\n\n"
            "⬇️ <b>Choose action:</b>"
        ),
        "vi": (
            "<b>🔧 Công cụ tài khoản</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "🛡️ Tất cả thao tác an toàn\n"
            "🔐 Chỉ Garena\n\n"
            "⬇️ <b>Chọn thao tác:</b>"
        ),
        "hi": (
            "<b>🔧 खाता उपकरण</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "🛡️ सभी ऑपरेशन सुरक्षित\n"
            "🔐 केवल Garena\n\n"
            "⬇️ <b>क्रिया चुनें:</b>"
        ),
    },

    "btn_nickname": {"ar": " تغيير الاسم", "en": "🎭 Change Name", "vi": "🎭 Đổi tên", "hi": "🎭 नाम बदलें"},
    "btn_player_info": {"ar": "👤 معلوماتي", "en": " My Info", "vi": " Thông tin", "hi": " मेरी जानकारी"},
    "btn_check_token": {"ar": "🔍 فحص التوكن", "en": "🔍 Check Token", "vi": "🔍 Kiểm tra Token", "hi": "🔍 टोकन जांच"},
    "btn_bind_info": {"ar": " الربط", "en": "📡 Bind Info", "vi": "📡 Liên kết", "hi": "📡 बाइंड"},
    "btn_change_bind": {"ar": "🔄 تغيير البريد", "en": " Change Email", "vi": "🔄 Đổi Email", "hi": "🔄 ईमेल बदलें"},
    "btn_unbind": {"ar": "🔓 فك الربط", "en": "🔓 Unbind", "vi": " Hủy liên kết", "hi": "🔓 अनबाइंड"},
    "btn_cancel_bind": {"ar": " إلغاء الربط", "en": "🚫 Cancel Bind", "vi": "🚫 Hủy yêu cầu", "hi": " बाइंड रद्द"},
    "btn_bind_new": {"ar": "📩 بريد جديد", "en": "📩 New Email", "vi": "📩 Email mới", "hi": "📩 नया ईमेल"},
    "btn_check_links": {"ar": "🌐 المنصات", "en": " Platforms", "vi": "🌐 Nền tảng", "hi": "🌐 प्लेटफॉर्म"},
    "btn_revoke": {"ar": "🗑 إبطال التوكن", "en": "🗑 Revoke Token", "vi": "🗑 Thu hồi Token", "hi": "🗑 टोकन रद्द"},
    "btn_history": {"ar": "📋 السجل", "en": "📋 History", "vi": " Lịch sử", "hi": "📋 इतिहास"},

    # ═══════════════════════════════════════════════════════════════════
    #  OPERATIONS
    # ══════════════════════════════════════════════════════════════════

    "loading": {
        "ar": "⏳ جاري المعالجة...",
        "en": "⏳ Processing...",
        "vi": "⏳ Đang xử lý...",
        "hi": "⏳ प्रोसेस हो रहा है...",
    },

    "success": {
        "ar": "✅ <b>تمت العملية بنجاح!</b>",
        "en": "✅ <b>Operation successful!</b>",
        "vi": "✅ <b>Thao tác thành công!</b>",
        "hi": "✅ <b>ऑपरेशन सफल!</b>",
    },

    "error_generic": {
        "ar": "❌ <b>حدث خطأ.</b> حاول مرة أخرى.",
        "en": "❌ <b>Error occurred.</b> Try again.",
        "vi": "❌ <b>Có lỗi xảy ra.</b> Thử lại.",
        "hi": "❌ <b>त्रुटि हुई।</b> फिर से कोशिश करें।",
    },

    # More strings will be added as needed
    "send_new_name": {
        "ar": " أرسل <b>الاسم الجديد</b>:",
        "en": " Send <b>new name</b>:",
        "vi": "🎭 Gửi <b>tên mới</b>:",
        "hi": "🎭 <b>नया नाम</b> भेजें:",
    },

    "name_changed": {
        "ar": "✅ <b>تم تغيير الاسم!</b>\n\n الاسم الجديد: <b>{name}</b>\n\n+5 نقاط!",
        "en": "✅ <b>Name changed!</b>\n\n New name: <b>{name}</b>\n\n+5 points!",
        "vi": "✅ <b>Đã đổi tên!</b>\n\n🎭 Tên mới: <b>{name}</b>\n\n+5 điểm!",
        "hi": "✅ <b>नाम बदला गया!</b>\n\n🎭 नया नाम: <b>{name}</b>\n\n+5 पॉइंट!",
    },

    # ═══════════════════════════════════════════════════════════════════
    #  REWARDS
    # ═══════════════════════════════════════════════════════════════════

    "daily_claimed": {
        "ar": (
            "<b>✅ حصلت على مكافأة!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "⭐ +<b>{pts}</b> نقطة\n"
            "🔥 السلسلة: <b>{streak}</b> يوم\n"
            "🏆 المستوى: <b>{level}</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "💡 عد غداً لمكافأة أكبر!"
        ),
        "en": (
            "<b>🎁✅ Reward claimed!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "⭐ +<b>{pts}</b> points\n"
            "🔥 Streak: <b>{streak}</b> days\n"
            "🏆 Level: <b>{level}</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "💡 Come back tomorrow!"
        ),
        "vi": (
            "<b>🎁✅ Đã nhận thưởng!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "⭐ +<b>{pts}</b> điểm\n"
            "🔥 Chuỗi: <b>{streak}</b> ngày\n"
            "🏆 Cấp độ: <b>{level}</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "💡 Quay lại ngày mai!"
        ),
        "hi": (
            "<b>🎁✅ इनाम प्राप्त!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "⭐ +<b>{pts}</b> पॉइंट\n"
            " स्ट्रीक: <b>{streak}</b> दिन\n"
            "🏆 स्तर: <b>{level}</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "💡 कल वापस आएं!"
        ),
    },

    "daily_already": {
        "ar": (
            "⏰ <b>حصلت على هديتك اليوم!</b>\n\n"
            " عد غداً للمكافأة التالية.\n"
            "🔥 حافظ على سلسلتك!"
        ),
        "en": (
            "⏰ <b>Already claimed today!</b>\n\n"
            "💡 Come back tomorrow.\n"
            "🔥 Keep your streak!"
        ),
        "vi": (
            "⏰ <b>Đã nhận hôm nay!</b>\n\n"
            "💡 Quay lại ngày mai.\n"
            "🔥 Giữ chuỗi của bạn!"
        ),
        "hi": (
            " <b>आज मिल गया!</b>\n\n"
            "💡 कल आएं।\n"
            "🔥 स्ट्रीक बनाए रखें!"
        ),
    },

    # ═══════════════════════════════════════════════════════════════════
    #  ADMIN PANEL
    # ══════════════════════════════════════════════════════════════════

    "admin_title": {
        "ar": "<b> لوحة الإدارة — BOLT</b>",
        "en": "<b>👑 Admin Panel — BOLT</b>",
        "vi": "<b>👑 Bảng Quản trị — BOLT</b>",
        "hi": "<b> एडमिन पैनल — BOLT</b>",
    },

    "btn_stats": {"ar": "📈 إحصائيات", "en": "📈 Stats", "vi": "📈 Thống kê", "hi": "📈 आँकड़े"},
    "btn_broadcast": {"ar": " بث", "en": "📢 Broadcast", "vi": "📢 Phát sóng", "hi": "📢 प्रसारण"},
    "btn_backup": {"ar": "💾 نسخة", "en": "💾 Backup", "vi": "💾 Sao lưu", "hi": " बैकअप"},
    "btn_ban": {"ar": "🚫 حظر", "en": "🚫 Ban", "vi": " Cấm", "hi": " प्रतिबंध"},
    "btn_audit": {"ar": "📋 السجل", "en": "📋 Audit Log", "vi": "📋 Nhật ký", "hi": " लॉग"},
    "btn_tickets": {"ar": "💬 تذاكر", "en": "💬 Tickets", "vi": "💬 Vé", "hi": "💬 टिकट"},
    "btn_sec_stats": {"ar": "🛡️ الحماية", "en": "🛡️ Security", "vi": "🛡️ Bảo mật", "hi": "🛡️ सुरक्षा"},
    "btn_admins": {"ar": " الأدمن", "en": " Admins", "vi": " Quản trị viên", "hi": "👥 एडमिन"},
    "btn_tutorials": {"ar": "📹 الفيديوهات", "en": "📹 Tutorials", "vi": "📹 Video", "hi": "📹 ट्यूटोरियल"},
    "btn_view_tokens": {"ar": "🔐 التوكنات", "en": "🔐 Tokens", "vi": "🔐 Token", "hi": "🔐 टोकन"},

    "stats_text": {
        "ar": (
            "<b>📊 إحصائيات BOLT</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "👥 المستخدمون: <b>{users}</b>\n"
            "🔐 لديهم توكن: <b>{with_token}</b>\n"
            " إجمالي العمليات: <b>{ops}</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━"
        ),
        "en": (
            "<b>📊 BOLT Stats</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "👥 Users: <b>{users}</b>\n"
            "🔐 With token: <b>{with_token}</b>\n"
            "⚡ Total ops: <b>{ops}</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━"
        ),
        "vi": (
            "<b> Thống kê BOLT</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "👥 Người dùng: <b>{users}</b>\n"
            " Có token: <b>{with_token}</b>\n"
            "⚡ Tổng thao tác: <b>{ops}</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━"
        ),
        "hi": (
            "<b> BOLT आँकड़े</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "👥 उपयोगकर्ता: <b>{users}</b>\n"
            " टोकन के साथ: <b>{with_token}</b>\n"
            "⚡ कुल ऑपरेशन: <b>{ops}</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━"
        ),
    },

    "not_auth": {
        "ar": "⛔️ <b>غير مصرح!</b>",
        "en": "⛔️ <b>Unauthorized!</b>",
        "vi": "⛔️ <b>Không có quyền!</b>",
        "hi": "⛔️ <b>अनाधिकृत!</b>",
    },

    "ban_ask_id": {
        "ar": "🚫 أرسل <b>معرف المستخدم</b> للحظر:",
        "en": "🚫 Send <b>user ID</b> to ban:",
        "vi": "🚫 Gửi <b>ID người dùng</b> để cấm:",
        "hi": "🚫 प्रतिबंध के लिए <b>यूज़र ID</b> भेजें:",
    },

    "ban_done": {
        "ar": "🚫 <b>تم حظر {uid}!</b>",
        "en": "🚫 <b>Banned {uid}!</b>",
        "vi": "🚫 <b>Đã cấm {uid}!</b>",
        "hi": "🚫 <b>{uid} प्रतिबंधित!</b>",
    },

    "broadcast_ask": {
        "ar": "📢 أرسل الرسالة:",
        "en": "📢 Send message:",
        "vi": "📢 Gửi tin nhắn:",
        "hi": "📢 संदेश भेजें:",
    },

    "broadcast_done": {
        "ar": "📢 <b>تم البث!</b>\n\n✅ نجح: <b>{ok}</b>\n❌ فشل: <b>{fail}</b>",
        "en": "📢 <b>Done!</b>\n\n✅ Success: <b>{ok}</b>\n❌ Failed: <b>{fail}</b>",
        "vi": "📢 <b>Xong!</b>\n\n✅ Thành công: <b>{ok}</b>\n❌ Thất bại: <b>{fail}</b>",
        "hi": "📢 <b>पूरा!</b>\n\n✅ सफल: <b>{ok}</b>\n❌ विफल: <b>{fail}</b>",
    },

    "backup_ready": {
        "ar": "💾 <b>النسخة جاهزة!</b>",
        "en": " <b>Backup ready!</b>",
        "vi": "💾 <b>Sao lưu sẵn sàng!</b>",
        "hi": "💾 <b>बैकअप तैयार!</b>",
    },

    # ═══════════════════════════════════════════════════════════════════
    #  MISC
    # ═══════════════════════════════════════════════════════════════════

    "ratelimited": {
        "ar": " انتظر <b>{sec}</b> ثانية.",
        "en": "⏳ Wait <b>{sec}</b>s.",
        "vi": "⏳ Đợi <b>{sec}</b> giây.",
        "hi": "⏳ <b>{sec}</b> सेकंड रुकें।",
    },

    "ops_exhausted": {
        "ar": (
            "⚠️ <b>انتهت عملياتك اليومية!</b>\n\n"
            "📊 الحد: 15 عملية/يوم\n"
            "💡 عد غداً!"
        ),
        "en": (
            "⚠️ <b>Daily ops exhausted!</b>\n\n"
            "📊 Limit: 15 ops/day\n"
            "💡 Come back tomorrow!"
        ),
        "vi": (
            "⚠️ <b>Hết lượt hôm nay!</b>\n\n"
            "📊 Giới hạn: 15 lượt/ngày\n"
            "💡 Quay lại ngày mai!"
        ),
        "hi": (
            "⚠️ <b>दैनिक सीमा पूरी!</b>\n\n"
            "📊 सीमा: 15 ऑप/दिन\n"
            "💡 कल आएं!"
        ),
    },

    "user_banned": {
        "ar": "⛔️ <b>أنت محظور من هذا البوت.</b>",
        "en": "⛔️ <b>You are banned.</b>",
        "vi": "️ <b>Bạn bị cấm.</b>",
        "hi": "⛔️ <b>आप प्रतिबंधित हैं।</b>",
    },

    "cancel_done": {
        "ar": "✅ تم الإلغاء.",
        "en": "✅ Cancelled.",
        "vi": "✅ Đã huỷ.",
        "hi": "✅ रद्द किया गया।",
    },

    "unknown": {
        "ar": "❓ استخدم /start للبدء",
        "en": "❓ Use /start to begin",
        "vi": "❓ Dùng /start để bắt đầu",
        "hi": "❓ शुरू करने के लिए /start उपयोग करें",
    },

}

def t(user_id: int, key: str, **fmt) -> str:
    """Get translated string with HTML-safe formatting."""
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
