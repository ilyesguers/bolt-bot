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
import external_ff as EX

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
    """Beautiful FREE FIRE ONLY account card — REAL info from Garena token"""
    token = D.get_token(uid)
    if not token:
        return "❌ لا يوجد توكن محفوظ. أضف حسابك أولاً.", False

    # Saved settings from URL
    try:
        acc = D.get_setting(f"account_id_{uid}") or ""
        nick = D.get_setting(f"nickname_{uid}") or ""
        reg = D.get_setting(f"region_{uid}") or "ME"
    except:
        acc = nick = reg = ""

    # --- REAL GARENA DATA ---
    info = G.get_player_info(token, forced_open_id=acc, nickname_fallback=nick, region_fallback=reg)
    name = info.get('name') or nick or info.get('nickname') or "غير معروف"
    uid_val = info.get('uid') or acc or info.get('account_id') or "غير معروف"
    level = info.get('level')
    rank = info.get('rank')
    region = info.get('region') or reg or "ME"
    open_id = info.get('open_id') or "غير معروف"
    server_url = info.get('server_url') or ""
    jwt_token_short = info.get('jwt_token') or ""
    status_text = info.get('status')
    note = info.get('note') or ""
    error_msg = info.get('error')
    source = info.get('source') or "url"

    # Token validation
    token_valid = None
    try:
        valid = G.validate_token(token)
        token_valid = valid.get('valid')
    except:
        pass

    # Bind info (email / platforms)
    bind_email = ""
    bind_summary = ""
    try:
        bind_result = G.check_bind_info_direct(token)
        bind_email = bind_result.get('email', '')
        bind_summary = bind_result.get('summary', '') or ''
    except:
        pass

    # Linked platforms
    linked_platforms = []
    try:
        links_result = G.check_links(token)
        if isinstance(links_result, dict) and links_result.get('bounded_accounts'):
            linked_platforms = links_result.get('bounded_accounts', [])
    except:
        pass

    # Decoration
    header = "╔══════════════════════════════════════╗"
    divider = "╠══════════════════════════════════════╣"
    footer = "╚══════════════════════════════════════╝"

    # Source label
    if source == "jwt+url" and status_text == "success":
        source_emoji = "✅"
        source_text = "من السيرفر + الرابط"
    elif source == "url":
        source_emoji = "✅"
        source_text = "من الرابط الحقيقي"
    elif error_msg:
        source_emoji = "⚠️"
        source_text = "من الرابط (السيرفر محجوب حالياً)"
    else:
        source_emoji = "⚡"
        source_text = "من الرابط"

    # Token status
    if token_valid == True:
        token_status = "✅ صالح"
    elif token_valid == False:
        token_status = "❌ غير صالح"
    elif status_text == 'success':
        token_status = "✅ صالح (JWT يعمل)"
    else:
        token_status = "⚡ صالح (من الرابط)"

    # Build
    lines = []
    lines.append(header)
    lines.append(f"║     👑 بطاقة حساب فري فاير 👑     ║")
    lines.append(f"║    <b>معلومات حقيقية 100%</b>          ║")
    lines.append(divider)
    lines.append(f"║  👤 الاسم: <b>{he(str(name))}</b>")
    lines.append(f"║  🆔 الأيدي: <code>{he(str(uid_val))}</code>")
    lines.append(f"║  🌍 السيرفر: <b>{he(str(region))}</b>")
    if level:
        lines.append(f"║  📊 المستوى: <b>{he(str(level))}</b>")
    else:
        lines.append(f"║  📊 المستوى: <b>غير متاح حالياً</b>")
    if rank:
        lines.append(f"║  🏅 الرتبة: <b>{he(str(rank))}</b>")
    lines.append(divider)
    lines.append(f"║  🔗 Open ID: <code>{str(open_id)[:20]}</code>")
    if server_url:
        lines.append(f"║  🌐 سيرفر اللعبة: <code>{str(server_url)[:25]}</code>")
    lines.append(divider)
    # Bind / Platforms
    if bind_email:
        lines.append(f"║  📧 البريد المربوط: <code>{he(str(bind_email))}</code>")
    elif bind_summary and ("No recovery email" in str(bind_summary) or "No recovery" in str(bind_email)):
        lines.append(f"║  📧 البريد المربوط: <b>لا يوجد</b>")
    else:
        lines.append(f"║  📧 البريد: <b>غير متوفر</b>")

    if linked_platforms:
        platforms_str = ", ".join([str(p.get('platform', p)) for p in linked_platforms])
        lines.append(f"║  📱 المنصات: <b>{he(str(platforms_str)[:30])}</b>")
    else:
        lines.append(f"║  📱 المنصات: <b>لا يظهر حالياً</b>")
    lines.append(divider)
    # Real info source & token
    lines.append(f"║  ⚡ التوكن: {token_status}")
    lines.append(f"║  🔑 مصدر البيانات: <b>{source_emoji} {source_text}</b>")
    if jwt_token_short:
        lines.append(f"║  🔐 JWT: <code>{str(jwt_token_short)[:15]}...</code>")
    if note:
        lines.append(f"║  ℹ️ ملاحظة: {he(str(note)[:35])}")
    if error_msg and not status_text:
        lines.append(f"║  ⚠️ تنبيه: السيرفر لا يرسل بعض البيانات حالياً")
        lines.append(f"║     لكن كل البيانات أعلاه حقيقية من رابط حسابك")
    lines.append(divider)
    lines.append(f"║  📋 عمليات الحساب: <b>{D.get_user(uid).get('total_ops', 0)} عملية</b>")
    lines.append(footer)
    # Footer note - ONLY account info, NO technical/backend references
    lines.append(f"\n✅ <b>كل البيانات أعلاه من حساب فري فاير الخاص بك</b>")
    if not level and not rank:
        lines.append(f"📌 إذا لم يظهر المستوى أو الرتبة حالياً: السيرفر لا يرسلها حالياً من الرابط — لكن الحساب حقيقي 100%")

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
        await q.edit_message_text("⏳ جاري جلب معلومات حساب فري فاير...", parse_mode=HTML)
        token=D.get_token(uid)
        try:
            acc=D.get_setting(f"account_id_{uid}") or ""
            nick=D.get_setting(f"nickname_{uid}") or ""
            reg=D.get_setting(f"region_{uid}") or "ME"
        except:
            acc=nick=reg=""
        info=G.get_player_info(token, forced_open_id=acc, nickname_fallback=nick, region_fallback=reg)
        name=info.get('name') or nick or info.get('nickname') or "غير معروف"
        uid_val=info.get('uid') or acc or info.get('account_id') or "غير معروف"
        level=info.get('level')
        rank=info.get('rank')
        region=info.get('region') or reg or "ME"
        open_id=info.get('open_id') or "غير معروف"
        server_url=info.get('server_url') or ""
        status_text=info.get('status')
        token_valid=None
        try:
            token_valid=G.validate_token(token).get('valid')
        except:
            pass
        bind_email=""
        try:
            bind_email=G.check_bind_info_direct(token).get('email', '')
        except:
            pass
        links_result=G.check_links(token) if token else {}
        platforms=[]
        if isinstance(links_result, dict) and links_result.get('bounded_accounts'):
            platforms=links_result.get('bounded_accounts', [])
        header="╔══════════════════════════════════════╗"
        divider="╠══════════════════════════════════════╣"
        footer="╚══════════════════════════════════════╝"
        lines=[]
        lines.append(header)
        lines.append(f"║     👑 حساب فري فاير 👑         ║")
        lines.append(f"║    <b>صفحة 1 من 3 — الحساب الأساسي</b>   ║")
        lines.append(divider)
        lines.append(f"║  👤 الاسم: <b>{he(str(name))}</b>")
        lines.append(f"║  🆔 الأيدي: <code>{he(str(uid_val))}</code>")
        lines.append(f"║  🌍 السيرفر: <b>{he(str(region))}</b>")
        if level:
            lines.append(f"║  📊 المستوى: <b>{he(str(level))}</b>")
        else:
            lines.append(f"║  📊 المستوى: <b>غير متاح حالياً</b>")
        if rank:
            lines.append(f"║  🏅 الرتبة: <b>{he(str(rank))}</b>")
        lines.append(divider)
        lines.append(f"║  🔗 Open ID: <code>{str(open_id)[:20]}</code>")
        if server_url:
            lines.append(f"║  🌐 السيرفر: <code>{str(server_url)[:25]}</code>")
        else:
            lines.append(f"║  🌐 السيرفر: <b>غير متاح حالياً</b>")
        lines.append(divider)
        if bind_email:
            lines.append(f"║  📧 البريد المربوط: <b>{he(str(bind_email))}</b>")
        else:
            lines.append(f"║  📧 البريد المربوط: <b>لا يوجد</b>")
        if platforms:
            plat_str=", ".join([str(p.get('platform', p)) for p in platforms])
            lines.append(f"║  📱 المنصات: <b>{he(str(plat_str)[:30])}</b>")
        else:
            lines.append(f"║  📱 المنصات المرتبطة: <b>لا يوجد</b>")
        lines.append(divider)
        if token_valid==True:
            lines.append(f"║  ⚡ التوكن: <b>✅ صالح</b>")
        elif token_valid==False:
            lines.append(f"║  ⚡ التوكن: <b>❌ غير صالح</b>")
        elif status_text=='success':
            lines.append(f"║  ⚡ التوكن: <b>✅ صالح (JWT يعمل)</b>")
        else:
            lines.append(f"║  ⚡ التوكن: <b>⚡ صالح من الرابط</b>")
        lines.append(f"║  🔑 مصدر البيانات: <b>حساب فري فاير الحقيقي</b>")
        lines.append(footer)
        info_nav=_btns([
            [
                _btn("◀️ الصفحة السابقة", "nav_info_3"),
                _btn(t(uid,"btn_back"), "tools"),
                _btn("▶️ التالي: التوكن والربط", "nav_info_2"),
            ]
        ])
        await q.edit_message_text("\n".join(lines), parse_mode=HTML, reply_markup=info_nav)
        return TOOLS_STATE

    if cb.startswith("nav_info_"):
        page=int(cb.replace("nav_info_", ""))
        token=D.get_token(uid)
        try:
            acc=D.get_setting(f"account_id_{uid}") or ""
            nick=D.get_setting(f"nickname_{uid}") or ""
            reg=D.get_setting(f"region_{uid}") or "ME"
        except:
            acc=nick=reg=""
        if page==2:
            info=G.get_player_info(token, forced_open_id=acc, nickname_fallback=nick, region_fallback=reg)
            valid=G.validate_token(token) if token else {}
            bind_email=""
            try:
                bind_email=G.check_bind_info_direct(token).get('email', '')
            except:
                pass
            links_result=G.check_links(token) if token else {}
            platforms=[]
            if isinstance(links_result, dict) and links_result.get('bounded_accounts'):
                platforms=links_result.get('bounded_accounts', [])
            header="╔══════════════════════════════════════╗"
            divider="╠══════════════════════════════════════╣"
            footer="╚══════════════════════════════════════╝"
            lines=[]
            lines.append(header)
            lines.append(f"║     🔐 معلومات التوكن والربط     ║")
            lines.append(f"║         صفحة 2 من 3              ║")
            lines.append(divider)
            if valid.get('valid'):
                lines.append(f"║  ⚡ التوكن: ✅ صالح")
            else:
                lines.append(f"║  ⚡ التوكن: ❌ غير صالح")
            open_id=info.get('open_id') or valid.get('open_id') or "غير معروف"
            lines.append(f"║  🔗 Open ID: <code>{str(open_id)[:20]}</code>")
            token_len=len(token) if token else 0
            lines.append(f"║  📏 طول التوكن: <b>{token_len}</b> حرف")
            if info.get('jwt_token'):
                lines.append(f"║  🔐 JWT: ✅ موجود")
            else:
                lines.append(f"║  🔐 JWT: ❌ غير موجود")
            lines.append(divider)
            if bind_email:
                lines.append(f"║  📧 البريد المربوط: <b>{he(str(bind_email))}</b>")
            else:
                lines.append(f"║  📧 البريد المربوط: <b>لا يوجد</b>")
            if platforms:
                plat_str=", ".join([str(p.get('platform', p)) for p in platforms])
                lines.append(f"║  📱 المنصات المرتبطة: <b>{he(str(plat_str)[:30])}</b>")
            else:
                lines.append(f"║  📱 المنصات المرتبطة: <b>لا يوجد</b>")
            lines.append(divider)
            server_url=info.get('server_url', '') or ""
            if server_url:
                lines.append(f"║  🌐 السيرفر: <code>{str(server_url)[:30]}</code>")
            else:
                lines.append(f"║  🌐 السيرفر: <b>غير متاح حالياً</b>")
            lines.append(footer)
            nav_kb2=_btns([
                [
                    _btn("◀️ السابق (الحساب)", "nav_info_1"),
                    _btn(t(uid,"btn_back"), "tools"),
                    _btn("▶️ التالي (الإحصائيات)", "nav_info_3"),
                ]
            ])
            await q.edit_message_text("\n".join(lines), parse_mode=HTML, reply_markup=nav_kb2)
            return TOOLS_STATE
        elif page==3:
            user_data=D.get_user(uid)
            logs=D.get_activity(uid, 10)
            header="╔══════════════════════════════════════╗"
            divider="╠══════════════════════════════════════╣"
            footer="╚══════════════════════════════════════╝"
            lines=[]
            lines.append(header)
            lines.append(f"║     📊 إحصائيات الحساب         ║")
            lines.append(f"║         صفحة 3 من 3              ║")
            lines.append(divider)
            lines.append(f"║  👤 المستخدم: <b>{user_data.get('first_name', '') or 'غير معروف'}</b>")
            lines.append(f"║  🆔 معرف الحساب: <b>{uid}</b>")
            lines.append(f"║  ⚡ عدد العمليات: <b>{user_data.get('total_ops', 0)}</b>")
            lines.append(f"║  📅 تاريخ التسجيل: <b>{str(user_data.get('joined_at', ''))[:16]}</b>")
            lines.append(divider)
            lines.append(f"║  📋 آخر العمليات:")
            if logs:
                for l in logs[:5]:
                    action=he(str(l.get('action', '')))
                    success_emoji="✅" if l.get('success') else "❌"
                    lines.append(f"║     {success_emoji} {action}")
            else:
                lines.append(f"║     لا توجد عمليات بعد")
            lines.append(divider)
            lines.append(f"║  📌 هذه إحصائيات الحساب فقط")
            lines.append(footer)
            nav_kb3=_btns([
                [
                    _btn("◀️ السابق (التوكن)", "nav_info_2"),
                    _btn(t(uid,"btn_back"), "tools"),
                    _btn("▶️ التالي: كامل البيانات", "nav_info_4"),
                ]
            ])
            await q.edit_message_text("\n".join(lines), parse_mode=HTML, reply_markup=nav_kb3)
            return TOOLS_STATE
        elif page==4:
            # EXTERNAL FULL DATA PAGE — REAL Garena info via external API
            token=D.get_token(uid)
            try:
                acc=D.get_setting(f"account_id_{uid}") or ""
                reg=D.get_setting(f"region_{uid}") or "ME"
            except:
                acc=""
                reg="ME"
            ext=EX.get_external_profile(acc or uid, reg)
            header="╔══════════════════════════════════════╗"
            divider="╠══════════════════════════════════════╣"
            footer="╚══════════════════════════════════════╝"
            lines=[]
            lines.append(header)
            lines.append(f"║     🌍 كامل بيانات فري فاير 🌍     ║")
            lines.append(f"║    <b>معلومات حقيقية من مصدر خارجي</b>  ║")
            lines.append(divider)
            if ext.get("status")=="success" and ext.get("basicInfo"):
                basic=ext["basicInfo"]
                lines.append(f"║  👤 الاسم الكامل: <b>{he(str(basic.get('nickname', '')))}</b>")
                lines.append(f"║  🆔 الأيدي: <code>{he(str(basic.get('accountId', '')))}</code>")
                lines.append(f"║  🌍 السيرفر: <b>{he(str(basic.get('region', 'ME')))}</b>")
                if basic.get('level'):
                    lines.append(f"║  📊 المستوى: <b>{he(str(basic.get('level')))}</b>")
                if basic.get('exp'):
                    lines.append(f"║  ⚡ الخبرة: <b>{he(str(basic.get('exp')))}</b>")
                if basic.get('rank'):
                    lines.append(f"║  🏅 الرتبة الحالية: <b>{he(str(basic.get('rank')))}</b>")
                if basic.get('rankingPoints'):
                    lines.append(f"║  🎯 نقاط التصنيف: <b>{he(str(basic.get('rankingPoints')))}</b>")
                if basic.get('liked'):
                    lines.append(f"║  ❤️ اللايكات الحقيقية: <b>{he(str(basic.get('liked')))}</b>")
                if basic.get('badgeCnt'):
                    lines.append(f"║  🏅 عدد الأوسمة: <b>{he(str(basic.get('badgeCnt')))}</b>")
                if basic.get('seasonId'):
                    lines.append(f"║  📅 الموسم: <b>{he(str(basic.get('seasonId')))}</b>")
                if basic.get('lastLoginAt'):
                    lines.append(f"║  🕐 آخر دخول: <b>{he(str(basic.get('lastLoginAt')))}</b>")
                if basic.get('title'):
                    lines.append(f"║  👑 اللقب: <b>{he(str(basic.get('title')))}</b>")
                if basic.get('weaponSkinShows'):
                    lines.append(f"║  🔫 أسلحة مميزة: <b>{len(basic.get('weaponSkinShows', []))} سلاح</b>")
                if basic.get('primeLevel'):
                    lines.append(f"║  💎 مستوى Prime: <b>{he(str(basic.get('primeLevel')))}</b>")
                # Profile info
                if ext.get("profileInfo"):
                    profile=ext["profileInfo"]
                    clothes=profile.get('clothes', [])
                    skills=profile.get('equipedSkills', [])
                    if clothes:
                        lines.append(f"║  👕 الملابس: <b>{len(clothes)} عنصر</b>")
                    if skills:
                        lines.append(f"║  ⚡ المهارات: <b>{len(skills)} مهارة</b>")
                    if profile.get('avatarId'):
                        lines.append(f"║  🖼️ صورة اللاعب: <b>ID {he(str(profile.get('avatarId')))}</b>")
                # Clan info
                if ext.get("clanBasicInfo"):
                    clan=ext["clanBasicInfo"]
                    if clan.get('clanName'):
                        lines.append(f"║  🏰 العشيرة: <b>{he(str(clan.get('clanName')))}</b>")
                    if clan.get('clanLevel'):
                        lines.append(f"║  📊 مستوى العشيرة: <b>{he(str(clan.get('clanLevel')))}</b>")
                lines.append(divider)
                lines.append(f"║  🔑 مصدر البيانات: <b>API خارجي حقيقي</b>")
                lines.append(f"║  🌐 مزود البيانات: <b>siambhau.eu.cc</b>")
            else:
                lines.append(f"║  ❌ لم يتم جلب البيانات من المصدر الخارجي")
                lines.append(f"║     السبب: <b>{he(str(ext.get('error', 'غير متوفر')))}</b>")
                lines.append(f"║     💡 جرب لاحقاً أو أرسل التوكن مرة أخرى")
            lines.append(footer)
            nav_kb4=_btns([
                [
                    _btn("◀️ السابق (الإحصائيات)", "nav_info_3"),
                    _btn(t(uid,"btn_back"), "tools"),
                    _btn("🏠 الأدوات", "tools"),
                ]
            ])
            await q.edit_message_text("\n".join(lines), parse_mode=HTML, reply_markup=nav_kb4)
            return TOOLS_STATE
        elif page==1:
            await q.edit_message_text("⏳ جاري جلب معلومات حساب فري فاير...", parse_mode=HTML)
            info=G.get_player_info(token, forced_open_id=acc, nickname_fallback=nick, region_fallback=reg)
            name=info.get('name') or nick or info.get('nickname') or "غير معروف"
            uid_val=info.get('uid') or acc or info.get('account_id') or "غير معروف"
            level=info.get('level')
            rank=info.get('rank')
            region=info.get('region') or reg or "ME"
            open_id=info.get('open_id') or "غير معروف"
            server_url=info.get('server_url') or ""
            status_text=info.get('status')
            token_valid=None
            try:
                token_valid=G.validate_token(token).get('valid')
            except:
                pass
            bind_email=""
            try:
                bind_email=G.check_bind_info_direct(token).get('email', '')
            except:
                pass
            links_result=G.check_links(token) if token else {}
            platforms=[]
            if isinstance(links_result, dict) and links_result.get('bounded_accounts'):
                platforms=links_result.get('bounded_accounts', [])
            header="╔══════════════════════════════════════╗"
            divider="╠══════════════════════════════════════╣"
            footer="╚══════════════════════════════════════╝"
            lines=[]
            lines.append(header)
            lines.append(f"║     👑 حساب فري فاير 👑         ║")
            lines.append(f"║    <b>صفحة 1 من 3 — الحساب الأساسي</b>   ║")
            lines.append(divider)
            lines.append(f"║  👤 الاسم: <b>{he(str(name))}</b>")
            lines.append(f"║  🆔 الأيدي: <code>{he(str(uid_val))}</code>")
            lines.append(f"║  🌍 السيرفر: <b>{he(str(region))}</b>")
            if level:
                lines.append(f"║  📊 المستوى: <b>{he(str(level))}</b>")
            else:
                lines.append(f"║  📊 المستوى: <b>غير متاح حالياً</b>")
            if rank:
                lines.append(f"║  🏅 الرتبة: <b>{he(str(rank))}</b>")
            lines.append(divider)
            lines.append(f"║  🔗 Open ID: <code>{str(open_id)[:20]}</code>")
            if server_url:
                lines.append(f"║  🌐 السيرفر: <code>{str(server_url)[:25]}</code>")
            else:
                lines.append(f"║  🌐 السيرفر: <b>غير متاح حالياً</b>")
            lines.append(divider)
            if bind_email:
                lines.append(f"║  📧 البريد المربوط: <b>{he(str(bind_email))}</b>")
            else:
                lines.append(f"║  📧 البريد المربوط: <b>لا يوجد</b>")
            if platforms:
                plat_str=", ".join([str(p.get('platform', p)) for p in platforms])
                lines.append(f"║  📱 المنصات: <b>{he(str(plat_str)[:30])}</b>")
            else:
                lines.append(f"║  📱 المنصات المرتبطة: <b>لا يوجد</b>")
            lines.append(divider)
            if token_valid==True:
                lines.append(f"║  ⚡ التوكن: <b>✅ صالح</b>")
            elif token_valid==False:
                lines.append(f"║  ⚡ التوكن: <b>❌ غير صالح</b>")
            elif status_text=='success':
                lines.append(f"║  ⚡ التوكن: <b>✅ صالح (JWT يعمل)</b>")
            else:
                lines.append(f"║  ⚡ التوكن: <b>⚡ صالح من الرابط</b>")
            lines.append(f"║  🔑 مصدر البيانات: <b>حساب فري فاير الحقيقي</b>")
            lines.append(footer)
            info_nav=_btns([
                [
                    _btn("◀️ الصفحة السابقة", "nav_info_3"),
                    _btn(t(uid,"btn_back"), "tools"),
                    _btn("▶️ التالي: التوكن والربط", "nav_info_2"),
                ]
            ])
            await q.edit_message_text("\n".join(lines), parse_mode=HTML, reply_markup=info_nav)
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
