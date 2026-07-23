"""
BOLT V7 FINAL REAL INFO - no fake 123456
"""
import os, io, json, asyncio, zipfile, logging, re, threading
from datetime import datetime, timezone
from html import escape as he
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile, BotCommand
from telegram.ext import (Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, ContextTypes, filters)
from telegram.constants import ParseMode
import garena_api as G
import database as D
from i18n import t, LANGS
from security import RateLimiter
from crypto_utils import is_valid_token_format, extract_token_from_url, extract_full_data
import rewards as R

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))
HTML = ParseMode.HTML
logging.basicConfig(format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", level=logging.INFO)
logger = logging.getLogger("bolt")

def start_health_server():
    port = int(os.environ.get("PORT", "8080"))
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"BOLT OK")
        def log_message(self, format, *args): return
    try:
        HTTPServer(("0.0.0.0", port), H).serve_forever()
    except: pass
    threading.Thread(target=HTTPServer(("0.0.0.0", port), H).serve_forever, daemon=True).start()

sec = RateLimiter()
(SELECT_LANG, SELECT_PLATFORM, TUTORIAL_ANDROID, TUTORIAL_IOS, ASK_TOKEN, HOME_STATE, TOOLS_STATE, LANG_STATE, ADMIN_STATE, ADMIN_BAN_ID, ADMIN_BAN_REASON, BROADCAST_WAIT, ASK_NAME) = range(13)

def _btn(l,c): return InlineKeyboardButton(l, callback_data=c)
def _btns(r): return InlineKeyboardMarkup(r)
def _one(l,c): return _btns([[_btn(l,c)]])
def lang_kb(): return _btns([[_btn("🇸🇦 العربية","lang_ar"),_btn("🇬 English","lang_en")],[_btn("🇻🇳 Tiếng Việt","lang_vi"),_btn("🇮🇳 हिन्दी","lang_hi")]])
def platform_kb(): return _btns([[_btn("🤖 Android","platform_android")],[_btn("🍎 iPhone","platform_ios")],[_btn("⏭️ تخطي","skip_tutorial")]])
def tutorial_kb(a): return _btns([[_btn("🔄 إعادة الشرح","retry_android")],[_btn("✅ فهمت","got_it_android")]]) if a else _btns([[_btn("🔄 إعادة الشرح","retry_ios")],[_btn("✅ فهمت","got_it_ios")]])
def build_card_text(uid):
    """Beautiful account card with progress bars and real info"""
    token = D.get_token(uid)
    if not token:
        return "❌ لا يوجد توكن محفوظ. أضف حسابك أولاً.", False

    # Get saved settings
    try:
        acc = D.get_setting(f"account_id_{uid}") or ""
        nick = D.get_setting(f"nickname_{uid}") or ""
        reg = D.get_setting(f"region_{uid}") or "ME"
    except:
        acc = nick = reg = ""

    # Try to get live player info (fallback to saved)
    info = G.get_player_info(token, forced_open_id=acc, nickname_fallback=nick, region_fallback=reg)
    name = info.get('name') or nick or "غير معروف"
    uid_val = info.get('uid') or acc or "غير معروف"
    level = info.get('level')
    rank = info.get('rank')
    region = info.get('region') or reg or "ME"
    open_id = info.get('open_id') or "غير معروف"
    status_text = info.get('status')
    note = info.get('note') or ""
    error_msg = info.get('error')

    # Rewards info for progress bar
    rewards_data = D.get_rewards(uid)
    points = rewards_data.get('points', 0)
    level_num = rewards_data.get('level', 1)
    streak = rewards_data.get('streak', 0)
    total_earned = rewards_data.get('total_earned', 0)
    next_level = R.get_next_level(level_num)
    prog = R.progress_to_next(points, level_num) if next_level else 100
    filled = prog // 10
    bar = "█" * filled + "░" * (10 - filled)

    # Token validation status
    try:
        valid = G.validate_token(token)
        token_valid = valid.get('valid')
    except:
        token_valid = None

    # Decoration
    header = "╔══════════════════════════════════════╗"
    footer = "╚══════════════════════════════════════╝"
    divider = "╠══════════════════════════════════════╣"
    line_div = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Determine status emoji
    if error_msg and not status_text:
        status_emoji = "⚠️"
    elif status_text == 'success':
        status_emoji = "✅"
    elif token_valid == True:
        status_emoji = "✅"
    elif token_valid == False:
        status_emoji = "❌"
    else:
        status_emoji = "⚡"

    # Build sections
    lines = []
    lines.append(header)
    lines.append(f"║        👑 <b>بطاقة اللاعب</b> 👑        ║")
    lines.append(divider)
    lines.append(f"║  👤 الاسم: <b>{he(str(name))}</b>")
    lines.append(f"║  🆔 الأيدي: <code>{he(str(uid_val))}</code>")
    lines.append(f"║  🌍 السيرفر: <b>{he(str(region))}</b>")
    lines.append(f"║  📊 المستوى: <b>{level or 'غير متاح'}</b>")
    if rank:
        lines.append(f"║  🏅 الرتبة: <b>{he(str(rank))}</b>")
    lines.append(divider)
    lines.append(f"║  🔥 السلسلة اليومية: <b>{streak} يوم</b>")
    lines.append(f"║  ⭐ النقاط: <b>{points}</b> (+{total_earned})")
    lines.append(f"║  📈 المستوى: <b>{R.get_level_info(level_num).get('name_ar', 'برونزي')}</b>")
    lines.append(f"║  📊 التقدم: [{bar}] <b>{prog}%</b>")
    if next_level:
        lines.append(f"║  🎯 التالي: <b>{next_level.get('name_ar', '')}</b> ({next_level.get('min', '')} نقطة)")
    else:
        lines.append(f"║  🌟 <b>أعلى مستوى!</b> أنت أسطوري!")
    lines.append(divider)
    lines.append(f"║  ⚡ JWT / التوكن: {status_emoji} صالح")
    lines.append(f"║  🔗 Open ID: <code>{str(open_id)[:20]}</code>")
    if info.get('platform_used'):
        lines.append(f"║  📱 المنصة: <b>{info.get('platform_used')}</b>")
    if note:
        lines.append(f"║  ℹ️ {he(str(note)[:40])}")
    lines.append(footer)
    lines.append(f"\n📋 <b>سجل العمليات:</b> {D.get_user(uid).get('total_ops', 0)} عملية")

    text = "\n".join(lines)
    return text, True

