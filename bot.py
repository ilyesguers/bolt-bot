"""
BOLT ⚡ — Telegram Bot (Full Version)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🛡️ Protected • Free • Fast
🔐 AES-256 encryption
📖 Interactive Tutorials (Android/iOS)
 Advanced Admin Panel
🌍 Multi-language: AR / EN / VI / HI

Built: July 2026
"""

import os
import io
import json
import asyncio
import zipfile
import logging
from datetime import datetime, timezone
from html import escape as he

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    InputFile, BotCommand,
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler,
    ContextTypes, filters,
)
from telegram.constants import ParseMode

import garena_api as G
import database as D
from i18n import t, LANGS
from crypto_utils import is_valid_token_format, hash_token

# ─── Config ───────────────────────────────────────────────────────────────────

BOT_TOKEN  = os.environ["TELEGRAM_BOT_TOKEN"]
OWNER_ID   = int(os.environ.get("OWNER_ID", "0"))
HTML       = ParseMode.HTML

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("bolt")

# ─── States ───────────────────────────────────────────────────────────────────

(
    # Onboarding
    SELECT_LANG,
    SELECT_PLATFORM,
    TUTORIAL_ANDROID,
    TUTORIAL_IOS,
    ASK_TOKEN,
    
    # Main
    HOME_STATE,
    TOOLS_STATE,
    LANG_STATE,
    ADMIN_STATE,
    
    # Admin actions
    ADMIN_BAN_ID,
    ADMIN_BAN_REASON,
    ADMIN_ADD_ADMIN,
    ADMIN_REMOVE_ADMIN,
    ADMIN_UPDATE_VIDEO_ANDROID,
    ADMIN_UPDATE_VIDEO_IOS,
    BROADCAST_WAIT,
    
    # Operations
    ASK_NAME,
    CHANGE_BIND_MODE,
    CHANGE_BIND_NEW_EMAIL,
    CHANGE_BIND_OTP,
    CHANGE_BIND_SEC_CODE,
    UNBIND_MODE,
    UNBIND_EMAIL,
    UNBIND_OTP,
    UNBIND_SEC_CODE,
    BIND_NEW_EMAIL,
    BIND_NEW_OTP,
    BIND_NEW_SEC_CODE,
) = range(28)

# ─── Keyboards ────────────────────────────────────────────────────────────────

def _btn(label, cb):
    return InlineKeyboardButton(label, callback_data=cb)

def lang_selection_kb():
    return InlineKeyboardMarkup([
        [_btn("🇸🇦 العربية", "lang_ar"), _btn("🇬 English", "lang_en")],
        [_btn("🇻🇳 Tiếng Việt", "lang_vi"), _btn("🇮🇳 हिन्दी", "lang_hi")],
    ])

def platform_selection_kb():
    return InlineKeyboardMarkup([
        [_btn("🤖 Android", "platform_android")],
        [_btn("🍎 iPhone (iOS)", "platform_ios")],
        [_btn("️ تخطي الشرح / Skip Tutorial", "skip_tutorial")],
    ])

def tutorial_android_kb():
    return InlineKeyboardMarkup([
        [_btn("▶️ عرض الفيديو", "show_video_android")],
        [_btn("✅ فهمت، أدخل التوكن", "got_it_android")],
        [_btn("🔄 عرض الشرح مرة أخرى", "retry_tutorial")],
    ])

def tutorial_ios_kb():
    return InlineKeyboardMarkup([
        [_btn("▶️ عرض الفيديو", "show_video_ios")],
        [_btn("✅ فهمت، أدخل التوكن", "got_it_ios")],
        [_btn("🔄 عرض الشرح مرة أخرى", "retry_tutorial")],
    ])

def home_kb(uid):
    has_token = D.has_token(uid)
    rows = []
    if has_token:
        rows.append([_btn(t(uid, "btn_tools"), "tools"), _btn(t(uid, "btn_card"), "card")])
        rows.append([_btn(t(uid, "btn_rewards"), "rewards"), _btn(t(uid, "btn_daily"), "daily")])
    else:
        rows.append([_btn(t(uid, "btn_add"), "add_token")])
    rows.append([_btn(t(uid, "btn_leaderboard"), "leaderboard"), _btn(t(uid, "btn_support"), "support")])
    rows.append([_btn(t(uid, "btn_lang"), "lang")])
    if D.is_admin(uid):
        rows.append([_btn(t(uid, "btn_admin"), "admin")])
    return InlineKeyboardMarkup(rows)

