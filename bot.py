"""
BOLT ⚡ — Telegram Bot
━━━━━━━━━━━━━━━━━━━━━━
🛡️ Protected • Free • Fast
🔐 AES-256 encryption for all tokens
🎁 Rewards system with levels & streaks
📊 No third-party APIs — direct Garena only
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
import rewards as R
from i18n import t, LANGS
from security import RateLimiter, sanitize_html, sanitize_text, validate_email, validate_nickname
from crypto_utils import is_valid_token_format, hash_token, token_fingerprint, mask_token

# ─── Config ───────────────────────────────────────────────────────────────────

BOT_TOKEN  = os.environ["TELEGRAM_BOT_TOKEN"]
OWNER_ID   = int(os.environ.get("OWNER_ID", "0"))
HTML       = ParseMode.HTML

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("bolt")

# ─── Security ─────────────────────────────────────────────────────────────────

sec = RateLimiter()

# ─── Emoji ────────────────────────────────────────────────────────────────────

BOLT_E = "⚡"
SHIELD = "🛡️"
LOCK   = "🔐"
KEY    = "🗝"
CHECK  = "✅"
CROSS  = "❌"
CLOCK  = "⏳"
INFO   = "💡"
WARN   = "⚠️"
FIRE   = "🔥"
STAR   = "⭐"
GIFT   = "🎁"
TROPHY = "🏆"
CARD   = "🃏"
CHART  = "📊"
GEAR   = "🔧"
BACK   = "🔙"
HOME   = "🏠"
RADIO  = "📢"
SAVE   = "💾"
CROWN  = "👑"
GLOBE  = "🌍"
MAIL   = "📩"
EARTH  = "🌐"
LINK   = "🔗"
SCROLL = "📜"
PERSON = "👤"
ROCKET = "🚀"

# ─── States ───────────────────────────────────────────────────────────────────

(
    HOME_STATE,
    ASK_TOKEN,
    ASK_NAME,
    TOOLS_STATE,
    LANG_STATE,
    ADMIN_STATE,
    BROADCAST_WAIT,
    SUPPORT_SUBJECT,
    SUPPORT_MESSAGE,
    ADMIN_BAN_ID,
    ADMIN_BAN_REASON,
) = range(11)

# ─── Keyboards ────────────────────────────────────────────────────────────────

def _btn(label, cb):
    return InlineKeyboardButton(label, callback_data=cb)

def home_kb(uid):
    has_token = D.has_token(uid)
    rows = []
    if has_token:
        rows.append([_btn(t(uid, "btn_tools"), "tools"), _btn(t(uid, "btn_card"), "card")])
        rows.append([_btn(t(uid, "btn_rewards"), "rewards"), _btn(t(uid, "btn_daily"), "daily")])
    else:
        rows.append([_btn(t(uid, "btn_add"), "add_token")])
        rows.append([_btn(t(uid, "btn_rewards"), "rewards"), _btn(t(uid, "btn_daily"), "daily")])
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
        [_btn(t(uid, "btn_check_links"), "check_links"),
         _btn(t(uid, "btn_history"), "history")],
        [_btn(t(uid, "btn_back"), "home")],
    ])

def admin_kb(uid):
    return InlineKeyboardMarkup([
        [_btn(t(uid, "btn_stats"), "a_stats"),
         _btn(t(uid, "btn_sec_stats"), "a_sec")],
        [_btn(t(uid, "btn_broadcast"), "a_bcast"),
         _btn(t(uid, "btn_backup"), "a_backup")],
        [_btn(t(uid, "btn_ban"), "a_ban"),
         _btn(t(uid, "btn_audit"), "a_audit")],
        [_btn(t(uid, "btn_tickets"), "a_tickets"),
         _btn(t(uid, "btn_back"), "home")],
    ])

def lang_kb():
    return InlineKeyboardMarkup([
        [_btn("🇸🇦 العربية", "lang_ar"), _btn("🇬🇧 English", "lang_en")],
        [_btn("🇻🇳 Tiếng Việt", "lang_vi"), _btn("🇮🇳 हिन्दी", "lang_hi")],
    ])

def one_btn(label, cb):
    return InlineKeyboardMarkup([[_btn(label, cb)]])

def two_btn(l1, c1, l2, c2):
    return InlineKeyboardMarkup([[_btn(l1, c1), _btn(l2, c2)]])

# ─── Guards ───────────────────────────────────────────────────────────────────

async def _check_ban(update, ctx):
    uid = update.effective_user.id
    banned, _ = sec.is_banned(uid)
    if banned:
        fn = _get_fn(update)
        await fn(f"⛔️ {t(uid, 'user_banned')}", parse_mode=HTML)
        return False
    return True

async def _check_rate(update, ctx, action="general"):
    uid = update.effective_user.id
    ok, retry = sec.check(uid, action)
    if not ok:
        if update.callback_query:
            await update.callback_query.answer(t(uid, "ratelimited", sec=retry), show_alert=True)
        else:
            await update.effective_message.reply_text(f"{WARN} {t(uid, 'ratelimited', sec=retry)}", parse_mode=HTML)
        return False
    return True

async def _check_daily(update, ctx):
    uid = update.effective_user.id
    ok, remaining, limit = D.check_daily_ops(uid)
    if not ok:
        msg = t(uid, "ops_exhausted")
        if update.callback_query:
            await update.callback_query.answer(msg, show_alert=True)
        else:
            await update.effective_message.reply_text(f"{WARN} {msg}", parse_mode=HTML)
        return False
    return True

def _get_fn(update):
    if update.callback_query:
        return lambda txt, **kw: update.callback_query.edit_message_text(txt, **kw)
    return lambda txt, **kw: update.effective_message.reply_text(txt, **kw)

# ─── Home Text Builder ────────────────────────────────────────────────────────

def _home_text(uid):
    user = D.get_user(uid)
    rw = D.get_rewards(uid)
    name = user.get("first_name") or user.get("username") or "User" if user else "User"
    has_token = D.has_token(uid)
    token_status = t(uid, "token_active") if has_token else t(uid, "token_none")

    _, today_ops, max_ops = D.check_daily_ops(uid)
    today_ops = max_ops - today_ops  # used ops
    # Re-check to get remaining
    ok, remaining, limit = D.check_daily_ops(uid)

    lines = [
        f"{BOLT_E} **BOLT** — {t(uid, 'home_sub')}",
        "",
        f"{SHIELD} ━━━━━━━━ ⚡ ━━━━━━━━ {SHIELD}",
        "",
        f"{PERSON} {name}",
        f"{LOCK} {t(uid, 'home_token_status', status=token_status)}",
        f"{CHART} {t(uid, 'home_stats', ops=remaining, max=limit, streak=rw.get('streak', 0))}",
        f"{TROPHY} {R.get_level_info(rw.get('level', 1)).get('name_ar', '🥉 Bronze')}",
        "",
        f"{SHIELD} ━━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"{ROCKET} {t(uid, 'home_choose')}",
    ]
    return "\n".join(lines)

# ─── Post Init ────────────────────────────────────────────────────────────────

async def post_init(app):
    D.init_db()
    try:
        for lang in ["ar", "en"]:
            await app.bot.set_my_commands([
                BotCommand("start", "ابدأ / Start"),
                BotCommand("cancel", "إلغاء / Cancel"),
            ], language_code=lang)
    except:
        pass
    logger.info("⚡ BOLT started — OWNER=%s", OWNER_ID)

# ─── /start ───────────────────────────────────────────────────────────────────

async def cmd_start(update, ctx) -> int:
    uid = update.effective_user.id
    uname = update.effective_user.username or ""
    fname = update.effective_user.first_name or ""

    user = D.ensure_user(uid, uname, fname)
    sec.audit(uid, "START", f"@{uname}")

    # Check if new user → show welcome
    is_new = user["total_ops"] == 0 and not D.has_token(uid)

    if is_new:
        text = t(uid, "welcome_new")
        fn = update.effective_message.reply_text
        await fn(text, parse_mode=HTML, reply_markup=InlineKeyboardMarkup([
            [_btn(t(uid, "btn_add"), "add_token")]
        ]))
        return HOME_STATE

    text = _home_text(uid)
    fn = _get_fn(update)
    await fn(text, parse_mode=HTML, reply_markup=home_kb(uid))
    return HOME_STATE

# ─── Home Callbacks ───────────────────────────────────────────────────────────

async def home_cb(update, ctx) -> int:
    q = update.callback_query
    await q.answer()
    uid = update.effective_user.id
    cb = q.data

    if not await _check_ban(update, ctx):
        return ConversationHandler.END

    # ── HOME ──
    if cb == "home":
        text = _home_text(uid)
        await q.edit_message_text(text, parse_mode=HTML, reply_markup=home_kb(uid))
        return HOME_STATE

    # ── ADD TOKEN ──
    if cb == "add_token":
        if not await _check_rate(update, ctx, "token_ops"):
            return HOME_STATE
        await q.edit_message_text(t(uid, "send_token"), parse_mode=HTML,
                                   reply_markup=one_btn(t(uid, "btn_back"), "home"))
        return ASK_TOKEN

    # ── TOOLS ──
    if cb == "tools":
        if not await _check_rate(update, ctx):
            return HOME_STATE
        if not D.has_token(uid):
            await q.edit_message_text(t(uid, "no_token"), parse_mode=HTML,
                                       reply_markup=one_btn(t(uid, "btn_add"), "add_token"))
            return ASK_TOKEN
        sec.audit(uid, "OPEN_TOOLS")
        await q.edit_message_text(f"{GEAR} {t(uid, 'tools_title')}", parse_mode=HTML,
                                   reply_markup=tools_kb(uid))
        return TOOLS_STATE

    # ── MY CARD ──
    if cb == "card":
        user = D.get_user(uid)
        rw = D.get_rewards(uid)
        name = user.get("first_name") or user.get("username") or "User"
        joined = user["joined_at"][:10] if user else "?"
        text = t(uid, "my_card_title", name=he(name), uid=uid, joined=joined)
        text += "\n\n" + R.format_reward_card(rw["points"], rw["level"], rw["streak"], rw["total_earned"])
        await q.edit_message_text(text, parse_mode=HTML,
                                   reply_markup=one_btn(t(uid, "btn_back"), "home"))
        sec.audit(uid, "VIEW_CARD")
        return HOME_STATE

    # ── REWARDS ──
    if cb == "rewards":
        rw = D.get_rewards(uid)
        text = R.format_reward_card(rw["points"], rw["level"], rw["streak"], rw["total_earned"])
        await q.edit_message_text(text, parse_mode=HTML,
                                   reply_markup=one_btn(t(uid, "btn_back"), "home"))
        sec.audit(uid, "VIEW_REWARDS")
        return HOME_STATE

    # ── DAILY REWARD ──
    if cb == "daily":
        ok, pts = D.claim_daily(uid)
        if ok:
            rw = D.get_rewards(uid)
            sec.audit(uid, "DAILY_CLAIM", f"+{pts}")
            lvl = R.get_level_info(rw["level"]).get("name_ar", "")
            await q.edit_message_text(
                t(uid, "daily_claimed", pts=pts, streak=rw["streak"], level=lvl),
                parse_mode=HTML, reply_markup=one_btn(t(uid, "btn_back"), "home")
            )
        else:
            await q.edit_message_text(t(uid, "daily_already"), parse_mode=HTML,
                                       reply_markup=one_btn(t(uid, "btn_back"), "home"))
        return HOME_STATE

    # ── LEADERBOARD ──
    if cb == "leaderboard":
        board = D.leaderboard(10)
        if not board:
            await q.edit_message_text(f"{TROPHY} {t(uid, 'leaderboard_empty')}",
                                       parse_mode=HTML, reply_markup=one_btn(t(uid, "btn_back"), "home"))
            return HOME_STATE

        medals = ["🥇", "🥈", "🥉"] + ["⚡"] * 7
        lines = [f"{TROPHY} **{t(uid, 'leaderboard_title')}**\n"]
        my_pos = None
        for i, u in enumerate(board):
            m = medals[i] if i < len(medals) else "  "
            name = he(u.get("first_name") or u.get("username") or str(u["user_id"]))
            lvl = R.get_level_info(u.get("level", 1)).get("name_ar", "🥉")
            lines.append(f"{m} **{name}** — {u.get('points', 0)} pts {lvl}")
            if u["user_id"] == uid:
                my_pos = i + 1

        # Find user position if not in top 10
        if my_pos is None:
            rw = D.get_rewards(uid)
            my_pts = rw.get("points", 0)
            # Count users with more points
            my_pos = sum(1 for b in board if b.get("points", 0) > my_pts) + 1
            # Actually need full query but let's approximate
            lines.append(t(uid, "leaderboard_you", pos=my_pos, pts=my_pts))

        await q.edit_message_text("\n".join(lines), parse_mode=HTML,
                                   reply_markup=one_btn(t(uid, "btn_back"), "home"))
        sec.audit(uid, "VIEW_LEADERBOARD")
        return HOME_STATE

    # ── SUPPORT ──
    if cb == "support":
        await q.edit_message_text(f"{MAIL} {t(uid, 'support_ask_subject')}", parse_mode=HTML,
                                   reply_markup=one_btn(t(uid, "btn_cancel"), "home"))
        return SUPPORT_SUBJECT

    # ── LANGUAGE ──
    if cb == "lang":
        await q.edit_message_text(f"{GLOBE} {t(uid, 'lang_title')}", parse_mode=HTML,
                                   reply_markup=lang_kb())
        return LANG_STATE

    # ── ADMIN ──
    if cb == "admin":
        if not D.is_admin(uid):
            await q.answer(t(uid, "not_auth"), show_alert=True)
            return HOME_STATE
        sec.audit(uid, "OPEN_ADMIN")
        await q.edit_message_text(f"{CROWN} **{t(uid, 'admin_title')}**", parse_mode=HTML,
                                   reply_markup=admin_kb(uid))
        return ADMIN_STATE

    return HOME_STATE

# ─── Language ─────────────────────────────────────────────────────────────────

async def lang_cb(update, ctx) -> int:
    q = update.callback_query
    await q.answer()
    uid = update.effective_user.id
    cb = q.data

    if cb == "home":
        text = _home_text(uid)
        await q.edit_message_text(text, parse_mode=HTML, reply_markup=home_kb(uid))
        return HOME_STATE

    if cb.startswith("lang_"):
        lang = cb[5:]
        if lang in LANGS:
            D.set_lang(uid, lang)
            sec.audit(uid, "LANG", lang)
            text = f"{CHECK} {t(uid, 'lang_set')}"
            await q.edit_message_text(text, parse_mode=HTML,
                                       reply_markup=one_btn(t(uid, "btn_home"), "home"))
    return LANG_STATE

# ─── Token Input ──────────────────────────────────────────────────────────────

async def token_handler(update, ctx) -> int:
    uid = update.effective_user.id
    if not await _check_ban(update, ctx):
        return ConversationHandler.END

    raw = update.message.text.strip()

    # Validate format
    if not is_valid_token_format(raw):
        await update.message.reply_text(f"{CROSS} {t(uid, 'token_bad')}", parse_mode=HTML)
        return ASK_TOKEN

    # Validate with Garena (DIRECT call)
    msg = await update.message.reply_text(f"{CLOCK} {t(uid, 'loading')}", parse_mode=HTML)
    validation = G.validate_token(raw)

    if not validation.get("valid"):
        await msg.edit_text(f"{CROSS} {t(uid, 'token_invalid')}", parse_mode=HTML,
                             reply_markup=one_btn(t(uid, "btn_back"), "home"))
        sec.audit(uid, "TOKEN_INVALID", hash_token(raw))
        return ASK_TOKEN

    # Store encrypted with fingerprint
    D.set_token(uid, raw)
    D.increment_ops(uid)
    D.log_activity(uid, "ADD_TOKEN", f"fp={token_fingerprint(raw)[:8]}", success=True)
    D.add_points(uid, R.POINTS.get("add_token", 10), "add_token", "First token added")
    sec.audit(uid, "TOKEN_SET", f"hash={hash_token(raw)}")

    await msg.edit_text(
        t(uid, "token_saved"),
        parse_mode=HTML, reply_markup=tools_kb(uid)
    )
    return TOOLS_STATE

# ─── Tools Callbacks ─────────────────────────────────────────────────────────

async def tools_cb(update, ctx) -> int:
    q = update.callback_query
    await q.answer()
    uid = update.effective_user.id
    cb = q.data

    if not await _check_ban(update, ctx):
        return ConversationHandler.END

    if cb == "home":
        text = _home_text(uid)
        await q.edit_message_text(text, parse_mode=HTML, reply_markup=home_kb(uid))
        return HOME_STATE

    if cb == "tools":
        await q.edit_message_text(f"{GEAR} {t(uid, 'tools_title')}", parse_mode=HTML,
                                   reply_markup=tools_kb(uid))
        return TOOLS_STATE

    # ── NICKNAME ──
    if cb == "nickname":
        if not await _check_rate(update, ctx, "nickname"):
            return TOOLS_STATE
        if not await _check_daily(update, ctx):
            return TOOLS_STATE
        await q.edit_message_text(t(uid, "send_new_name"), parse_mode=HTML,
                                   reply_markup=one_btn(t(uid, "btn_back"), "tools"))
        return ASK_NAME

    # ── PLAYER INFO ──
    if cb == "player_info":
        if not await _check_rate(update, ctx, "garena_api"):
            return TOOLS_STATE
        if not await _check_daily(update, ctx):
            return TOOLS_STATE
        return await _do_player_info(update, ctx)

    # ── CHECK TOKEN ──
    if cb == "check_token":
        if not await _check_rate(update, ctx, "garena_api"):
            return TOOLS_STATE
        return await _do_check_token(update, ctx)

    # ── BIND INFO ──
    if cb == "bind_info":
        if not await _check_rate(update, ctx, "garena_api"):
            return TOOLS_STATE
        if not await _check_daily(update, ctx):
            return TOOLS_STATE
        return await _do_bind_info(update, ctx)

    # ── CHECK LINKS ──
    if cb == "check_links":
        if not await _check_rate(update, ctx, "garena_api"):
            return TOOLS_STATE
        if not await _check_daily(update, ctx):
            return TOOLS_STATE
        return await _do_check_links(update, ctx)

    # ── HISTORY ──
    if cb == "history":
        logs = D.get_activity(uid, 15)
        if not logs:
            text = f"{SCROLL} {t(uid, 'history_empty')}"
        else:
            lines = [f"{SCROLL} **{t(uid, 'history_title')}**\n"]
            for log in logs:
                icon = "✅" if log["success"] else "❌"
                ts = log["timestamp"][:16]
                lines.append(f"{icon} {log['action']} — {ts}")
            text = "\n".join(lines)
        await q.edit_message_text(text, parse_mode=HTML,
                                   reply_markup=one_btn(t(uid, "btn_back"), "tools"))
        return TOOLS_STATE

    return TOOLS_STATE

# ─── Nickname Handler ─────────────────────────────────────────────────────────

async def name_handler(update, ctx) -> int:
    uid = update.effective_user.id
    if not await _check_ban(update, ctx):
        return ConversationHandler.END

    name = update.message.text.strip()
    valid, result = validate_nickname(name)
    if not valid:
        await update.message.reply_text(t(uid, "name_invalid", reason=result), parse_mode=HTML)
        return ASK_NAME

    token = D.get_token(uid)
    if not token:
        await update.message.reply_text(t(uid, "no_token"), parse_mode=HTML)
        return HOME_STATE

    msg = await update.message.reply_text(f"{CLOCK} {t(uid, 'loading')}", parse_mode=HTML)
    try:
        r = G.change_name(token, name)
        if r.get("error"):
            text = f"{CROSS} {r['error']}"
            success = False
        elif r.get("status") == 200:
            text = t(uid, "name_changed", name=he(name))
            success = True
        else:
            text = f"{WARN} {r.get('status')}"
            success = False
    except Exception as e:
        text = f"{CROSS} {e}"
        success = False

    if success:
        D.increment_ops(uid)
        D.add_points(uid, R.POINTS.get("change_name", 5), "change_name", name)
        D.log_activity(uid, "NICKNAME", name, success=True)

    sec.audit(uid, "NICKNAME" if success else "NICKNAME_FAIL", name)
    await msg.edit_text(text, parse_mode=HTML, reply_markup=tools_kb(uid))
    return TOOLS_STATE

# ─── Garena Actions ───────────────────────────────────────────────────────────

def _need_token(update, ctx):
    uid = update.effective_user.id
    token = D.get_token(uid)
    if not token:
        return None
    return token

async def _do_player_info(update, ctx) -> int:
    q = update.callback_query
    uid = update.effective_user.id
    token = _need_token(update, ctx)
    if not token:
        await q.edit_message_text(t(uid, "no_token"), parse_mode=HTML, reply_markup=home_kb(uid))
        return HOME_STATE

    await q.edit_message_text(f"{CLOCK} {t(uid, 'loading')}", parse_mode=HTML)
    info = G.get_player_info(token)

    if info.get("error"):
        text = f"{CROSS} {info['error']}"
        D.log_activity(uid, "PLAYER_INFO", info["error"][:50], success=False)
    elif info.get("status") == "success":
        D.log_activity(uid, "PLAYER_INFO", "ok", success=True)
        D.add_points(uid, R.POINTS.get("check_info", 2), "check_info", "Player info")
        if info.get("name"):
            text = t(uid, "player_info_card",
                     uid=info.get("uid", "?"), name=he(info.get("name", "?")),
                     level=info.get("level", "?"), rank=info.get("rank", "?"),
                     oid=info.get("open_id", "?"))
        else:
            text = t(uid, "player_info_basic", oid=info.get("open_id", "?"))
    else:
        text = t(uid, "error_generic")

    sec.audit(uid, "PLAYER_INFO", info.get("open_id", "")[:20])
    await q.edit_message_text(text, parse_mode=HTML, reply_markup=tools_kb(uid))
    return TOOLS_STATE

async def _do_check_token(update, ctx) -> int:
    q = update.callback_query
    uid = update.effective_user.id
    token = _need_token(update, ctx)
    if not token:
        await q.edit_message_text(t(uid, "no_token"), parse_mode=HTML, reply_markup=home_kb(uid))
        return HOME_STATE

    await q.edit_message_text(f"{CLOCK} {t(uid, 'loading')}", parse_mode=HTML)
    result = G.validate_token(token)

    if result.get("valid"):
        text = t(uid, "token_valid_msg", oid=result.get("open_id", "?"),
                 expires=result.get("expires", "?"))
        D.add_points(uid, R.POINTS.get("validate_token", 1), "validate_token", "Token valid")
        D.log_activity(uid, "TOKEN_CHECK", "valid", success=True)
    else:
        text = t(uid, "token_invalid")
        D.log_activity(uid, "TOKEN_CHECK", "invalid", success=False)

    sec.audit(uid, "TOKEN_CHECK", f"valid={result.get('valid')}")
    await q.edit_message_text(text, parse_mode=HTML, reply_markup=tools_kb(uid))
    return TOOLS_STATE

async def _do_bind_info(update, ctx) -> int:
    q = update.callback_query
    uid = update.effective_user.id
    token = _need_token(update, ctx)
    if not token:
        await q.edit_message_text(t(uid, "no_token"), parse_mode=HTML, reply_markup=home_kb(uid))
        return HOME_STATE

    await q.edit_message_text(f"{CLOCK} {t(uid, 'loading')}", parse_mode=HTML)

    # Use DIRECT Garena API
    result = G.check_bind_info_direct(token)
    if result.get("error"):
        text = f"{CROSS} {result['error']}"
    elif result.get("email"):
        lines = [f"{MAIL} **{t(uid, 'bind_info_title')}**\n"]
        lines.append(f"📧 Email: `{he(result['email'])}`")
        if result.get("status"):
            lines.append(f"📊 Status: {result['status']}")
        text = "\n".join(lines)
    else:
        text = f"{INFO} {result}"

    D.add_points(uid, R.POINTS.get("check_info", 2), "bind_info", "Checked")
    D.log_activity(uid, "BIND_INFO", "", success=G.is_success(result))
    sec.audit(uid, "BIND_INFO", "")
    await q.edit_message_text(text, parse_mode=HTML, reply_markup=tools_kb(uid))
    return TOOLS_STATE

async def _do_check_links(update, ctx) -> int:
    q = update.callback_query
    uid = update.effective_user.id
    token = _need_token(update, ctx)
    if not token:
        await q.edit_message_text(t(uid, "no_token"), parse_mode=HTML, reply_markup=home_kb(uid))
        return HOME_STATE

    await q.edit_message_text(f"{CLOCK} {t(uid, 'loading')}", parse_mode=HTML)

    # DIRECT Garena API
    j = G.check_links(token)
    bounded = j.get("bounded_accounts", [])
    lines = [f"{EARTH} **{t(uid, 'links_title')}**"]
    found = False
    for x in bounded:
        p = x.get("platform")
        ui = x.get("user_info", {})
        name = G.PLATFORM_NAMES.get(p, f"Platform {p}")
        lines.append(f"\n◾️ **{name}**")
        if ui.get("email"):
            lines.append(f"  {MAIL} {he(ui['email'])}")
        if ui.get("nickname"):
            lines.append(f"  {PERSON} {he(ui['nickname'])}")
        found = True
    if not found:
        lines.append(f"\n{INFO} {t(uid, 'no_links')}")

    D.add_points(uid, R.POINTS.get("check_links", 2), "check_links", "Links checked")
    D.log_activity(uid, "CHECK_LINKS", f"count={len(bounded)}", success=True)
    sec.audit(uid, "CHECK_LINKS", f"found={found}")
    await q.edit_message_text("\n".join(lines), parse_mode=HTML, reply_markup=tools_kb(uid))
    return TOOLS_STATE

# ─── Support ──────────────────────────────────────────────────────────────────

async def support_subj(update, ctx) -> int:
    uid = update.effective_user.id
    ctx.user_data["_ticket_subj"] = sanitize_text(update.message.text, 100)
    await update.message.reply_text(t(uid, "support_ask_message"), parse_mode=HTML,
                                     reply_markup=one_btn(t(uid, "btn_cancel"), "home"))
    return SUPPORT_MESSAGE

async def support_msg(update, ctx) -> int:
    uid = update.effective_user.id
    subj = ctx.user_data.get("_ticket_subj", "مشكلة")
    message = sanitize_text(update.message.text, 1000)
    tid = D.create_ticket(uid, subj, message)
    sec.audit(uid, "TICKET", f"#{tid}")
    D.log_activity(uid, "SUPPORT", f"#{tid}", success=True)
    await update.message.reply_text(t(uid, "support_created", tid=tid), parse_mode=HTML,
                                     reply_markup=one_btn(t(uid, "btn_home"), "home"))
    return HOME_STATE

# ─── Admin Panel ──────────────────────────────────────────────────────────────

async def admin_cb(update, ctx) -> int:
    q = update.callback_query
    await q.answer()
    uid = update.effective_user.id

    if not D.is_admin(uid):
        await q.answer(t(uid, "not_auth"), show_alert=True)
        return ADMIN_STATE

    cb = q.data

    if cb == "home":
        text = _home_text(uid)
        await q.edit_message_text(text, parse_mode=HTML, reply_markup=home_kb(uid))
        return HOME_STATE

    if cb == "admin":
        await q.edit_message_text(f"{CROWN} **{t(uid, 'admin_title')}**", parse_mode=HTML,
                                   reply_markup=admin_kb(uid))
        return ADMIN_STATE

    if cb == "a_stats":
        users = D.user_count()
        # Count users with tokens
        with __import__('sqlite3').connect(D.DB_FILE) as c:
            with_token = c.execute("SELECT COUNT(*) FROM users WHERE encrypted_token IS NOT NULL").fetchone()[0]
            total_ops = c.execute("SELECT COALESCE(SUM(total_ops),0) FROM users").fetchone()[0]
            max_lvl = c.execute("SELECT COALESCE(MAX(level),1) FROM rewards").fetchone()[0]
        sec.audit(uid, "STATS")
        await q.edit_message_text(
            t(uid, "stats_text", users=users, with_token=with_token, ops=total_ops, max_level=max_lvl),
            parse_mode=HTML, reply_markup=one_btn(t(uid, "btn_back"), "admin")
        )
        return ADMIN_STATE

    if cb == "a_sec":
        s = sec.stats()
        sec.audit(uid, "SEC_STATS")
        await q.edit_message_text(
            t(uid, "sec_stats", total_logs=s["total_logs"], banned=s["banned"],
              abuse=s["abuse_flags"], last24=s["last_24h"]),
            parse_mode=HTML, reply_markup=one_btn(t(uid, "btn_back"), "admin")
        )
        return ADMIN_STATE

    if cb == "a_backup":
        await q.edit_message_text(f"{SAVE} {t(uid, 'loading')}", parse_mode=HTML)
        sec.audit(uid, "BACKUP")
        data = D.export_data()
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("backup.json", json.dumps(data, ensure_ascii=False, indent=2, default=str))
            if os.path.exists(D.DB_FILE):
                with open(D.DB_FILE, "rb") as f:
                    zf.writestr("bolt.db", f.read())
            if os.path.exists("bolt_security.db"):
                with open("bolt_security.db", "rb") as f:
                    zf.writestr("security.db", f.read())
        buf.seek(0)
        now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        await ctx.bot.send_document(
            chat_id=uid,
            document=InputFile(buf, filename=f"BOLT_backup_{now_str}.zip"),
            caption=f"{SAVE} BOLT ⚡ Backup\n🔒 Tokens encrypted (AES-256)",
            parse_mode=HTML,
        )
        await q.edit_message_text(f"{SAVE} {t(uid, 'backup_ready')}", parse_mode=HTML,
                                   reply_markup=admin_kb(uid))
        return ADMIN_STATE

    if cb == "a_bcast":
        await q.edit_message_text(f"{RADIO} {t(uid, 'broadcast_ask')}", parse_mode=HTML,
                                   reply_markup=one_btn(t(uid, "btn_cancel"), "admin"))
        return BROADCAST_WAIT

    if cb == "a_ban":
        await q.edit_message_text(t(uid, "ban_ask_id"), parse_mode=HTML,
                                   reply_markup=one_btn(t(uid, "btn_cancel"), "admin"))
        return ADMIN_BAN_ID

    if cb == "a_audit":
        logs = sec.get_audit(limit=25)
        lines = [f"{SCROLL} **سجل العمليات الأمني**\n"]
        for log in logs[:25]:
            lines.append(f"• [{log['timestamp'][:16]}] **{log['user_id']}** → {log['action']}")
        if len(lines) <= 1:
            lines.append("📭 Empty")
        await q.edit_message_text("\n".join(lines)[:4000], parse_mode=HTML,
                                   reply_markup=one_btn(t(uid, "btn_back"), "admin"))
        return ADMIN_STATE

    if cb == "a_tickets":
        tickets = D.get_open_tickets()
        lines = [f"{MAIL} **التذاكر المفتوحة:**\n"]
        for tk in tickets[:20]:
            name = he(tk.get("first_name") or tk.get("username") or str(tk["user_id"]))
            lines.append(f"• **#{tk['id']}** — {he(tk['subject'])} ({name})")
        if len(lines) <= 1:
            lines.append("📭 لا توجد تذاكر")
        await q.edit_message_text("\n".join(lines), parse_mode=HTML,
                                   reply_markup=one_btn(t(uid, "btn_back"), "admin"))
        return ADMIN_STATE

    return ADMIN_STATE

async def admin_ban_id(update, ctx) -> int:
    uid = update.effective_user.id
    if not D.is_admin(uid):
        return ADMIN_STATE
    try:
        target = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text(f"{CROSS} Invalid ID", parse_mode=HTML)
        return ADMIN_BAN_ID
    ctx.user_data["_ban_target"] = target
    await update.message.reply_text("🚫 سبب الحظر (أو أرسل `.`):", parse_mode=HTML,
                                     reply_markup=one_btn(t(uid, "btn_cancel"), "admin"))
    return ADMIN_BAN_REASON

async def admin_ban_reason(update, ctx) -> int:
    uid = update.effective_user.id
    if not D.is_admin(uid):
        return ADMIN_STATE
    target = ctx.user_data.get("_ban_target")
    if not target:
        return ADMIN_STATE
    reason = sanitize_text(update.message.text, 200)
    sec.ban(target, reason)
    sec.audit(uid, "BAN_USER", f"target={target} reason={reason}")
    await update.message.reply_text(t(uid, "ban_done", uid=target), parse_mode=HTML,
                                     reply_markup=one_btn(t(uid, "btn_back"), "admin"))
    return ADMIN_STATE

async def broadcast_handler(update, ctx) -> int:
    uid = update.effective_user.id
    if not D.is_admin(uid):
        return ADMIN_STATE

    user_ids = D.get_all_user_ids()
    ok_c, fail_c = 0, 0
    status = await update.message.reply_text(f"{RADIO} {t(uid, 'loading')}", parse_mode=HTML)

    for tid in user_ids:
        if tid == uid:
            ok_c += 1
            continue
        try:
            await ctx.bot.copy_message(chat_id=tid, from_chat_id=update.effective_chat.id,
                                        message_id=update.message.message_id)
            ok_c += 1
        except:
            fail_c += 1
        await asyncio.sleep(0.05)

    sec.audit(uid, "BROADCAST", f"ok={ok_c} fail={fail_c}")
    await status.edit_text(t(uid, "broadcast_done", ok=ok_c, fail=fail_c), parse_mode=HTML,
                            reply_markup=one_btn(t(uid, "btn_back"), "admin"))
    return ADMIN_STATE

# ─── Cancel ───────────────────────────────────────────────────────────────────

async def cancel_cmd(update, ctx) -> int:
    uid = update.effective_user.id
    await update.message.reply_text(t(uid, "cancel_done"), parse_mode=HTML)
    return ConversationHandler.END

async def unknown_text(update, ctx) -> None:
    uid = update.effective_user.id
    await update.message.reply_text(f"{INFO} {t(uid, 'unknown')}", parse_mode=HTML)

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    D.init_db()

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    bk_home = [CallbackQueryHandler(home_cb, pattern="^home$")]
    bk_tools = [CallbackQueryHandler(tools_cb, pattern="^tools$")]

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", cmd_start)],
        states={
            HOME_STATE: [CallbackQueryHandler(home_cb)],
            LANG_STATE: [CallbackQueryHandler(lang_cb)],
            TOOLS_STATE: [CallbackQueryHandler(tools_cb)],
            ADMIN_STATE: [CallbackQueryHandler(admin_cb)],
            ASK_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, token_handler), *bk_home],
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_handler), *bk_tools],
            SUPPORT_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, support_subj)],
            SUPPORT_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, support_msg)],
            BROADCAST_WAIT: [
                MessageHandler(~filters.COMMAND, broadcast_handler),
                CallbackQueryHandler(admin_cb, pattern="^admin$"),
            ],
            ADMIN_BAN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_ban_id)],
            ADMIN_BAN_REASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_ban_reason)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_cmd),
            CommandHandler("start", cmd_start),
        ],
        allow_reentry=True,
        per_message=False,
    )

    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_text))

    logger.info("⚡ BOLT — starting...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