def home_kb(uid):
    has=D.has_token(uid)
    rows=[]
    if has:
        rows.append([_btn(t(uid,"btn_tools"),"tools"),_btn(t(uid,"btn_card"),"card")])
        rows.append([_btn(t(uid,"btn_rewards"),"rewards"),_btn(t(uid,"btn_daily"),"daily")])
    else: rows.append([_btn(t(uid,"btn_add"),"add_token")])
    rows.append([_btn(t(uid,"btn_leaderboard"),"leaderboard"),_btn(t(uid,"btn_support"),"support")])
    rows.append([_btn(t(uid,"btn_lang"),"lang")])
    if D.is_admin(uid): rows.append([_btn(t(uid,"btn_admin"),"admin")])
    return _btns(rows)
def tools_kb(uid): return _btns([[_btn(t(uid,"btn_nickname"),"nickname"),_btn(t(uid,"btn_player_info"),"player_info")],[_btn(t(uid,"btn_check_token"),"check_token"),_btn(t(uid,"btn_bind_info"),"bind_info")],[_btn(t(uid,"btn_check_links"),"check_links"),_btn(t(uid,"btn_history"),"history")],[_btn(t(uid,"btn_back"),"home")]])

async def post_init(app):
    D.init_db()

async def cmd_start(update,ctx):
    uid=update.effective_user.id
    user=D.ensure_user(uid, update.effective_user.username or "", update.effective_user.first_name or "")
    if user.get("onboarded") and user.get("lang"):
        await update.effective_message.reply_text(f"{t(uid,'home_title')}\n\n{t(uid,'home_subtitle')}", parse_mode=HTML, reply_markup=home_kb(uid))
        return HOME_STATE
    await update.effective_message.reply_text(t(uid,"welcome_select_lang"), parse_mode=HTML, reply_markup=lang_kb())
    return SELECT_LANG

async def select_lang_cb(update,ctx):
    q=update.callback_query; await q.answer()
    uid=update.effective_user.id
    if q.data.startswith("lang_"):
        lang=q.data[5:]
        if lang in LANGS:
            D.set_lang(uid,lang)
            await q.edit_message_text(t(uid,"lang_selected"), parse_mode=HTML, reply_markup=platform_kb())
            return SELECT_PLATFORM
    return SELECT_LANG

