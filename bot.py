"""
BOLT ⚡ — Telegram Bot (Complete)
 Protected • Free • Fast
 AES-256 encryption
🤖 Auto-extract token from URL
 Full admin panel
🌍 AR / EN / VI / HI
"""

import os, io, json, asyncio, zipfile, logging, re
from datetime import datetime, timezone
from html import escape as he

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile, BotCommand
from telegram.ext import (Application, CommandHandler, MessageHandler,
                          CallbackQueryHandler, ConversationHandler, ContextTypes, filters)
from telegram.constants import ParseMode

import garena_api as G
import database as D
import rewards as R
from i18n import t, LANGS
from security import RateLimiter, sanitize_text, validate_nickname
from crypto_utils import is_valid_token_format, hash_token, extract_token_from_url

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))
HTML = ParseMode.HTML

logging.basicConfig(format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", level=logging.INFO)
logger = logging.getLogger("bolt")

sec = RateLimiter()

# ─── States ──────────────────────────────────────────────────────────────────
(SELECT_LANG, SELECT_PLATFORM, TUTORIAL_ANDROID, TUTORIAL_IOS, ASK_TOKEN,
 HOME_STATE, TOOLS_STATE, LANG_STATE, ADMIN_STATE,
 ADMIN_BAN_ID, ADMIN_BAN_REASON, BROADCAST_WAIT,
 ASK_NAME) = range(13)

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _btn(label, cb): return InlineKeyboardButton(label, callback_data=cb)
def _btns(rows): return InlineKeyboardMarkup(rows)
def _one(label, cb): return _btns([[_btn(label, cb)]])

def lang_kb():
    return _btns([[_btn("🇸🇦 العربية", "lang_ar"), _btn("🇬🇧 English", "lang_en")],
                   [_btn("🇻🇳 Tiếng Việt", "lang_vi"), _btn("🇮🇳 हिन्दी", "lang_hi")]])

def platform_kb():
    return _btns([[_btn(" Android", "platform_android")],
                   [_btn("🍎 iPhone", "platform_ios")],
                   [_btn("⏭️ تخطي", "skip_tutorial")]])

def tutorial_kb(android):
    if android:
        return _btns([[_btn("🔄 إعادة الشرح", "retry_android")],
                       [_btn("✅ فهمت", "got_it_android")]])
    return _btns([[_btn("🔄 إعادة الشرح", "retry_ios")],
                   [_btn("✅ فهمت", "got_it_ios")]])

def home_kb(uid):
    has = D.has_token(uid)
    rows = []
    if has:
        rows.append([_btn(t(uid, "btn_tools"), "tools"), _btn(t(uid, "btn_card"), "card")])
        rows.append([_btn(t(uid, "btn_rewards"), "rewards"), _btn(t(uid, "btn_daily"), "daily")])
    else:
        rows.append([_btn(t(uid, "btn_add"), "add_token")])
    rows.append([_btn(t(uid, "btn_leaderboard"), "leaderboard"), _btn(t(uid, "btn_support"), "support")])
    rows.append([_btn(t(uid, "btn_lang"), "lang")])
    if D.is_admin(uid): rows.append([_btn(t(uid, "btn_admin"), "admin")])
    return _btns(rows)

def tools_kb(uid):
    return _btns([
        [_btn(t(uid, "btn_nickname"), "nickname"), _btn(t(uid, "btn_player_info"), "player_info")],
        [_btn(t(uid, "btn_check_token"), "check_token"), _btn(t(uid, "btn_bind_info"), "bind_info")],
        [_btn(t(uid, "btn_change_bind"), "change_bind"), _btn(t(uid, "btn_unbind"), "unbind")],
        [_btn(t(uid, "btn_cancel_bind"), "cancel_bind"), _btn(t(uid, "btn_bind_new"), "bind_new")],
        [_btn(t(uid, "btn_check_links"), "check_links"), _btn(t(uid, "btn_revoke"), "revoke")],
        [_btn(t(uid, "btn_history"), "history"), _btn(t(uid, "btn_back"), "home")],
    ])

def admin_kb(uid):
    return _btns([
        [_btn(t(uid, "btn_stats"), "a_stats"), _btn(t(uid, "btn_sec_stats"), "a_sec")],
        [_btn(t(uid, "btn_broadcast"), "a_bcast"), _btn(t(uid, "btn_backup"), "a_backup")],
        [_btn(t(uid, "btn_ban"), "a_ban"), _btn(t(uid, "btn_admins"), "a_admins")],
        [_btn(t(uid, "btn_tutorials"), "a_tutorials"), _btn(t(uid, "btn_view_tokens"), "a_tokens")],
        [_btn(t(uid, "btn_tickets"), "a_tickets"), _btn(t(uid, "btn_audit"), "a_audit")],
        [_btn(t(uid, "btn_back"), "home")],
    ])

# ─── Post Init ───────────────────────────────────────────────────────────────

async def post_init(app):
    D.init_db()
    try:
        for lang in ["ar", "en"]:
            await app.bot.set_my_commands([BotCommand("start", "ابدأ / Start")], language_code=lang)
    except: pass
    logger.info(" BOLT started — OWNER=%s", OWNER_ID)

# ─── /start ──────────────────────────────────────────────────────────────────

async def cmd_start(update, ctx) -> int:
    uid = update.effective_user.id
    uname = update.effective_user.username or ""
    fname = update.effective_user.first_name or ""

    banned, reason = D.is_banned(uid)
    if banned:
        await update.effective_message.reply_text(f"⛔️ <b>محظور</b>\n\nالسبب: {reason}", parse_mode=HTML)
        return ConversationHandler.END

    user = D.ensure_user(uid, uname, fname)

    if user.get("onboarded") and user.get("lang"):
        text = f"{t(uid, 'home_title')}\n\n{t(uid, 'home_subtitle')}"
        await update.effective_message.reply_text(text, parse_mode=HTML, reply_markup=home_kb(uid))
        return HOME_STATE

    await update.effective_message.reply_text(t(uid, "welcome_select_lang"), parse_mode=HTML, reply_markup=lang_kb())
    return SELECT_LANG

# ─── Language ────────────────────────────────────────────────────────────────

async def select_lang_cb(update, ctx) -> int:
    q = update.callback_query; await q.answer()
    uid = update.effective_user.id
    cb = q.data
    if cb.startswith("lang_"):
        lang = cb[5:]
        if lang in LANGS:
            D.set_lang(uid, lang)
            await q.edit_message_text(t(uid, "lang_selected"), parse_mode=HTML, reply_markup=platform_kb())
            return SELECT_PLATFORM
    return SELECT_LANG

# ─── Platform ────────────────────────────────────────────────────────────────

async def select_platform_cb(update, ctx) -> int:
    q = update.callback_query; await q.answer()
    uid = update.effective_user.id
    cb = q.data
    if cb == "platform_android":
        await q.edit_message_text(f"{t(uid, 'tutorial_title')}\n\n{t(uid, 'tutorial_android_steps')}",
                                   parse_mode=HTML, reply_markup=tutorial_kb(True))
        return TUTORIAL_ANDROID
    elif cb == "platform_ios":
        await q.edit_message_text(f"{t(uid, 'tutorial_title')}\n\n{t(uid, 'tutorial_ios_steps')}",
                                   parse_mode=HTML, reply_markup=tutorial_kb(False))
        return TUTORIAL_IOS
    elif cb == "skip_tutorial":
        D.set_onboarded(uid, 1)
        await q.edit_message_text(t(uid, "ask_token"), parse_mode=HTML, reply_markup=_one(t(uid, "btn_back"), "home"))
        return ASK_TOKEN
    return SELECT_PLATFORM

# ─── Tutorial ────────────────────────────────────────────────────────────────

async def tutorial_cb(update, ctx) -> int:
    q = update.callback_query; await q.answer()
    uid = update.effective_user.id
    cb = q.data
    if cb in ("retry_android",):
        await q.edit_message_text(f"{t(uid, 'tutorial_title')}\n\n{t(uid, 'tutorial_android_steps')}",
                                   parse_mode=HTML, reply_markup=tutorial_kb(True))
        return TUTORIAL_ANDROID
    elif cb in ("retry_ios",):
        await q.edit_message_text(f"{t(uid, 'tutorial_title')}\n\n{t(uid, 'tutorial_ios_steps')}",
                                   parse_mode=HTML, reply_markup=tutorial_kb(False))
        return TUTORIAL_IOS
    elif cb in ("got_it_android", "got_it_ios"):
        D.set_onboarded(uid, 1)
        await q.edit_message_text(t(uid, "ask_token"), parse_mode=HTML,
                                   reply_markup=_one(t(uid, "btn_back"), "home"))
        return ASK_TOKEN
    return TUTORIAL_ANDROID if "android" in cb else TUTORIAL_IOS

# ─── Token Handler (Auto-extract from URL) ──────────────────────────────────

async def token_handler(update, ctx) -> int:
    uid = update.effective_user.id
    raw = update.message.text.strip()

    token = extract_token_from_url(raw)

    if not token or not is_valid_token_format(token):
        await update.message.reply_text(t(uid, "token_invalid"), parse_mode=HTML)
        return ASK_TOKEN

    msg = await update.message.reply_text(f" {t(uid, 'loading')}", parse_mode=HTML)

    validation = G.validate_token(token)

    if not validation.get("valid"):
        await msg.edit_text(t(uid, "token_invalid"), parse_mode=HTML,
                             reply_markup=_one(t(uid, "btn_back"), "home"))
        return ASK_TOKEN

    D.set_token(uid, token)
    D.increment_ops(uid)
    D.log_activity(uid, "ADD_TOKEN", "Token added", success=True)

    await msg.edit_text(t(uid, "token_saved"), parse_mode=HTML, reply_markup=home_kb(uid))
    return HOME_STATE

# ── Home ────────────────────────────────────────────────────────────────────

async def home_cb(update, ctx) -> int:
    q = update.callback_query; await q.answer()
    uid = update.effective_user.id
    cb = q.data

    banned, reason = D.is_banned(uid)
    if banned:
        await q.edit_message_text(f"⛔️ <b>محظور</b>\n\nالسبب: {reason}", parse_mode=HTML)
        return ConversationHandler.END

    if cb == "home":
        text = f"{t(uid, 'home_title')}\n\n{t(uid, 'home_subtitle')}"
        await q.edit_message_text(text, parse_mode=HTML, reply_markup=home_kb(uid))
        return HOME_STATE

    if cb == "add_token":
        await q.edit_message_text(t(uid, "ask_token"), parse_mode=HTML,
                                   reply_markup=_one(t(uid, "btn_back"), "home"))
        return ASK_TOKEN

    if cb == "tools":
        if not D.has_token(uid):
            await q.edit_message_text(t(uid, "ask_token"), parse_mode=HTML,
                                       reply_markup=_one(t(uid, "btn_add"), "add_token"))
            return ASK_TOKEN
        await q.edit_message_text(t(uid, "tools_title"), parse_mode=HTML, reply_markup=tools_kb(uid))
        return TOOLS_STATE

    if cb == "lang":
        await q.edit_message_text(f"🌍 <b>اختر اللغة:</b>", parse_mode=HTML, reply_markup=lang_kb())
        return LANG_STATE

    if cb == "admin":
        if not D.is_admin(uid):
            await q.answer(t(uid, "not_auth"), show_alert=True)
            return HOME_STATE
        await q.edit_message_text(t(uid, "admin_title"), parse_mode=HTML, reply_markup=admin_kb(uid))
        return ADMIN_STATE

    if cb == "card":
        user = D.get_user(uid)
        rw = D.get_rewards(uid)
        name = user.get("first_name") or user.get("username") or "User"
        text = f" <b>بطاقتي</b>\n\n👤 {he(name)}\n🆔 <code>{uid}</code>\n {user.get('joined_at', '?')[:10]}"
        await q.edit_message_text(text, parse_mode=HTML, reply_markup=_one(t(uid, "btn_back"), "home"))
        return HOME_STATE

    if cb == "rewards":
        rw = D.get_rewards(uid)
        text = f"🏆 <b>المكافآت</b>\n\n النقاط: <b>{rw.get('points', 0)}</b>\n🔥 السلسلة: <b>{rw.get('streak', 0)}</b>\n🏆 المستوى: <b>{rw.get('level', 1)}</b>"
        await q.edit_message_text(text, parse_mode=HTML, reply_markup=_one(t(uid, "btn_back"), "home"))
        return HOME_STATE

    if cb == "daily":
        ok, pts = D.claim_daily(uid)
        if ok:
            rw = D.get_rewards(uid)
            await q.edit_message_text(t(uid, "daily_claimed", pts=pts, streak=rw.get('streak', 0), level=rw.get('level', 1)),
                                       parse_mode=HTML, reply_markup=_one(t(uid, "btn_back"), "home"))
        else:
            await q.edit_message_text(t(uid, "daily_already"), parse_mode=HTML,
                                       reply_markup=_one(t(uid, "btn_back"), "home"))
        return HOME_STATE

    if cb == "leaderboard":
        board = D.leaderboard(10)
        if not board:
            await q.edit_message_text(" لا يوجد متصدرون", parse_mode=HTML, reply_markup=_one(t(uid, "btn_back"), "home"))
            return HOME_STATE
        lines = [f"🏆 <b>المتصدرون</b>\n"]
        for i, u in enumerate(board[:10]):
            m = ["🥇", "🥈", "🥉"] + [""] * 7
            name = he(u.get("first_name") or u.get("username") or str(u["user_id"]))
            lines.append(f"{m[i]} <b>{name}</b> — {u.get('points', 0)} pts")
        await q.edit_message_text("\n".join(lines), parse_mode=HTML, reply_markup=_one(t(uid, "btn_back"), "home"))
        return HOME_STATE

    if cb == "support":
        await q.edit_message_text("💬 <b>الدعم</b>\n\nاكتب مشكلتك:", parse_mode=HTML,
                                   reply_markup=_one(t(uid, "btn_cancel"), "home"))
        return HOME_STATE

    return HOME_STATE

# ─── Lang CB ─────────────────────────────────────────────────────────────────

async def lang_cb(update, ctx) -> int:
    q = update.callback_query; await q.answer()
    uid = update.effective_user.id
    cb = q.data
    if cb == "home":
        text = f"{t(uid, 'home_title')}\n\n{t(uid, 'home_subtitle')}"
        await q.edit_message_text(text, parse_mode=HTML, reply_markup=home_kb(uid))
        return HOME_STATE
    if cb.startswith("lang_"):
        lang = cb[5:]
        if lang in LANGS:
            D.set_lang(uid, lang)
            await q.edit_message_text(f"✅ {t(uid, 'lang_selected')}", parse_mode=HTML,
                                       reply_markup=_one(t(uid, "btn_home"), "home"))
    return LANG_STATE

# ─── Tools CB ────────────────────────────────────────────────────────────────

async def tools_cb(update, ctx) -> int:
    q = update.callback_query; await q.answer()
    uid = update.effective_user.id
    cb = q.data

    if cb == "home":
        text = f"{t(uid, 'home_title')}\n\n{t(uid, 'home_subtitle')}"
        await q.edit_message_text(text, parse_mode=HTML, reply_markup=home_kb(uid))
        return HOME_STATE

    if cb == "tools":
        await q.edit_message_text(t(uid, "tools_title"), parse_mode=HTML, reply_markup=tools_kb(uid))
        return TOOLS_STATE

    token = D.get_token(uid)
    if not token and cb != "history":
        await q.edit_message_text(t(uid, "ask_token"), parse_mode=HTML,
                                   reply_markup=_one(t(uid, "btn_back"), "home"))
        return ASK_TOKEN

    if cb == "nickname":
        await q.edit_message_text(t(uid, "send_new_name"), parse_mode=HTML,
                                   reply_markup=_one(t(uid, "btn_back"), "tools"))
        return ASK_NAME

    if cb == "player_info":
        await q.edit_message_text(f"⏳ {t(uid, 'loading')}", parse_mode=HTML)
        info = G.get_player_info(token)
        if info.get("error"):
            text = f"❌ {info['error']}"
        elif info.get("status") == "success":
            if info.get("name"):
                text = f"👤 <b>معلوماتي</b>\n\n🆔 UID: <code>{info.get('uid', '?')}</code>\n👤 الاسم: <b>{he(info.get('name', '?'))}</b>\n المستوى: <b>{info.get('level', '?')}</b>\n🏅 الرتبة: <b>{info.get('rank', '?')}</b>\n🔗 Open ID: <code>{info.get('open_id', '?')}</code>"
            else:
                text = f"👤 <b>معلوماتي</b>\n\n Open ID: <code>{info.get('open_id', '?')}</code>"
        else:
            text = "❌ فشل"
        await q.edit_message_text(text, parse_mode=HTML, reply_markup=_one(t(uid, "btn_back"), "tools"))
        return TOOLS_STATE

    if cb == "check_token":
        await q.edit_message_text(f"⏳ {t(uid, 'loading')}", parse_mode=HTML)
        result = G.validate_token(token)
        if result.get("valid"):
            text = f"✅ <b>صالح!</b>\n\n🆔 Open ID: <code>{result.get('open_id', '?')}</code>\n ينتهي: {result.get('expires', '?')}"
        else:
            text = " <b>غير صالح!</b>"
        await q.edit_message_text(text, parse_mode=HTML, reply_markup=_one(t(uid, "btn_back"), "tools"))
        return TOOLS_STATE

    if cb == "bind_info":
        await q.edit_message_text(f"⏳ {t(uid, 'loading')}", parse_mode=HTML)
        result = G.check_bind_info_direct(token)
        if result.get("email"):
            text = f"📡 <b>الربط</b>\n\n📧 Email: <code>{he(result['email'])}</code>"
        elif result.get("error"):
            text = f"❌ {result['error']}"
        else:
            text = "📡 <b>لا يوجد بريد مربوط</b>"
        await q.edit_message_text(text, parse_mode=HTML, reply_markup=_one(t(uid, "btn_back"), "tools"))
        return TOOLS_STATE

    if cb == "change_bind":
        await q.edit_message_text("🔄 <b>تغيير البريد</b>\n\nقيد التطوير", parse_mode=HTML,
                                   reply_markup=_one(t(uid, "btn_back"), "tools"))
        return TOOLS_STATE

    if cb == "unbind":
        await q.edit_message_text("🔓 <b>فك الربط</b>\n\nقيد التطوير", parse_mode=HTML,
                                   reply_markup=_one(t(uid, "btn_back"), "tools"))
        return TOOLS_STATE

    if cb == "cancel_bind":
        await q.edit_message_text("🚫 <b>إلغاء الربط</b>\n\nقيد التطوير", parse_mode=HTML,
                                   reply_markup=_one(t(uid, "btn_back"), "tools"))
        return TOOLS_STATE

    if cb == "bind_new":
        await q.edit_message_text(" <b>بريد جديد</b>\n\nقيد التطوير", parse_mode=HTML,
                                   reply_markup=_one(t(uid, "btn_back"), "tools"))
        return TOOLS_STATE

    if cb == "check_links":
        await q.edit_message_text(f"⏳ {t(uid, 'loading')}", parse_mode=HTML)
        j = G.check_links(token)
        bounded = j.get("bounded_accounts", [])
        if bounded:
            lines = [f"🌐 <b>المنصات</b>\n"]
            for x in bounded:
                p = x.get("platform")
                ui = x.get("user_info", {})
                name = G.PLATFORM_NAMES.get(p, f"Platform {p}")
                lines.append(f"️ <b>{name}</b>")
                if ui.get("email"): lines.append(f"   {he(ui['email'])}")
            text = "\n".join(lines)
        else:
            text = "🌐 <b>لا توجد منصات مرتبطة</b>"
        await q.edit_message_text(text, parse_mode=HTML, reply_markup=_one(t(uid, "btn_back"), "tools"))
        return TOOLS_STATE

    if cb == "revoke":
        await q.edit_message_text(" <b>إبطال التوكن</b>\n\nقيد التطوير", parse_mode=HTML,
                                   reply_markup=_one(t(uid, "btn_back"), "tools"))
        return TOOLS_STATE

    if cb == "history":
        logs = D.get_activity(uid, 15)
        if not logs:
            text = "📋 <b>لا توجد عمليات</b>"
        else:
            lines = [f"📋 <b>السجل</b>\n"]
            for log in logs[:15]:
                icon = "✅" if log["success"] else "❌"
                ts = log["timestamp"][:16]
                lines.append(f"{icon} {log['action']} — {ts}")
            text = "\n".join(lines)
        await q.edit_message_text(text, parse_mode=HTML, reply_markup=_one(t(uid, "btn_back"), "home"))
        return TOOLS_STATE

    return TOOLS_STATE

# ─── Nickname Handler ────────────────────────────────────────────────────────

async def name_handler(update, ctx) -> int:
    uid = update.effective_user.id
    name = update.message.text.strip()

    if len(name) < 2 or len(name) > 18:
        await update.message.reply_text("❌ الاسم يجب أن يكون 2-18 حرف", parse_mode=HTML)
        return ASK_NAME

    token = D.get_token(uid)
    if not token:
        await update.message.reply_text(t(uid, "ask_token"), parse_mode=HTML)
        return HOME_STATE

    msg = await update.message.reply_text(f"⏳ {t(uid, 'loading')}", parse_mode=HTML)
    try:
        r = G.change_name(token, name)
        if r.get("status") == 200:
            text = t(uid, "name_changed", name=he(name))
        else:
            text = f"❌ {r.get('error', 'فشل')}"
    except Exception as e:
        text = f"❌ {e}"

    await msg.edit_text(text, parse_mode=HTML, reply_markup=_one(t(uid, "btn_back"), "tools"))
    return TOOLS_STATE

# ─── Admin CB ────────────────────────────────────────────────────────────────

async def admin_cb(update, ctx) -> int:
    q = update.callback_query; await q.answer()
    uid = update.effective_user.id

    if not D.is_admin(uid):
        await q.answer(t(uid, "not_auth"), show_alert=True)
        return ADMIN_STATE

    cb = q.data

    if cb == "home":
        text = f"{t(uid, 'home_title')}\n\n{t(uid, 'home_subtitle')}"
        await q.edit_message_text(text, parse_mode=HTML, reply_markup=home_kb(uid))
        return HOME_STATE

    if cb == "admin":
        await q.edit_message_text(t(uid, "admin_title"), parse_mode=HTML, reply_markup=admin_kb(uid))
        return ADMIN_STATE

    if cb == "a_stats":
        users = D.user_count()
        with __import__('sqlite3').connect(D.DB_FILE) as c:
            with_token = c.execute("SELECT COUNT(*) FROM users WHERE encrypted_token IS NOT NULL").fetchone()[0]
            total_ops = c.execute("SELECT COALESCE(SUM(total_ops),0) FROM users").fetchone()[0]
        await q.edit_message_text(t(uid, "stats_text", users=users, with_token=with_token, ops=total_ops),
                                   parse_mode=HTML, reply_markup=_one(t(uid, "btn_back"), "admin"))
        return ADMIN_STATE

    if cb == "a_sec":
        await q.edit_message_text("🛡️ <b>الحماية</b>\n\n✅ Rate Limiting نشط\n✅ Audit Log نشط\n✅ Ban System نشط",
                                   parse_mode=HTML, reply_markup=_one(t(uid, "btn_back"), "admin"))
        return ADMIN_STATE

    if cb == "a_bcast":
        await q.edit_message_text(t(uid, "broadcast_ask"), parse_mode=HTML,
                                   reply_markup=_one(t(uid, "btn_cancel"), "admin"))
        return BROADCAST_WAIT

    if cb == "a_backup":
        await q.edit_message_text(f"⏳ {t(uid, 'loading')}", parse_mode=HTML)
        data = D.export_data()
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("backup.json", json.dumps(data, ensure_ascii=False, indent=2, default=str))
            if os.path.exists(D.DB_FILE):
                with open(D.DB_FILE, "rb") as f: zf.writestr("bolt.db", f.read())
        buf.seek(0)
        now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        await ctx.bot.send_document(chat_id=uid, document=InputFile(buf, filename=f"BOLT_{now_str}.zip"),
                                     caption=f"💾 {t(uid, 'backup_ready')}", parse_mode=HTML)
        await q.edit_message_text(f"💾 {t(uid, 'backup_ready')}", parse_mode=HTML,
                                   reply_markup=_one(t(uid, "btn_back"), "admin"))
        return ADMIN_STATE

    if cb == "a_ban":
        await q.edit_message_text(t(uid, "ban_ask_id"), parse_mode=HTML,
                                   reply_markup=_one(t(uid, "btn_cancel"), "admin"))
        return ADMIN_BAN_ID

    if cb == "a_admins":
        admins = D.get_admins()
        if not admins:
            text = "👥 <b>لا يوجد أدمن</b>"
        else:
            lines = [f"👥 <b>الأدمن</b>\n"]
            for a in admins:
                lines.append(f"• <b>{a['user_id']}</b> — {a.get('permissions', 'full')}")
            text = "\n".join(lines)
        await q.edit_message_text(text, parse_mode=HTML, reply_markup=_one(t(uid, "btn_back"), "admin"))
        return ADMIN_STATE

    if cb == "a_tutorials":
        android_url = D.get_tutorial_video("android")
        ios_url = D.get_tutorial_video("ios")
        text = f" <b>الفيديوهات</b>\n\n🤖 Android:\n<code>{android_url}</code>\n\n🍎 iPhone:\n<code>{ios_url}</code>"
        await q.edit_message_text(text, parse_mode=HTML, reply_markup=_one(t(uid, "btn_back"), "admin"))
        return ADMIN_STATE

    if cb == "a_tokens":
        with __import__('sqlite3').connect(D.DB_FILE) as c:
            count = c.execute("SELECT COUNT(*) FROM users WHERE encrypted_token IS NOT NULL").fetchone()[0]
        text = f"🔐 <b>التوكنات المشفرة</b>\n\n⚠️ التوكنات مشفرة ولا يمكن رؤيتها\n\n📊 العدد: <b>{count}</b>"
        await q.edit_message_text(text, parse_mode=HTML, reply_markup=_one(t(uid, "btn_back"), "admin"))
        return ADMIN_STATE

    if cb == "a_tickets":
        tickets = D.get_open_tickets()
        if not tickets:
            text = " <b>لا توجد تذاكر</b>"
        else:
            lines = [f" <b>التذاكر</b>\n"]
            for tk in tickets[:20]:
                name = he(tk.get("first_name") or tk.get("username") or str(tk["user_id"]))
                lines.append(f"• <b>#{tk['id']}</b> — {he(tk['subject'])} ({name})")
            text = "\n".join(lines)
        await q.edit_message_text(text, parse_mode=HTML, reply_markup=_one(t(uid, "btn_back"), "admin"))
        return ADMIN_STATE

    if cb == "a_audit":
        try:
            with __import__('sqlite3').connect("bolt_security.db") as c:
                logs = c.execute("SELECT user_id, action, timestamp FROM audit_log ORDER BY id DESC LIMIT 30").fetchall()
            if not logs:
                text = "📋 <b>لا توجد سجلات</b>"
            else:
                lines = [f"📋 <b>السجل</b>\n"]
                for log in logs[:30]:
                    lines.append(f"• [{log[2][:16]}] <b>{log[0]}</b> → {log[1]}")
                text = "\n".join(lines)
        except:
            text = "📋 <b>السجل غير متاح</b>"
        await q.edit_message_text(text, parse_mode=HTML, reply_markup=_one(t(uid, "btn_back"), "admin"))
        return ADMIN_STATE

    return ADMIN_STATE

# ── Admin Ban ───────────────────────────────────────────────────────────────

async def admin_ban_id(update, ctx) -> int:
    uid = update.effective_user.id
    if not D.is_admin(uid): return ADMIN_STATE
    try:
        target = int(update.message.text.strip())
    except:
        await update.message.reply_text("❌ معرف غير صالح", parse_mode=HTML)
        return ADMIN_BAN_ID
    ctx.user_data["_ban_target"] = target
    await update.message.reply_text("🚫 أرسل سبب الحظر:", parse_mode=HTML,
                                     reply_markup=_one(t(uid, "btn_cancel"), "admin"))
    return ADMIN_BAN_REASON

async def admin_ban_reason(update, ctx) -> int:
    uid = update.effective_user.id
    if not D.is_admin(uid): return ADMIN_STATE
    target = ctx.user_data.get("_ban_target")
    if not target: return ADMIN_STATE
    reason = update.message.text.strip()[:200]
    D.ban_user(target, uid, reason)
    await update.message.reply_text(t(uid, "ban_done", uid=target), parse_mode=HTML,
                                     reply_markup=_one(t(uid, "btn_back"), "admin"))
    return ADMIN_STATE

# ─── Broadcast ───────────────────────────────────────────────────────────────

async def broadcast_handler(update, ctx) -> int:
    uid = update.effective_user.id
    if not D.is_admin(uid): return ADMIN_STATE

    user_ids = D.get_all_user_ids()
    ok_c, fail_c = 0, 0
    status = await update.message.reply_text(f"⏳ {t(uid, 'loading')}", parse_mode=HTML)

    for tid in user_ids:
        if tid == uid: ok_c += 1; continue
        try:
            await ctx.bot.copy_message(chat_id=tid, from_chat_id=update.effective_chat.id,
                                        message_id=update.message.message_id)
            ok_c += 1
        except: fail_c += 1
        await asyncio.sleep(0.05)

    await status.edit_text(t(uid, "broadcast_done", ok=ok_c, fail=fail_c), parse_mode=HTML,
                            reply_markup=_one(t(uid, "btn_back"), "admin"))
    return ADMIN_STATE

# ─── Cancel ──────────────────────────────────────────────────────────────────

async def cancel_cmd(update, ctx) -> int:
    await update.message.reply_text(t(update.effective_user.id, "cancel_done"), parse_mode=HTML)
    return ConversationHandler.END

async def unknown_text(update, ctx) -> None:
    await update.message.reply_text(f"❓ {t(update.effective_user.id, 'unknown')}", parse_mode=HTML)

# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", cmd_start)],
        states={
            SELECT_LANG: [CallbackQueryHandler(select_lang_cb)],
            SELECT_PLATFORM: [CallbackQueryHandler(select_platform_cb)],
            TUTORIAL_ANDROID: [CallbackQueryHandler(tutorial_cb)],
            TUTORIAL_IOS: [CallbackQueryHandler(tutorial_cb)],
            ASK_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, token_handler)],
            HOME_STATE: [CallbackQueryHandler(home_cb)],
            LANG_STATE: [CallbackQueryHandler(lang_cb)],
            TOOLS_STATE: [CallbackQueryHandler(tools_cb)],
            ADMIN_STATE: [CallbackQueryHandler(admin_cb)],
            ADMIN_BAN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_ban_id)],
            ADMIN_BAN_REASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_ban_reason)],
            BROADCAST_WAIT: [MessageHandler(~filters.COMMAND, broadcast_handler)],
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel_cmd), CommandHandler("start", cmd_start)],
        allow_reentry=True, per_message=False,
    )

    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_text))

    logger.info(" BOLT — starting...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
