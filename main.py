
import os, json, asyncio, re
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, KeyboardButton, CopyTextButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from panel import create_order, get_otp, get_all_countries, get_display_name

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 1853202569
BASE_DIR = "/data" if os.path.exists("/data") else "."

BAL_FILE = os.path.join(BASE_DIR, "balances.json")
RANGES_FILE = os.path.join(BASE_DIR, "ranges.json")
MAINT_FILE = os.path.join(BASE_DIR, "maintenance.json")
ACTIVE_FILE = os.path.join(BASE_DIR, "active_numbers.json")
CONFIG_FILE = os.path.join(BASE_DIR, "bot_config.json")

DEFAULT_CONFIG = {
    "must_join": ["@APNOfficial", "@APNOTP", "@Proxystore999"],
    "otp_group": "https://t.me/APNOTP",
    "otp_group_id": "@APNOTP",
    "services": ["FACEBOOK"],
    "community_url": "https://t.me/APNOfficial",
    "number_bot_url": "https://t.me/APNNUMBERBOT",
    "flags": {"NEPAL": "🇳🇵", "USA": "🇺🇸", "BD": "🇧🇩", "MADAGASCAR": "🇲🇬", "MADAGASCAR_NEW_ACCOUNT": "🇲🇬"},
    "prices": {"DEFAULT": "0.003$"},
    "buttons": {"get_number": "📱 Get Number", "withdraw": "💸 Withdraw", "balance": "💰 Balance", "refer": "👥 Refer", "help": "❓ Help", "back": "⬅️ Back", "change": "🔄 Change", "view_otp": "📥 View OTP", "number_btn": "🔢 Number", "channel_btn": "📢 Channel", "services_facebook": "📘 Facebook", "services_whatsapp": "💬 WhatsApp", "services_tiktok": "🎵 TikTok", "admin_panel": "⚙️ Admin Panel"},
    "texts": {"start": "Welcome to APN Number Bot! 🎉\n\nGet fresh numbers for verification!", "select_service": "💳 Select Platform:", "select_country": "💳 {platform} - Select country:", "fetching": "⏳ Getting number for {country}...", "no_stock_user": "❌ Out of Stock! {country}\nPlease try later.", "no_stock_admin": "❌ Out of Stock! {country}\nRid: {rid}\n/add {service} COUNTRY <rid>\nCheck /list + VOLTX_API_KEY", "number_header": "{flag} {country} Fresh Number 💸\n📱 {platform}\n💫 Wait 10s for OTP"}
}

def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                cfg = json.load(f)
                return cfg
    except: pass
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    try:
        with open(CONFIG_FILE, 'w') as f: json.dump(cfg, f, indent=2)
    except: pass

def load_json(f, default):
    for p in [f, os.path.join(".", os.path.basename(f))]:
        if os.path.exists(p):
            try:
                with open(p,'r') as fp: return json.load(fp)
            except: continue
    return default

def save_json(f, data):
    for p in [f, os.path.join(".", os.path.basename(f))]:
        try:
            os.makedirs(os.path.dirname(p) if os.path.dirname(p) else ".", exist_ok=True)
            with open(p,'w') as fp: json.dump(data, fp, indent=2)
        except: pass

def is_maintenance(): return load_json(MAINT_FILE, {"enabled": False}).get("enabled", False)
def get_user(uid):
    db = load_json(os.path.join(BASE_DIR, "balances.json"), {})
    uid=str(uid)
    if uid not in db:
        db[uid]={"balance":0.0,"requests":[],"total":0}
        save_json(os.path.join(BASE_DIR, "balances.json"), db)
    return db[uid]
def save_user(uid, data):
    db = load_json(os.path.join(BASE_DIR, "balances.json"), {})
    db[str(uid)]=data
    save_json(os.path.join(BASE_DIR, "balances.json"), db)
def save_active_number(uid, number, country, service):
    db = load_json(ACTIVE_FILE, {})
    uid=str(uid)
    if uid not in db: db[uid]=[]
    db[uid].append({"number": number, "country": country, "service": service, "time": datetime.now().isoformat()})
    db[uid]=db[uid][-20:]
    save_json(ACTIVE_FILE, db)