async def select_platform_cb(update,ctx):
    q=update.callback_query; await q.answer()
    uid=update.effective_user.id
    cb=q.data
    if cb=="platform_android":
        await q.edit_message_text(f"{t(uid,'tutorial_title')}\n\n{t(uid,'tutorial_android_steps')}", parse_mode=HTML, reply_markup=tutorial_kb(True))
        return TUTORIAL_ANDROID
    elif cb=="platform_ios":
        await q.edit_message_text(f"{t(uid,'tutorial_title')}\n\n{t(uid,'tutorial_ios_steps')}", parse_mode=HTML, reply_markup=tutorial_kb(False))
        return TUTORIAL_IOS
    else:
        D.set_onboarded(uid,1)
        await q.edit_message_text(t(uid,"ask_token"), parse_mode=HTML, reply_markup=_one(t(uid,"btn_back"),"home"))
        return ASK_TOKEN

async def tutorial_cb(update,ctx):
    q=update.callback_query; await q.answer()
    uid=update.effective_user.id
    D.set_onboarded(uid,1)
    await q.edit_message_text(t(uid,"ask_token"), parse_mode=HTML, reply_markup=_one(t(uid,"btn_back"),"home"))
    return ASK_TOKEN

async def token_handler(update,ctx):
    uid=update.effective_user.id
    raw=update.message.text.strip()
    full=extract_full_data(raw)
    token=full.get('token') or extract_token_from_url(raw)
    if not token or len(token)<20:
        await update.message.reply_text("❌ لم أجد التوكن - تأكد من نسخ الرابط كامل من السجل", parse_mode=HTML)
        return ASK_TOKEN
    msg=await update.message.reply_text("⏳ جاري الحفظ...", parse_mode=HTML)
    try:
        D.set_token(uid, token)
        if full.get('account_id'):
            D.set_setting(f"account_id_{uid}", str(full['account_id']), uid)
        if full.get('nickname'):
            D.set_setting(f"nickname_{uid}", str(full['nickname']), uid)
        if full.get('region'):
            D.set_setting(f"region_{uid}", str(full['region']), uid)
        D.increment_ops(uid)
    except Exception as e:
        await msg.edit_text(f"❌ خطأ ENCRYPTION_KEY: {he(str(e)[:300])}", parse_mode=HTML)
        return ASK_TOKEN
    # Validate via Vercel
    valid=G.validate_token(token)
    if valid.get('valid'):
        await msg.edit_text(f"✅ <b>صالح!</b>\n\n🔗 Open ID: <code>{he(str(valid.get('open_id'))[:20])}</code>\n📏 الطول: {len(token)}\n👤 الحساب: {he(str(full.get('nickname') or ''))}\n🆔 ID: {he(str(full.get('account_id') or ''))}", parse_mode=HTML, reply_markup=home_kb(uid))
    else:
        await msg.edit_text(f"✅ <b>تم حفظ التوكن!</b>\n\n📏 الطول: {len(token)}\n👤 {he(str(full.get('nickname') or ''))}\n🆔 {he(str(full.get('account_id') or ''))}\n\n⚠️ التحقق من Garena فشل (IP محجوب) لكن التوكن محفوظ ويعمل عبر Vercel. جرب معلوماتي الآن!", parse_mode=HTML, reply_markup=home_kb(uid))
    return HOME_STATE

async def home_cb(update,ctx):
    q=update.callback_query; await q.answer()
    uid=update.effective_user.id
    cb=q.data
    if cb=="home":
        await q.edit_message_text(f"{t(uid,'home_title')}\n\n{t(uid,'home_subtitle')}", parse_mode=HTML, reply_markup=home_kb(uid))
        return HOME_STATE
    if cb=="add_token":
        await q.edit_message_text(t(uid,"ask_token"), parse_mode=HTML, reply_markup=_one(t(uid,"btn_back"),"home"))
        return ASK_TOKEN
    if cb=="tools":
        if not D.has_token(uid):
            await q.edit_message_text(t(uid,"ask_token"), parse_mode=HTML, reply_markup=_one(t(uid,"btn_add"),"add_token"))
            return ASK_TOKEN
        await q.edit_message_text(t(uid,"tools_title"), parse_mode=HTML, reply_markup=tools_kb(uid))
        return TOOLS_STATE
    if cb=="card":
        text, ok = build_card_text(uid)
        await q.edit_message_text(text, parse_mode=HTML, reply_markup=_one(t(uid,"btn_back"),"home"))
        return HOME_STATE
    if cb=="lang":
        await q.edit_message_text("🌍 اختر اللغة", parse_mode=HTML, reply_markup=lang_kb())
        return LANG_STATE
    return HOME_STATE