def tools_kb(uid):
    return InlineKeyboardMarkup([
        [_btn(t(uid, "btn_nickname"), "nickname"),
         _btn(t(uid, "btn_player_info"), "player_info")],
        [_btn(t(uid, "btn_check_token"), "check_token"),
         _btn(t(uid, "btn_bind_info"), "bind_info")],
        [_btn(t(uid, "btn_change_bind"), "change_bind"),
         _btn(t(uid, "btn_unbind"), "unbind")],
        [_btn(t(uid, "btn_cancel_bind"), "cancel_bind"),
         _btn(t(uid, "btn_bind_new"), "bind_new")],
        [_btn(t(uid, "btn_check_links"), "check_links"),
         _btn(t(uid, "btn_revoke"), "revoke")],
        [_btn(t(uid, "btn_history"), "history")],
        [_btn(t(uid, "btn_back"), "home")],
    ])

def admin_kb(uid):
    return InlineKeyboardMarkup([
        [_btn(t(uid, "btn_stats"), "a_stats"),
         _btn(t(uid, "btn_sec_stats"), "a_sec")],
        [_btn(t(uid, "btn_broadcast"), "a_bcast"),
         _btn(t(uid, "btn_backup"), "a_backup")],
        [_btn(t(uid, "btn_ban"), "a_ban"),
         _btn(t(uid, "btn_admins"), "a_admins")],
        [_btn(t(uid, "btn_tutorials"), "a_tutorials"),
         _btn(t(uid, "btn_view_tokens"), "a_tokens")],
        [_btn(t(uid, "btn_tickets"), "a_tickets"),
         _btn(t(uid, "btn_back"), "home")],
    ])

def one_btn(label, cb):
    return InlineKeyboardMarkup([[_btn(label, cb)]])

def two_btn(l1, c1, l2, c2):
    return InlineKeyboardMarkup([[_btn(l1, c1), _btn(l2, c2)]])

# ─── Post Init ────────────────────────────────────────────────────────────────

async def post_init(app):
    D.init_db()
    try:
        for lang in ["ar", "en"]:
            await app.bot.set_my_commands([
                BotCommand("start", "ابدأ / Start"),
            ], language_code=lang)
    except:
        pass
    logger.info("⚡ BOLT started — OWNER=%s", OWNER_ID)

# ── /start ───────────────────────────────────────────────────────────────────

async def cmd_start(update, ctx) -> int:
    uid = update.effective_user.id
    uname = update.effective_user.username or ""
    fname = update.effective_user.first_name or ""

    # Check ban
    banned, reason = D.is_banned(uid)
    if banned:
        await update.effective_message.reply_text(
            f"⛔️ <b>أنت محظور من هذا البوت.</b>\n\nالسبب: {reason}",
            parse_mode=HTML
        )
        return ConversationHandler.END

    user = D.ensure_user(uid, uname, fname)

    # If already onboarded, go to home
    if user.get("onboarded") and user.get("lang"):
        text = f"{t(uid, 'home_title')}\n\n{t(uid, 'home_subtitle')}"
        await update.effective_message.reply_text(text, parse_mode=HTML, reply_markup=home_kb(uid))
        return HOME_STATE

    # Show language selection
    await update.effective_message.reply_text(
        t(uid, "welcome_select_lang"),
        parse_mode=HTML,
        reply_markup=lang_selection_kb()
    )
    return SELECT_LANG

# ─── Language Selection ───────────────────────────────────────────────────────

async def select_lang_cb(update, ctx) -> int:
    q = update.callback_query
    await q.answer()
    uid = update.effective_user.id
    cb = q.data

    if cb.startswith("lang_"):
        lang = cb[5:]
        if lang in LANGS:
            D.set_lang(uid, lang)
            await q.edit_message_text(
                t(uid, "lang_selected"),
                parse_mode=HTML,
                reply_markup=platform_selection_kb()
            )
            return SELECT_PLATFORM

    return SELECT_LANG