async def is_joined(user_id, context):
    if user_id == ADMIN_ID: return True
    cfg = load_config()
    for ch in cfg["must_join"]:
        try:
            m = await context.bot.get_chat_member(chat_id=ch, user_id=user_id)
            if m.status in ['left','kicked']: return False
        except: continue
    return True

async def otp_watcher(bot, order_id, user_id, number, service, country_code):
    for i in range(18):
        await asyncio.sleep(10)
        try:
            otp = await asyncio.to_thread(get_otp, order_id)
            if otp:
                cfg = load_config()
                flag = cfg["flags"].get(country_code.upper(), "🌍")
                display = get_display_name(country_code)
                text = f"{flag} {display}\n📞 `{number}`\n🔑 OTP: {otp}"
                try: kb = [[InlineKeyboardButton(f"🔑 {otp}", copy_text=CopyTextButton(otp))]]
                except: kb = [[InlineKeyboardButton(f"📋 {otp}", callback_data=f"copy_{otp}")]]
                try: await bot.send_message(chat_id=user_id, text=text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
                except: await bot.send_message(chat_id=user_id, text=text, reply_markup=InlineKeyboardMarkup(kb))
                try:
                    masked = f"+{number[:4]}XXXXXX{number[-3:]}"
                    t2 = f"#{country_code} {masked} -> {otp}"
                    await bot.send_message(chat_id=cfg["otp_group_id"], text=t2)
                except: pass
                return
        except Exception as e: print(f"[WATCHER ERR] {e}")

async def bot_off(update, context):
    if update.effective_user.id!= ADMIN_ID: return
    save_json(MAINT_FILE, {"enabled": True})
    await update.message.reply_text("🔴 OFF")
async def bot_on(update, context):
    if update.effective_user.id!= ADMIN_ID: return
    save_json(MAINT_FILE, {"enabled": False})
    await update.message.reply_text("🟢 ON")
async def admin_panel(update, context):
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text("⚙️ ADMIN\n/add FB MADAGASCAR_NEW_ACCOUNT 12345\n/list\n/debug\n/set_button get_number NewName\n/list_buttons")
async def list_buttons(update, context):
    if update.effective_user.id != ADMIN_ID: return
    cfg = load_config()
    txt = "Buttons:\n"
    for k,v in cfg["buttons"].items(): txt+=f"{k}={v}\n"
    await update.message.reply_text(txt, parse_mode="Markdown")
async def set_button(update, context):
    if update.effective_user.id != ADMIN_ID: return
    if len(context.args)<2: await update.message.reply_text("❌ /set_button <key> <name>"); return
    key = context.args[0].lower()
    new_name = " ".join(context.args[1:])
    cfg = load_config()
    if key not in cfg["buttons"]: await update.message.reply_text(f"❌ Not found {key}"); return
    cfg["buttons"][key]=new_name
    save_config(cfg)
    await update.message.reply_text(f"✅ {key} -> {new_name}")
async def add_range(update, context):
    if update.effective_user.id!= ADMIN_ID: return
    try:
        service = context.args[0].upper()
        name = context.args[1].upper()
        rid = context.args[2]
        if service=="FB": service="FACEBOOK"
        data = load_json(RANGES_FILE, {"FACEBOOK":{}})
        if service not in data: data[service]={}
        data[service][name]=rid
        save_json(RANGES_FILE, data)
        await update.message.reply_text(f"✅ Added {service}/{name}={rid}")
    except: await update.message.reply_text("❌ /add FB NEPAL 26134")
async def del_range(update, context):
    if update.effective_user.id!= ADMIN_ID: return
    try:
        service = context.args[0].upper()
        name = context.args[1].upper()
        if service=="FB": service="FACEBOOK"
        data = load_json(RANGES_FILE, {})
        if name in data.get(service, {}):
            del data[service][name]
            save_json(RANGES_FILE, data)
            await update.message.reply_text(f"🗑 {name}")
        else: await update.message.reply_text("❌ Not found")
    except: await update.message.reply_text("❌ /del FB NEPAL")
async def list_range(update, context):
    if update.effective_user.id!= ADMIN_ID: return
    data = load_json(RANGES_FILE, {})
    if not data: await update.message.reply_text("❌ No ranges! /add FB NEPAL 26134"); return
    txt="📋 Ranges:\n"
    for srv, rng in data.items():
        txt+=f"{srv}:\n"
        for n,r in rng.items(): txt+=f"  {n}={r} -> {get_display_name(n)}\n"
    await update.message.reply_text(txt, parse_mode="Markdown")
async def debug_numbers(update, context):
    if update.effective_user.id!= ADMIN_ID: return
    import os
    api_key = os.getenv("VOLTX_API_KEY","") or os.getenv("MAUTHAPI_KEY","")
    data = load_json(RANGES_FILE, {})
    txt=f"API Key: {'SET' if api_key else 'NOT SET!'}\nRanges: {data}\n"
    await update.message.reply_text(txt, parse_mode="Markdown")
async def get_my_id(update, context): await update.message.reply_text(f"ID: {update.effective_user.id}")
async def start(update, context):
    uid = update.effective_user.id
    cfg = load_config()
    if is_maintenance() and uid!=ADMIN_ID: await update.message.reply_text("🔧 Maintenance"); return
    if not await is_joined(uid, context):
        txt="⚠️ Join channels first!\n"
        kb=[]
        for ch in cfg["must_join"]:
            ch_name=ch.replace("@","")
            kb.append([InlineKeyboardButton(f"📢 Join {ch_name}", url=f"https://t.me/{ch_name}")])
        kb.append([InlineKeyboardButton("✅ Joined", callback_data="check_join")])
        await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return
    txt=cfg["texts"]["start"]
    buttons=cfg["buttons"]
    kb=[[KeyboardButton(buttons.get("get_number","📱 Get Number"))], [KeyboardButton(buttons.get("withdraw","💸 Withdraw")), KeyboardButton(buttons.get("balance","💰 Balance"))], [KeyboardButton(buttons.get("refer","👥 Refer")), KeyboardButton(buttons.get("help","❓ Help"))]]
    if uid==ADMIN_ID: kb.append([KeyboardButton(buttons.get("admin_panel","⚙️ Admin Panel"))])
    await update.message.reply_text(txt, reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def handle_text_messages(update, context):
    uid=update.effective_user.id
    text=update.message.text
    cfg=load_config()
    buttons=cfg["buttons"]
    if text==buttons.get("get_number","📱 Get Number"): await show_services(update, context)
    elif text==buttons.get("withdraw","💸 Withdraw"):
        await update.message.reply_text("💸 **Withdraw**\n\nMinimum $5\nContact @PolasChandra for withdraw\n\nYour Balance: ${:.4f}".format(get_user(uid).get('balance',0.0)), parse_mode="Markdown")
    elif text==buttons.get("balance","💰 Balance"):
        user=get_user(uid)
        await update.message.reply_text(f"💰 Balance: ${user.get('balance',0):.4f}")
    elif text==buttons.get("help","❓ Help"):
        await update.message.reply_text("❓ **Help & Support**\n\nContact: @PolasChandra\n\nFor any issue, message @PolasChandra", parse_mode="Markdown")
    elif text==buttons.get("refer","👥 Refer"):
        bot_username = (await context.bot.get_me()).username
        await update.message.reply_text(f"👥 Refer: https://t.me/{bot_username}?start={uid}")
    elif text==buttons.get("admin_panel","⚙️ Admin Panel") and uid==ADMIN_ID: await admin_panel(update, context)

async def show_services(update, context):
    cfg=load_config()
    buttons=cfg["buttons"]
    txt=cfg["texts"]["select_service"]
    kb=[]
    for srv in cfg["services"]:
        key=f"services_{srv.lower()}"
        btn_text=buttons.get(key, srv)
        kb.append([InlineKeyboardButton(btn_text, callback_data=f"s_{srv}")])
    kb.append([InlineKeyboardButton(buttons.get("back","⬅️ Back"), callback_data="main_menu")])
    if isinstance(update, Update) and update.message:
        await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
    else:
        try:
            await update.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        except:
            # For callback query case
            await update.callback_query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))