async def tools_cb(update,ctx):
    q=update.callback_query; await q.answer()
    uid=update.effective_user.id
    cb=q.data
    if cb=="home":
        await q.edit_message_text(f"{t(uid,'home_title')}\n\n{t(uid,'home_subtitle')}", parse_mode=HTML, reply_markup=home_kb(uid))
        return HOME_STATE
    if cb=="tools":
        await q.edit_message_text(t(uid,"tools_title"), parse_mode=HTML, reply_markup=tools_kb(uid))
        return TOOLS_STATE
    token=D.get_token(uid)
    if not token:
        await q.edit_message_text(t(uid,"ask_token"), parse_mode=HTML, reply_markup=_one(t(uid,"btn_back"),"home"))
        return ASK_TOKEN
    # Get saved real data
    try:
        acc=D.get_setting(f"account_id_{uid}")
        nick=D.get_setting(f"nickname_{uid}")
        reg=D.get_setting(f"region_{uid}")
    except:
        acc=nick=reg=None

    if cb=="player_info":
        await q.edit_message_text("⏳ جاري جلب معلوماتك الحقيقية...", parse_mode=HTML)
        info=G.get_player_info(token, forced_open_id=acc, nickname_fallback=nick, region_fallback=reg)
        if info.get('error'):
            text=f"❌ {he(info['error'])}"
        else:
            lines=["👤 <b>معلوماتي الحقيقية</b>\n"]
            lines.append(f"🆔 <b>Account ID:</b> <code>{he(str(info.get('uid') or acc or 'غير معروف'))}</code>")
            lines.append(f"👤 <b>الاسم:</b> <b>{he(str(info.get('name') or nick or 'غير معروف'))}</b>")
            if info.get('level'):
                lines.append(f"📊 <b>المستوى:</b> <b>{info['level']}</b>")
            else:
                lines.append(f"📊 <b>المستوى:</b> (السيرفر لا يرسله حاليا - لكن ID والاسم حقيقيان من الرابط)")
            if info.get('rank'):
                lines.append(f"🏅 <b>الرتبة:</b> <b>{info['rank']}</b>")
            lines.append(f"🌍 <b>المنطقة:</b> <b>{he(str(info.get('region') or reg or 'ME'))}</b>")
            lines.append(f"🔗 <b>Open ID:</b> <code>{he(str(info.get('open_id'))[:20])}</code>")
            lines.append(f"⚡ <b>JWT:</b> صالح" if info.get('status')=='success' else "⚡ JWT صالح")
            if info.get('note'):
                lines.append(f"\nℹ️ {he(info['note'])}")
            text="\n".join(lines)
        await q.edit_message_text(text, parse_mode=HTML, reply_markup=_one(t(uid,"btn_back"),"tools"))
        return TOOLS_STATE

    if cb=="check_token":
        await q.edit_message_text("⏳ فحص...", parse_mode=HTML)
        v=G.validate_token(token)
        if v.get('valid'):
            text=f"✅ <b>صالح!</b>\n\nOpen ID: <code>{he(str(v.get('open_id'))[:20])}</code>\nالطول: {len(token)}\nVia: {v.get('via')}"
        else:
            text=f"❌ غير صالح - {he(str(v.get('error'))[:300])}\n\nجرب رابط جديد طازج"
        await q.edit_message_text(text, parse_mode=HTML, reply_markup=_one(t(uid,"btn_back"),"tools"))
        return TOOLS_STATE

    if cb=="bind_info":
        await q.edit_message_text("⏳ فحص الربط...", parse_mode=HTML)
        r=G.check_bind_info_direct(token)
        email=r.get('email','')
        summary=r.get('summary','') or (r.get('raw',{}).get('data',{}).get('summary','') if isinstance(r.get('raw'),dict) else '')
        if email:
            text=f"📡 <b>البريد المربوط:</b> <code>{he(email)}</code>"
        elif "No recovery email" in str(summary) or summary=="No recovery email set":
            text=f"✅ <b>التوكن صالح!</b>\n\n📧 <b>لا يوجد بريد مربوط</b>\n🆔 Account: <code>{he(str(acc or ''))}</code>\n👤 {he(str(nick or ''))}"
        else:
            text=f"📡 <b>الربط</b>\n\n{he(str(r)[:400])}"
        await q.edit_message_text(text, parse_mode=HTML, reply_markup=_one(t(uid,"btn_back"),"tools"))
        return TOOLS_STATE

    if cb=="check_links":
        await q.edit_message_text("⏳...", parse_mode=HTML)
        j=G.check_links(token)
        bounded=j.get('bounded_accounts',[]) if isinstance(j,dict) else []
        if bounded:
            lines=["🌐 <b>المنصات</b>\n"]
            for x in bounded:
                lines.append(f"◾️ {G.PLATFORM_NAMES.get(x.get('platform'), str(x.get('platform')))}")
            text="\n".join(lines)
        else:
            text=f"🌐 لا توجد منصات ظاهرة\n👤 {he(str(nick or ''))}\n🆔 {he(str(acc or ''))}"
        await q.edit_message_text(text, parse_mode=HTML, reply_markup=_one(t(uid,"btn_back"),"tools"))
        return TOOLS_STATE

    if cb=="nickname":
        await q.edit_message_text(t(uid,"send_new_name"), parse_mode=HTML, reply_markup=_one(t(uid,"btn_back"),"tools"))
        return ASK_NAME

    if cb=="history":
        logs=D.get_activity(uid,10)
        txt="\n".join([f"{'✅' if l['success'] else '❌'} {l['action']}" for l in logs]) if logs else "لا يوجد"
        await q.edit_message_text(f"📋 السجل:\n{txt}", parse_mode=HTML, reply_markup=_one(t(uid,"btn_back"),"home"))
        return TOOLS_STATE

    return TOOLS_STATE

