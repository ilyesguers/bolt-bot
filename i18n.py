"""
BOLT ⚡ — Internationalization
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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

    # ═══ HOME ═══════════════════════════════════════════════════════════
    "home_title": {
        "ar": "⚡ **BOLT** — بوت إدارة الحسابات",
        "en": "⚡ **BOLT** — Account Manager",
        "vi": "⚡ **BOLT** — Quản lý tài khoản",
        "hi": "⚡ **BOLT** — खाता प्रबंधक",
    },
    "home_sub": {
        "ar": "🛡️ محمي • مجاني • سريع",
        "en": "🛡️ Protected • Free • Fast",
        "vi": "🛡️ Bảo mật • Miễn phí • Nhanh",
        "hi": "🛡️ सुरक्षित • मुफ़्त • तेज़",
    },
    "home_stats": {
        "ar": "📊 العمليات اليوم: **{ops}/{max}** | 🔥 السلسلة: **{streak}** يوم",
        "en": "📊 Today's ops: **{ops}/{max}** | 🔥 Streak: **{streak}** days",
        "vi": "📊 Hôm nay: **{ops}/{max}** | 🔥 Chuỗi: **{streak}** ngày",
        "hi": "📊 आज: **{ops}/{max}** | 🔥 स्ट्रीक: **{streak}** दिन",
    },
    "home_token_status": {
        "ar": "🔐 التوكن: **{status}**",
        "en": "🔐 Token: **{status}**",
        "vi": "🔐 Token: **{status}**",
        "hi": "🔐 टोकन: **{status}**",
    },
    "token_active": {"ar": "✅ مُفعّل", "en": "✅ Active", "vi": "✅ Hoạt động", "hi": "✅ सक्रिय"},
    "token_none": {"ar": "❌ غير مُضاف", "en": "❌ Not set", "vi": "❌ Chưa thêm", "hi": "❌ नहीं जोड़ा"},
    "home_choose": {
        "ar": "⬇️ اختر من القائمة:",
        "en": "⬇️ Choose:",
        "vi": "⬇️ Chọn:",
        "hi": "⬇️ चुनें:",
    },

    # ═══ BUTTONS ════════════════════════════════════════════════════════
    "btn_tools":     {"ar": "🔧 الأدوات", "en": "🔧 Tools", "vi": "🔧 Công cụ", "hi": "🔧 टूल्स"},
    "btn_add":       {"ar": "➕ إضافة حساب", "en": "➕ Add", "vi": "➕ Thêm", "hi": "➕ जोड़ें"},
    "btn_card":      {"ar": "🃏 بطاقتي", "en": "🃏 My Card", "vi": "🃏 Thẻ", "hi": "🃏 कार्ड"},
    "btn_rewards":   {"ar": "🏆 المكافآت", "en": "🏆 Rewards", "vi": "🏆 Thưởng", "hi": "🏆 इनाम"},
    "btn_daily":     {"ar": "🎁 هدية يومية", "en": "🎁 Daily", "vi": "🎁 Quà", "hi": "🎁 रोज़ाना"},
    "btn_support":   {"ar": "💬 الدعم", "en": "💬 Support", "vi": "💬 Hỗ trợ", "hi": "💬 सहायता"},
    "btn_leaderboard":{"ar": "📊 المتصدرون", "en": "📊 Top", "vi": "📊 Top", "hi": "📊 टॉप"},
    "btn_lang":      {"ar": "🌍 اللغة", "en": "🌍 Lang", "vi": "🌍 Ngôn ngữ", "hi": "🌍 भाषा"},
    "btn_admin":     {"ar": "👑 الإدارة", "en": "👑 Admin", "vi": "👑 Admin", "hi": "👑 एडमिन"},
    "btn_back":      {"ar": "🔙 رجوع", "en": "🔙 Back", "vi": "🔙 Lại", "hi": "🔙 वापस"},
    "btn_home":      {"ar": "🏠 الرئيسية", "en": "🏠 Home", "vi": "🏠 Trang chủ", "hi": "🏠 मुख्य"},
    "btn_cancel":    {"ar": "❌ إلغاء", "en": "❌ Cancel", "vi": "❌ Huỷ", "hi": "❌ रद्द"},

    # ═══ TOOLS ══════════════════════════════════════════════════════════
    "tools_title": {
        "ar": "🔧 **أدوات الحساب**\n\n🛡️ جميع العمليات آمنة ومباشرة\n⬇️ اختر:",
        "en": "🔧 **Account Tools**\n\n🛡️ All ops are safe & direct\n⬇️ Choose:",
        "vi": "🔧 **Công cụ**\n\n🛡️ An toàn & trực tiếp\n⬇️ Chọn:",
        "hi": "🔧 **टूल्स**\n\n🛡️ सुरक्षित & सीधा\n⬇️ चुनें:",
    },
    "btn_nickname":    {"ar": "🎭 تغيير الاسم", "en": "🎭 Name", "vi": "🎭 Tên", "hi": "🎭 नाम"},
    "btn_player_info": {"ar": "👤 معلوماتي", "en": "👤 My Info", "vi": "👤 Info", "hi": "👤 जानकारी"},
    "btn_check_token": {"ar": "🔍 فحص التوكن", "en": "🔍 Check", "vi": "🔍 Kiểm tra", "hi": "🔍 जांच"},
    "btn_bind_info":   {"ar": "📡 الربط", "en": "📡 Bind", "vi": "📡 Liên kết", "hi": "📡 बाइंड"},
    "btn_check_links": {"ar": "🌐 المنصات", "en": "🌐 Links", "vi": "🌐 Liên kết", "hi": "🌐 लिंक"},
    "btn_history":     {"ar": "📋 السجل", "en": "📋 History", "vi": "📋 Lịch sử", "hi": "📋 इतिहास"},

    # ═══ TOKEN ══════════════════════════════════════════════════════════
    "no_token": {
        "ar": "🔐 لم تضف حساباً بعد.\n📩 أرسل **Access Token** :",
        "en": "🔐 No account yet.\n📩 Send **Access Token**:",
        "vi": "🔐 Chưa có tài khoản.\n📩 Gửi **Access Token**:",
        "hi": "🔐 कोई खाता नहीं।\n📩 **Access Token** भेजें:",
    },
    "send_token": {
        "ar": "📩 أرسل **Access Token** الجديد:",
        "en": "📩 Send new **Access Token**:",
        "vi": "📩 Gửi **Access Token** mới:",
        "hi": "📩 नया **Access Token** भेजें:",
    },
    "token_saved": {
        "ar": "🛡️✅ تم حفظ التوكن بأمان!\n\n🔒 مشفر بـ AES-256\n📊 +10 نقاط مكافأة\n\n🎯 اختر عملية من القائمة:",
        "en": "🛡️✅ Token saved securely!\n\n🔒 AES-256 encrypted\n📊 +10 reward points\n\n🎯 Choose an action:",
        "vi": "🛡️✅ Token đã lưu!\n\n🔒 AES-256\n📊 +10 điểm\n\n🎯 Chọn:",
        "hi": "🛡️✅ Token सेव!\n\n🔒 AES-256\n📊 +10 पॉइंट\n\n🎯 चुनें:",
    },
    "token_bad": {
        "ar": "❌ التوكن غير صالح (أقل من 20 حرف أو يحتوي مسافات).",
        "en": "❌ Invalid token (under 20 chars or contains spaces).",
        "vi": "❌ Token không hợp lệ.",
        "hi": "❌ टोकन गलत।",
    },
    "token_valid_msg": {
        "ar": "✅ **التوكن صالح!**\n\n🆔 Open ID: `{oid}`\n📅 ينتهي: {expires}",
        "en": "✅ **Token valid!**\n\n🆔 Open ID: `{oid}`\n📅 Expires: {expires}",
        "vi": "✅ **Token hợp lệ!**\n\n🆔 Open ID: `{oid}`\n📅 Hết hạn: {expires}",
        "hi": "✅ **टोकन मान्य!**\n\n🆔 Open ID: `{oid}`\n📅 समाप्ति: {expires}",
    },
    "token_invalid": {
        "ar": "❌ التوكن غير صالح أو منتهي الصلاحية.",
        "en": "❌ Token invalid or expired.",
        "vi": "❌ Token không hợp lệ hoặc hết hạn.",
        "hi": "❌ टोकन अमान्य या समाप्त।",
    },
    "token_revoke_confirm": {
        "ar": "⚠️ هل تريد فعلاً حذف التوكن من البوت؟\nسيتم تشفيره ولن يمكن استرجاعه.",
        "en": "⚠️ Really delete token from bot?\nIt will be unrecoverable.",
        "vi": "⚠️ Xóa token khỏi bot?",
        "hi": "⚠️ टोकन हटाएं?",
    },
    "token_revoked": {
        "ar": "✅ تم حذف التوكن بنجاح!",
        "en": "✅ Token deleted!",
        "vi": "✅ Token đã xoá!",
        "hi": "✅ टोकन हटाया!",
    },

    # ═══ OPERATIONS ═════════════════════════════════════════════════════
    "send_new_name": {
        "ar": "🎭 أرسل **الاسم الجديد** (2-18 حرف):",
        "en": "🎭 Send **new name** (2-18 chars):",
        "vi": "🎭 Gửi **tên mới** (2-18 ký tự):",
        "hi": "🎭 **नया नाम** भेजें (2-18):",
    },
    "loading": {
        "ar": "⏳ جاري...",
        "en": "⏳ Loading...",
        "vi": "⏳ Đang xử lý...",
        "hi": "⏳ लोड...",
    },
    "name_changed": {
        "ar": "✅ تم تغيير الاسم إلى: **{name}**\n\n📊 +5 نقاط!",
        "en": "✅ Name changed to: **{name}**\n\n📊 +5 points!",
        "vi": "✅ Tên đã đổi: **{name}**\n\n📊 +5 điểm!",
        "hi": "✅ नाम बदला: **{name}**\n\n📊 +5 पॉइंट!",
    },
    "name_invalid": {
        "ar": "❌ {reason}",
        "en": "❌ {reason}",
        "vi": "❌ {reason}",
        "hi": "❌ {reason}",
    },

    # ═══ PLAYER INFO ════════════════════════════════════════════════════
    "player_info_card": {
        "ar": "👤 **بطاقة اللاعب**\n\n🆔 UID: `{uid}`\n👤 الاسم: **{name}**\n📊 المستوى: **{level}**\n🏅 الرتبة: **{rank}**\n\n🔗 Open ID: `{oid}`",
        "en": "👤 **Player Card**\n\n🆔 UID: `{uid}`\n👤 Name: **{name}**\n📊 Level: **{level}**\n🏅 Rank: **{rank}**\n\n🔗 Open ID: `{oid}`",
        "vi": "👤 **Thẻ người chơi**\n\n🆔 UID: `{uid}`\n👤 Tên: **{name}**\n📊 Level: **{level}**\n🏅 Rank: **{rank}**",
        "hi": "👤 **खिलाड़ी कार्ड**\n\n🆔 UID: `{uid}`\n👤 नाम: **{name}**\n📊 Level: **{level}**\n🏅 Rank: **{rank}**",
    },
    "player_info_basic": {
        "ar": "👤 **معلومات الحساب**\n\n🔗 Open ID: `{oid}`",
        "en": "👤 **Account Info**\n\n🔗 Open ID: `{oid}`",
        "vi": "👤 **Thông tin**\n\n🔗 Open ID: `{oid}`",
        "hi": "👤 **जानकारी**\n\n🔗 Open ID: `{oid}`",
    },

    # ═══ BIND / LINKS ═══════════════════════════════════════════════════
    "bind_info_title": {
        "ar": "📡 **معلومات الربط**",
        "en": "📡 **Bind Info**",
        "vi": "📡 **Liên kết**",
        "hi": "📡 **बाइंड जानकारी**",
    },
    "links_title": {
        "ar": "🌐 **الحسابات المرتبطة**",
        "en": "🌐 **Linked Accounts**",
        "vi": "🌐 **Tài khoản liên kết**",
        "hi": "🌐 **जुड़े खाते**",
    },
    "no_links": {
        "ar": "📭 لا توجد حسابات مرتبطة.",
        "en": "📭 No linked accounts.",
        "vi": "📭 Không có liên kết.",
        "hi": "📭 कोई लिंक नहीं।",
    },

    # ═══ REWARDS ════════════════════════════════════════════════════════
    "daily_claimed": {
        "ar": "🎁✅ حصلت على **+{pts} نقطة**!\n\n🔥 السلسلة: **{streak}** يوم\n📊 المستوى: {level}\n\n💡 عد غداً لمكافأة أكبر!",
        "en": "🎁✅ Got **+{pts} points**!\n\n🔥 Streak: **{streak}** days\n📊 Level: {level}\n\n💡 Come back tomorrow for more!",
        "vi": "🎁✅ **+{pts} điểm**!\n\n🔥 Chuỗi: **{streak}** ngày\n💡 Quay lại ngày mai!",
        "hi": "🎁✅ **+{pts} पॉइंट**!\n\n🔥 स्ट्रीक: **{streak}** दिन\n💡 कल फिर आएं!",
    },
    "daily_already": {
        "ar": "⏰ حصلت على هديتك اليوم!\nعد غداً للمكافأة التالية.",
        "en": "⏰ Already claimed today!\nCome back tomorrow.",
        "vi": "⏰ Đã nhận hôm nay!\nQuay lại ngày mai.",
        "hi": "⏰ आज मिल गया!\nकल आएं।",
    },

    # ═══ LEADERBOARD ════════════════════════════════════════════════════
    "leaderboard_title": {
        "ar": "🏆 **لوحة المتصدرين — BOLT**",
        "en": "🏆 **Leaderboard — BOLT**",
        "vi": "🏆 **Bảng xếp hạng — BOLT**",
        "hi": "🏆 **लीडरबोर्ड — BOLT**",
    },
    "leaderboard_empty": {
        "ar": "📭 لا يوجد متصدرون بعد. كن الأول!",
        "en": "📭 No leaders yet. Be the first!",
        "vi": "📭 Chưa có ai. Hãy là người đầu tiên!",
        "hi": "📭 कोई नहीं। पहले बनें!",
    },
    "leaderboard_you": {
        "ar": "\n\n⭐ **موقعك:** #{pos} — {pts} نقطة",
        "en": "\n\n⭐ **Your rank:** #{pos} — {pts} points",
        "vi": "\n\n⭐ **Bạn:** #{pos} — {pts} điểm",
        "hi": "\n\n⭐ **आप:** #{pos} — {pts} पॉइंट",
    },

    # ═══ MY CARD ════════════════════════════════════════════════════════
    "my_card_title": {
        "ar": "🃏 **بطاقتي — BOLT**\n\n👤 الاسم: **{name}**\n🆔 المعرف: `{uid}`\n📅 انضممت: {joined}",
        "en": "🃏 **My Card — BOLT**\n\n👤 Name: **{name}**\n🆔 ID: `{uid}`\n📅 Joined: {joined}",
        "vi": "🃏 **Thẻ — BOLT**\n\n👤 Tên: **{name}**\n🆔 ID: `{uid}`\n📅 Tham gia: {joined}",
        "hi": "🃏 **कार्ड — BOLT**\n\n👤 नाम: **{name}**\n🆔 ID: `{uid}`\n📅 जुड़े: {joined}",
    },

    # ═══ ACTIVITY HISTORY ═══════════════════════════════════════════════
    "history_title": {
        "ar": "📋 **آخر عملياتك**",
        "en": "📋 **Recent Activity**",
        "vi": "📋 **Hoạt động gần đây**",
        "hi": "📋 **हाल की गतिविधि**",
    },
    "history_empty": {
        "ar": "📭 لا توجد عمليات بعد.",
        "en": "📭 No activity yet.",
        "vi": "📭 Chưa có gì.",
        "hi": "📭 कुछ नहीं।",
    },

    # ═══ SUPPORT ════════════════════════════════════════════════════════
    "support_ask_subject": {
        "ar": "📝 اكتب عنوان المشكلة:",
        "en": "📝 Subject:",
        "vi": "📝 Tiêu đề:",
        "hi": "📝 विषय:",
    },
    "support_ask_message": {
        "ar": "📝 اشرح مشكلتك:",
        "en": "📝 Describe the issue:",
        "vi": "📝 Mô tả vấn đề:",
        "hi": "📝 समस्या बताएं:",
    },
    "support_created": {
        "ar": "✅ تم إنشاء التذكرة **#{tid}**\n💬 سنرد قريباً!",
        "en": "✅ Ticket **#{tid}** created!\n💬 Reply soon!",
        "vi": "✅ Vé **#{tid}** tạo!\n💬 Sắp phản hồi!",
        "hi": "✅ टिकट **#{tid}**!\n💬 जल्द उत्तर!",
    },

    # ═══ LANGUAGE ═══════════════════════════════════════════════════════
    "lang_title": {
        "ar": "🌍 اختر اللغة:",
        "en": "🌍 Choose language:",
        "vi": "🌍 Chọn ngôn ngữ:",
        "hi": "🌍 भाषा:",
    },
    "lang_set": {
        "ar": "✅ تم تغيير اللغة!",
        "en": "✅ Language changed!",
        "vi": "✅ Đổi ngôn ngữ!",
        "hi": "✅ भाषा बदली!",
    },

    # ═══ ADMIN ══════════════════════════════════════════════════════════
    "admin_title": {
        "ar": "👑 **لوحة الإدارة — BOLT**",
        "en": "👑 **Admin Panel — BOLT**",
        "vi": "👑 **Admin — BOLT**",
        "hi": "👑 **एडमिन — BOLT**",
    },
    "not_auth": {
        "ar": "⛔️ غير مصرح!",
        "en": "⛔️ Unauthorized!",
        "vi": "⛔️ Không có quyền!",
        "hi": "⛔️ नहीं!",
    },
    "btn_stats":     {"ar": "📈 إحصائيات", "en": "📈 Stats", "vi": "📈 Thống kê", "hi": "📈 आँकड़े"},
    "btn_broadcast": {"ar": "📢 بث", "en": "📢 Broadcast", "vi": "📢 Phát", "hi": "📢 प्रसारण"},
    "btn_backup":    {"ar": "💾 نسخة", "en": "💾 Backup", "vi": "💾 Sao lưu", "hi": "💾 बैकअप"},
    "btn_ban":       {"ar": "🚫 حظر", "en": "🚫 Ban", "vi": "🚫 Cấm", "hi": "🚫 प्रतिबंध"},
    "btn_audit":     {"ar": "📋 السجل", "en": "📋 Audit", "vi": "📋 Nhật ký", "hi": "📋 लॉग"},
    "btn_tickets":   {"ar": "💬 تذاكر", "en": "💬 Tickets", "vi": "💬 Vé", "hi": "💬 टिकट"},
    "btn_sec_stats": {"ar": "🛡️ الحماية", "en": "🛡️ Security", "vi": "🛡️ Bảo mật", "hi": "🛡️ सुरक्षा"},

    "stats_text": {
        "ar": "📊 **إحصائيات BOLT**\n\n👥 المستخدمون: **{users}**\n🔐 لديهم توكن: **{with_token}**\n⚡ إجمالي العمليات: **{ops}**\n🏆 أعلى مستوى: **{max_level}**",
        "en": "📊 **BOLT Stats**\n\n👥 Users: **{users}**\n🔐 With token: **{with_token}**\n⚡ Total ops: **{ops}**\n🏆 Max level: **{max_level}**",
        "vi": "📊 **BOLT Stats**\n\n👥 Users: **{users}**\n🔐 With token: **{with_token}**",
        "hi": "📊 **BOLT Stats**\n\n👥 Users: **{users}**\n🔐 With token: **{with_token}**",
    },
    "sec_stats": {
        "ar": "🛡️ **إحصائيات الحماية**\n\n📋 سجلات: **{total_logs}**\n🚫 محظورون: **{banned}**\n⚠️ تنبيهات: **{abuse}**\n⏱ آخر 24 ساعة: **{last24}**",
        "en": "🛡️ **Security**\n\n📋 Logs: **{total_logs}**\n🚫 Banned: **{banned}**\n⚠️ Flags: **{abuse}**\n⏱ Last 24h: **{last24}**",
        "vi": "🛡️ **Bảo mật**\n\n📋 Logs: **{total_logs}**\n🚫 Banned: **{banned}**",
        "hi": "🛡️ **सुरक्षा**\n\n📋 Logs: **{total_logs}**\n🚫 Banned: **{banned}**",
    },
    "broadcast_ask": {
        "ar": "📢 أرسل الرسالة:",
        "en": "📢 Send message:",
        "vi": "📢 Gửi tin nhắn:",
        "hi": "📢 संदेश:",
    },
    "broadcast_done": {
        "ar": "📢 تم!\n✅ نجح: **{ok}**\n❌ فشل: **{fail}**",
        "en": "📢 Done!\n✅ Success: **{ok}**\n❌ Failed: **{fail}**",
        "vi": "📢 Xong!\n✅ OK: **{ok}**\n❌ Fail: **{fail}**",
        "hi": "📢 पूरा!\n✅ OK: **{ok}**\n❌ Fail: **{fail}**",
    },
    "backup_ready": {
        "ar": "💾 النسخة جاهزة!",
        "en": "💾 Backup ready!",
        "vi": "💾 Sao lưu sẵn sàng!",
        "hi": "💾 बैकअप तैयार!",
    },
    "ban_ask_id": {
        "ar": "🚫 أرسل معرف المستخدم:",
        "en": "🚫 Send user ID:",
        "vi": "🚫 Gửi user ID:",
        "hi": "🚫 यूज़र ID:",
    },
    "ban_done": {
        "ar": "🚫 تم حظر **{uid}**!",
        "en": "🚫 Banned **{uid}**!",
        "vi": "🚫 Đã cấm **{uid}**!",
        "hi": "🚫 **{uid}** प्रतिबंधित!",
    },

    # ═══ MISC ═══════════════════════════════════════════════════════════
    "ratelimited": {
        "ar": "⏳ انتظر **{sec}** ثانية.",
        "en": "⏳ Wait **{sec}**s.",
        "vi": "⏳ Đợi **{sec}**s.",
        "hi": "⏳ **{sec}** सेकंड रुकें।",
    },
    "ops_exhausted": {
        "ar": "⚠️ انتهت عملياتك اليومية! عد غداً.",
        "en": "⚠️ Daily ops exhausted! Come back tomorrow.",
        "vi": "⚠️ Hết lượt hôm nay! Quay lại ngày mai.",
        "hi": "⚠️ दैनिक सीमा! कल आएं।",
    },
    "user_banned": {
        "ar": "⛔️ أنت محظور من هذا البوت.",
        "en": "⛔️ You are banned.",
        "vi": "⛔️ Bạn bị cấm.",
        "hi": "⛔️ प्रतिबंधित।",
    },
    "cancel_done": {
        "ar": "✅ تم الإلغاء. /start للعودة.",
        "en": "✅ Cancelled. /start to return.",
        "vi": "✅ Huỷ. /start để về.",
        "hi": "✅ रद्द। /start वापस।",
    },
    "unknown": {
        "ar": "❓ /start للبدء",
        "en": "❓ /start to begin",
        "vi": "❓ /start để bắt đầu",
        "hi": "❓ /start शुरू करें",
    },
    "success": {
        "ar": "✅ تمت العملية!",
        "en": "✅ Done!",
        "vi": "✅ Xong!",
        "hi": "✅ हो गया!",
    },
    "error_generic": {
        "ar": "❌ حدث خطأ. حاول مرة أخرى.",
        "en": "❌ Error occurred. Try again.",
        "vi": "❌ Lỗi. Thử lại.",
        "hi": "❌ त्रुटि। फिर से।",
    },
    "welcome_new": {
        "ar": "⚡ **أهلاً بك في BOLT!** 🎉\n\n🛡️ بوت مجاني 100% لإدارة حساباتك\n🔐 توكنك مشفر ولا أحد يستطيع الوصول إليه\n🏆 اربح نقاط مع كل عملية\n🎁 هدية يومية مجانية\n\n⬇️ ابدأ بإضافة حسابك:",
        "en": "⚡ **Welcome to BOLT!** 🎉\n\n🛡️ 100% free account manager\n🔐 Token encrypted, no one can access it\n🏆 Earn points with every action\n🎁 Free daily reward\n\n⬇️ Start by adding your account:",
        "vi": "⚡ **Chào mừng đến BOLT!** 🎉\n\n🛡️ Miễn phí 100%\n🔐 Token mã hóa\n🏆 Kiếm điểm\n🎁 Quà hàng ngày\n\n⬇️ Bắt đầu:",
        "hi": "⚡ **BOLT में स्वागत!** 🎉\n\n🛡️ 100% मुफ़्त\n🔐 टोकन एन्क्रिप्टेड\n🏆 पॉइंट कमाएं\n🎁 रोज़ाना इनाम\n\n⬇️ शुरू करें:",
    },
}

def t(user_id: int, key: str, **fmt) -> str:
    """Get translated string."""
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