# ─── Platform Selection ───────────────────────────────────────────────────────

async def select_platform_cb(update, ctx) -> int:
    q = update.callback_query
    await q.answer()
    uid = update.effective_user.id
    cb = q.data

    if cb == "platform_android":
        video_url = D.get_tutorial_video("android")
        text = (
            f"{t(uid, 'tutorial_title')}\n\n"
            f"{t(uid, 'tutorial_subtitle')}\n\n"
            f"{t(uid, 'tutorial_what_is')}\n\n"
            f"{t(uid, 'tutorial_choose_platform')}\n\n"
            f"{t(uid, 'tutorial_android_steps')}"
        )
        await q.edit_message_text(text, parse_mode=HTML, reply_markup=tutorial_android_kb())
        return TUTORIAL_ANDROID

    elif cb == "platform_ios":
        video_url = D.get_tutorial_video("ios")
        text = (
            f"{t(uid, 'tutorial_title')}\n\n"
            f"{t(uid, 'tutorial_subtitle')}\n\n"
            f"{t(uid, 'tutorial_what_is')}\n\n"
            f"{t(uid, 'tutorial_choose_platform')}\n\n"
            f"{t(uid, 'tutorial_ios_steps')}"
        )
        await q.edit_message_text(text, parse_mode=HTML, reply_markup=tutorial_ios_kb())
        return TUTORIAL_IOS

    elif cb == "skip_tutorial":
        D.set_onboarded(uid, 1)
        await q.edit_message_text(
            t(uid, "ask_token"),
            parse_mode=HTML,
            reply_markup=one_btn(t(uid, "btn_back"), "home")
        )
        return ASK_TOKEN

    return SELECT_PLATFORM

# ─── Tutorial Callbacks ───────────────────────────────────────────────────────

async def tutorial_android_cb(update, ctx) -> int:
    q = update.callback_query
    await q.answer()
    uid = update.effective_user.id
    cb = q.data

    if cb == "show_video_android":
        video_url = D.get_tutorial_video("android")
        await q.edit_message_text(
            f"📹 <b>فيديو الشرح — Android</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔗 الرابط:\n"
            f"<code>{video_url}</code>\n\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f"💡 اتبع الخطوات في الفيديو",
            parse_mode=HTML,
            reply_markup=tutorial_android_kb()
        )
        return TUTORIAL_ANDROID

    elif cb == "got_it_android":
        D.set_onboarded(uid, 1)
        await q.edit_message_text(
            t(uid, "ask_token"),
            parse_mode=HTML,
            reply_markup=one_btn(t(uid, "btn_back"), "home")
        )
        return ASK_TOKEN

    elif cb == "retry_tutorial":
        await q.edit_message_text(
            f"{t(uid, 'tutorial_title')}\n\n"
            f"{t(uid, 'tutorial_android_steps')}",
            parse_mode=HTML,
            reply_markup=tutorial_android_kb()
        )
        return TUTORIAL_ANDROID

    return TUTORIAL_ANDROID

async def tutorial_ios_cb(update, ctx) -> int:
    q = update.callback_query
    await q.answer()
    uid = update.effective_user.id
    cb = q.data

    if cb == "show_video_ios":
        video_url = D.get_tutorial_video("ios")
        await q.edit_message_text(
            f" <b>فيديو الشرح — iOS</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f" الرابط:\n"
            f"<code>{video_url}</code>\n\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f"💡 اتبع الخطوات في الفيديو",
            parse_mode=HTML,
            reply_markup=tutorial_ios_kb()
        )
        return TUTORIAL_IOS

    elif cb == "got_it_ios":
        D.set_onboarded(uid, 1)
        await q.edit_message_text(
            t(uid, "ask_token"),
            parse_mode=HTML,
            reply_markup=one_btn(t(uid, "btn_back"), "home")
        )
        return ASK_TOKEN

    elif cb == "retry_tutorial":
        await q.edit_message_text(
            f"{t(uid, 'tutorial_title')}\n\n"
            f"{t(uid, 'tutorial_ios_steps')}",
            parse_mode=HTML,
            reply_markup=tutorial_ios_kb()
        )
        return TUTORIAL_IOS

    return TUTORIAL_IOS