async def handle(update, context):
    q=update.callback_query
    await q.answer()
    data=q.data
    uid=q.from_user.id
    cfg=load_config()
    buttons=cfg["buttons"]
    if data=="check_join":
        if await is_joined(uid, context): await start(update, context)
        else: await q.edit_message_text("❌ Join first!")
        return
    if data in ["main_menu", "services"]: await show_services(q, context); return
    if data.startswith("s_"):
        service=data[2:]
        context.user_data['service']=service
        countries=get_all_countries(service)
        if not countries:
            if uid==ADMIN_ID: await q.edit_message_text(f"❌ No ranges for {service}!\n/add {service} NEPAL 26134")
            else: await q.edit_message_text(f"❌ No numbers for {service} yet!")
            return
        txt=cfg["texts"]["select_country"].format(platform=service.title())
        kb=[]
        for code in countries:
            display=get_display_name(code)
            flag=cfg["flags"].get(code.upper(), "🌍")
            kb.append([InlineKeyboardButton(f"{flag} {display}", callback_data=f"c_{code}")])
        kb.append([InlineKeyboardButton(buttons.get("back","⬅️ Back"), callback_data="services")])
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return
    if data.startswith("c_"):
        country_code=data[2:]
        service=context.user_data.get('service','FACEBOOK')
        display=get_display_name(country_code)
        flag=cfg["flags"].get(country_code.upper(), "🌍")
        await q.edit_message_text(f"⏳ Getting 8 numbers for {display}...")
        try:
            from panel import get_rid_for_country
            rid=get_rid_for_country(country_code, service)
            nums = []
            # Get 8 numbers
            for i in range(8):
                try:
                    order = await asyncio.to_thread(create_order, service, country_code)
                    if order:
                        # Avoid duplicate
                        if not any(o['number'] == order['number'] for o in nums):
                            nums.append(order)
                            save_active_number(uid, order['number'], country_code, service)
                            context.application.create_task(otp_watcher(context.bot, order['id'], uid, order['number'], service, country_code))
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"[GETNUM {i} ERR] {e}")
            
            if not nums:
                if uid==ADMIN_ID: await q.edit_message_text(cfg["texts"]["no_stock_admin"].format(country=display, service=service, rid=rid or "NOT SET"), parse_mode="Markdown")
                else: await q.edit_message_text(cfg["texts"]["no_stock_user"].format(country=display), parse_mode="Markdown")
                return
            
            header=cfg["texts"]["number_header"].format(flag=flag, country=display, platform=service.title())
            txt = header + f"\n\nGot {len(nums)} numbers:"
            kb=[]
            for o in nums:
                try: kb.append([InlineKeyboardButton(f"{o['number']}", copy_text=CopyTextButton(o['number']))])
                except: kb.append([InlineKeyboardButton(f"{o['number']}", callback_data=f"copy_{o['number']}")])
            kb.append([InlineKeyboardButton(buttons.get("view_otp","📥 View OTP"), url=cfg["otp_group"])])
            kb.append([InlineKeyboardButton(buttons.get("change","🔄 Change"), callback_data=f"c_{country_code}"), InlineKeyboardButton(buttons.get("back","🔙 Back"), callback_data=f"s_{service}")])
            await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        except Exception as e:
            print(f"[C ERR] {e}")
            import traceback
            traceback.print_exc()
            await q.edit_message_text(f"❌ Error for {display}")

from telegram.request import HTTPXRequest
request=HTTPXRequest(connection_pool_size=20, connect_timeout=30, read_timeout=30, write_timeout=30, pool_timeout=30)
app=ApplicationBuilder().token(TOKEN).request(request).build()
async def error_handler(update, context): print(f"[BOT ERROR] {context.error}")
app.add_error_handler(error_handler)
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin_panel))
app.add_handler(CommandHandler("debug", debug_numbers))
app.add_handler(CommandHandler("id", get_my_id))
app.add_handler(CommandHandler("add", add_range))
app.add_handler(CommandHandler("del", del_range))
app.add_handler(CommandHandler("list", list_range))
app.add_handler(CommandHandler("off", bot_off))
app.add_handler(CommandHandler("on", bot_on))
app.add_handler(CommandHandler("set_button", set_button))
app.add_handler(CommandHandler("list_buttons", list_buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
app.add_handler(CallbackQueryHandler(handle))
app.run_polling(drop_pending_updates=True)