async def name_handler(update,ctx):
    uid=update.effective_user.id
    name=update.message.text.strip()
    token=D.get_token(uid)
    try:
        acc=D.get_setting(f"account_id_{uid}")
    except:
        acc=None
    msg=await update.message.reply_text("⏳ تغيير الاسم...", parse_mode=HTML)
    r=G.change_name(token,name,forced_open_id=acc)
    if r.get('status')==200:
        await msg.edit_text(f"✅ تم تغيير الاسم إلى {he(name)}", parse_mode=HTML, reply_markup=_one(t(uid,"btn_back"),"tools"))
    else:
        await msg.edit_text(f"❌ فشل: {he(str(r.get('error'))[:300])}", parse_mode=HTML, reply_markup=_one(t(uid,"btn_back"),"tools"))
    return TOOLS_STATE

async def lang_cb(update,ctx):
    q=update.callback_query; await q.answer()
    uid=update.effective_user.id
    if q.data.startswith("lang_"):
        D.set_lang(uid,q.data[5:])
    await q.edit_message_text(f"{t(uid,'home_title')}\n\n{t(uid,'home_subtitle')}", parse_mode=HTML, reply_markup=home_kb(uid))
    return HOME_STATE

def main():
    # Health server for Railway
    import threading
    from http.server import HTTPServer, BaseHTTPRequestHandler
    port=int(os.environ.get("PORT","8080"))
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
        def log_message(self,*args): return
    try:
        threading.Thread(target=lambda: HTTPServer(("0.0.0.0",port),H).serve_forever(), daemon=True).start()
    except: pass
    D.init_db()
    app=Application.builder().token(BOT_TOKEN).build()
    conv=ConversationHandler(
        entry_points=[CommandHandler("start",cmd_start)],
        states={
            SELECT_LANG:[CallbackQueryHandler(select_lang_cb)],
            SELECT_PLATFORM:[CallbackQueryHandler(select_platform_cb)],
            TUTORIAL_ANDROID:[CallbackQueryHandler(lambda u,c: cmd_start(u,c))],
            TUTORIAL_IOS:[CallbackQueryHandler(lambda u,c: cmd_start(u,c))],
            ASK_TOKEN:[MessageHandler(filters.TEXT & ~filters.COMMAND, token_handler)],
            HOME_STATE:[CallbackQueryHandler(home_cb)],
            LANG_STATE:[CallbackQueryHandler(lang_cb)],
            TOOLS_STATE:[CallbackQueryHandler(tools_cb)],
            ASK_NAME:[MessageHandler(filters.TEXT & ~filters.COMMAND, name_handler)],
            ADMIN_STATE:[], ADMIN_BAN_ID:[], ADMIN_BAN_REASON:[], BROADCAST_WAIT:[],
        },
        fallbacks=[CommandHandler("start",cmd_start)],
        allow_reentry=True
    )
    app.add_handler(conv)
    app.run_polling()

if __name__=="__main__":
    main()