# ─── Token Input ──────────────────────────────────────────────────────────────

async def token_handler(update, ctx) -> int:
    uid = update.effective_user.id
    raw = update.message.text.strip()

    # Validate format
    if not is_valid_token_format(raw):
        await update.message.reply_text(
            t(uid, "token_invalid"),
            parse_mode=HTML
        )
        return ASK_TOKEN

    # Validate with Garena
    msg = await update.message.reply_text(f"⏳ {t(uid, 'loading')}", parse_mode=HTML)
    validation = G.validate_token(raw)

    if not validation.get("valid"):
        await msg.edit_text(
            t(uid, "token_invalid"),
            parse_mode=HTML,
            reply_markup=one_btn(t(uid, "btn_back"), "home")
        )
        return ASK_TOKEN

    # Store encrypted
    D.set_token(uid, raw)
    D.increment_ops(uid)
    D.log_activity(uid, "ADD_TOKEN", "Token added", success=True)

    await msg.edit_text(
        t(uid, "token_saved"),
        parse_mode=HTML,
        reply_markup=home_kb(uid)
    )
    return HOME_STATE

# ─── Home Callbacks ───────────────────────────────────────────────────────────

async def home_cb(update, ctx) -> int:
    q = update.callback_query
    await q.answer()
    uid = update.effective_user.id
    cb = q.data

    # Check ban
    banned, reason = D.is_banned(uid)
    if banned:
        await q.edit_message_text(
            f"⛔️ <b>أنت محظور.</b>\n\nالسبب: {reason}",
            parse_mode=HTML
        )
        return ConversationHandler.END

    if cb == "home":
        text = f"{t(uid, 'home_title')}\n\n{t(uid, 'home_subtitle')}"
        await q.edit_message_text(text, parse_mode=HTML, reply_markup=home_kb(uid))
        return HOME_STATE

    if cb == "add_token":
        await q.edit_message_text(
            t(uid, "ask_token"),
            parse_mode=HTML,
            reply_markup=one_btn(t(uid, "btn_back"), "home")
        )
        return ASK_TOKEN

    if cb == "tools":
        if not D.has_token(uid):
            await q.edit_message_text(
                t(uid, "ask_token"),
                parse_mode=HTML,
                reply_markup=one_btn(t(uid, "btn_add"), "add_token")
            )
            return ASK_TOKEN
        await q.edit_message_text(
            t(uid, "tools_title"),
            parse_mode=HTML,
            reply_markup=tools_kb(uid)
        )
        return TOOLS_STATE

    # More callbacks will be added...

    if cb == "lang":
        await q.edit_message_text(
            t(uid, "welcome_select_lang"),
            parse_mode=HTML,
            reply_markup=lang_selection_kb()
        )
        return LANG_STATE

    if cb == "admin":
        if not D.is_admin(uid):
            await q.answer(t(uid, "not_auth"), show_alert=True)
            return HOME_STATE
        await q.edit_message_text(
            t(uid, "admin_title"),
            parse_mode=HTML,
            reply_markup=admin_kb(uid)
        )
        return ADMIN_STATE

    return HOME_STATE

# ─── Language Callbacks ───────────────────────────────────────────────────────

async def lang_cb(update, ctx) -> int:
    q = update.callback_query
    await q.answer()
    uid = update.effective_user.id
    cb = q.data

    if cb.startswith("lang_"):
        lang = cb[5:]
        if lang in LANGS:
            D.set_lang(uid, lang)
            await q.edit_message_text(
                f"✅ {t(uid, 'lang_selected')}",
                parse_mode=HTML,
                reply_markup=one_btn(t(uid, "btn_home"), "home")
            )
    return LANG_STATE

# ─── Admin Callbacks ─────────────────────────────────────────────────────────

async def admin_cb(update, ctx) -> int:
    q = update.callback_query
    await q.answer()
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
        await q.edit_message_text(
            t(uid, "admin_title"),
            parse_mode=HTML,
            reply_markup=admin_kb(uid)
        )
        return ADMIN_STATE

    if cb == "a_stats":
        users = D.user_count()
        await q.edit_message_text(
            t(uid, "stats_text", users=users, with_token=0, ops=0),
            parse_mode=HTML,
            reply_markup=one_btn(t(uid, "btn_back"), "admin")
        )
        return ADMIN_STATE

    if cb == "a_bcast":
        await q.edit_message_text(
            t(uid, "broadcast_ask"),
            parse_mode=HTML,
            reply_markup=one_btn(t(uid, "btn_cancel"), "admin")
        )
        return BROADCAST_WAIT

    if cb == "a_ban":
        await q.edit_message_text(
            t(uid, "ban_ask_id"),
            parse_mode=HTML,
            reply_markup=one_btn(t(uid, "btn_cancel"), "admin")
        )
        return ADMIN_BAN_ID

    # More admin callbacks will be added...

    return ADMIN_STATE

# ─── Admin Ban ────────────────────────────────────────────────────────────────

async def admin_ban_id(update, ctx) -> int:
    uid = update.effective_user.id
    if not D.is_admin(uid):
        return ADMIN_STATE
    
    try:
        target = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ معرف غير صالح", parse_mode=HTML)
        return ADMIN_BAN_ID
    
    ctx.user_data["_ban_target"] = target
    await update.message.reply_text(
        "🚫 أرسل سبب الحظر:",
        parse_mode=HTML,
        reply_markup=one_btn(t(uid, "btn_cancel"), "admin")
    )
    return ADMIN_BAN_REASON

async def admin_ban_reason(update, ctx) -> int:
    uid = update.effective_user.id
    if not D.is_admin(uid):
        return ADMIN_STATE
    
    target = ctx.user_data.get("_ban_target")
    if not target:
        return ADMIN_STATE
    
    reason = update.message.text.strip()[:200]
    D.ban_user(target, uid, reason)
    
    await update.message.reply_text(
        t(uid, "ban_done", uid=target),
        parse_mode=HTML,
        reply_markup=one_btn(t(uid, "btn_back"), "admin")
    )
    return ADMIN_STATE

# ─── Broadcast ───────────────────────────────────────────────────────────────

async def broadcast_handler(update, ctx) -> int:
    uid = update.effective_user.id
    if not D.is_admin(uid):
        return ADMIN_STATE

    user_ids = D.get_all_user_ids()
    ok_c, fail_c = 0, 0
    status = await update.message.reply_text(f"⏳ {t(uid, 'loading')}", parse_mode=HTML)

    for tid in user_ids:
        if tid == uid:
            ok_c += 1
            continue
        try:
            await ctx.bot.copy_message(
                chat_id=tid,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id
            )
            ok_c += 1
        except:
            fail_c += 1
        await asyncio.sleep(0.05)

    await status.edit_text(
        t(uid, "broadcast_done", ok=ok_c, fail=fail_c),
        parse_mode=HTML,
        reply_markup=one_btn(t(uid, "btn_back"), "admin")
    )
    return ADMIN_STATE

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", cmd_start)],
        states={
            # Onboarding
            SELECT_LANG: [CallbackQueryHandler(select_lang_cb)],
            SELECT_PLATFORM: [CallbackQueryHandler(select_platform_cb)],
            TUTORIAL_ANDROID: [CallbackQueryHandler(tutorial_android_cb)],
            TUTORIAL_IOS: [CallbackQueryHandler(tutorial_ios_cb)],
            ASK_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, token_handler)],
            
            # Main
            HOME_STATE: [CallbackQueryHandler(home_cb)],
            LANG_STATE: [CallbackQueryHandler(lang_cb)],
            TOOLS_STATE: [CallbackQueryHandler(home_cb)],  # Will be expanded
            ADMIN_STATE: [CallbackQueryHandler(admin_cb)],
            
            # Admin actions
            ADMIN_BAN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_ban_id)],
            ADMIN_BAN_REASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_ban_reason)],
            BROADCAST_WAIT: [MessageHandler(~filters.COMMAND, broadcast_handler)],
        },
        fallbacks=[CommandHandler("start", cmd_start)],
        allow_reentry=True,
        per_message=False,
    )

    app.add_handler(conv)

    logger.info("⚡ BOLT — starting...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
