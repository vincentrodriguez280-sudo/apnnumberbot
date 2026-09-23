
import os, json, asyncio, shutil, re
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, KeyboardButton, CopyTextButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from panel import create_order, get_otp, get_all_countries, get_display_name

print("[BOT] Professional - No panel name, auto buttons from GitHub ranges")

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 1853202569

for p in ["/data", "/app/data", "."]:
    try:
        os.makedirs(p, exist_ok=True)
        if os.path.exists(p):
            BASE_DIR = p
            break
    except:
        continue
else:
    BASE_DIR = "."

BAL_FILE = os.path.join(BASE_DIR, "balances.json")
TRAFFIC_FILE = os.path.join(BASE_DIR, "traffic.json")
SUCCESS_FILE = os.path.join(BASE_DIR, "success_traffic.json")
RANGES_FILE = os.path.join(BASE_DIR, "ranges.json")
MAINT_FILE = os.path.join(BASE_DIR, "maintenance.json")
ACTIVE_FILE = os.path.join(BASE_DIR, "active_numbers.json")
CONFIG_FILE = os.path.join(BASE_DIR, "bot_config.json")

if not os.path.exists(RANGES_FILE) and os.path.exists("ranges.json"):
    try:
        shutil.copy("ranges.json", RANGES_FILE)
    except: pass

DEFAULT_CONFIG = {
    "must_join": ["@APNOfficial", "@APNOTP", "@Proxystore999"],
    "otp_group": "https://t.me/APNOTP",
    "otp_group_id": "@APNOTP",
    "support_id": "https://t.me/PolasChandra",
    "services": ["FACEBOOK", "WHATSAPP", "TIKTOK"],
    "community_url": "https://t.me/APNOfficial",
    "number_bot_url": "https://t.me/APNNUMBERBOT",
    "flags": {
        "NEPAL": "🇳🇵", "NEPAL_FB": "🇳🇵", "USA": "🇺🇸", "BD": "🇧🇩", "UK": "🇬🇧", "GB": "🇬🇧",
        "MOZAMBIQUE": "🇲🇿", "MYANMAR": "🇲🇲", "CAMEROON": "🇨🇲", "CAMBODIA": "🇰🇭",
        "MADAGASCAR": "🇲🇬", "MADAGASCARNEWACCOUNT": "🇲🇬", "MADAGASCAR_NEW_ACCOUNT": "🇲🇬",
        "MOROCCO": "🇲🇦", "NIGERIA": "🇳🇬", "GUINEA": "🇬🇳", "MONTENEGRO": "🇲🇪"
    },
    "prices": {
        "NEPAL": "0.005$", "NEPAL_FB": "0.005$", "USA": "0.003$", "BD": "0.005$",
        "MADAGASCARNEWACCOUNT": "0.005$", "MADAGASCAR_NEW_ACCOUNT": "0.005$", "MADAGASCAR": "0.005$",
        "DEFAULT": "0.003$"
    },
    "buttons": {
        "get_number": "📱 Get Number",
        "balance": "💰 Balance",
        "refer": "👥 Refer",
        "help": "❓ Help",
        "back": "⬅️ Back",
        "change": "🔄 Change",
        "view_otp": "📥 View OTP",
        "number_btn": "🔢 Number",
        "channel_btn": "📢 Channel",
        "services_facebook": "📘 Facebook",
        "services_whatsapp": "💬 WhatsApp",
        "admin_panel": "⚙️ Admin Panel"
    },
    "texts": {
        "start": "Welcome to APN Number Bot! 🎉\n\nGet fresh numbers for verification!",
        "select_service": "💳 Select Platform:",
        "select_country": "💳 {platform} - Select country:",
        "fetching": "⏳ Getting number for {country}...",
        "no_stock_user": "❌ Out of Stock! {country}\n\nPlease try again later or contact support.",
        "no_stock_admin": "❌ Out of Stock! {country}\n\nRid not set or empty. Use /add {service} {country} <rid>\nCheck /list",
        "number_header": "────────── ⋆⋅☆⋅⋆ ──────────\n{flag} {country} Fresh Number 💸\n📱 {platform}\n────────── ⋆⋅☆⋅⋆ ──────────\n\n💫 Wait 10s for OTP 🖤",
        "join_required": "⚠️ You must join our channels first!",
        "balance_text": "💰 Balance: ${balance:.4f}"
    }
}

def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                cfg = json.load(f)
                for k, v in DEFAULT_CONFIG.items():
                    if k not in cfg:
                        cfg[k] = v
                    elif isinstance(v, dict):
                        for kk, vv in v.items():
                            if kk not in cfg[k]:
                                cfg[k][kk] = vv
                return cfg
    except:
        pass
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(cfg, f, indent=2)
        with open("./bot_config.json", 'w') as f:
            json.dump(cfg, f, indent=2)
    except: pass

def load_json(f, default):
    for path in [f, os.path.join(".", os.path.basename(f))]:
        if os.path.exists(path):
            try:
                with open(path,'r') as fp: 
                    return json.load(fp)
            except: continue
    return default

def save_json(f, data):
    for path in [f, os.path.join(".", os.path.basename(f))]:
        try:
            os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
            with open(path,'w') as fp: json.dump(data, fp, indent=2)
        except: pass

def is_maintenance():
    return load_json(MAINT_FILE, {"enabled": False}).get("enabled", False)

def get_user(uid):
    db = load_json(BAL_FILE, {})
    uid=str(uid)
    if uid not in db:
        db[uid]={"balance":0.0,"requests":[],"total":0,"referrals":0,"referred_by":None}
        save_json(BAL_FILE, db)
    return db[uid]

def save_user(uid, data):
    db = load_json(BAL_FILE, {})
    db[str(uid)]=data
    save_json(BAL_FILE, db)

def add_request(uid, country):
    user = get_user(uid)
    user["requests"].append(datetime.now().isoformat())
    user["total"]+=1
    save_user(uid, user)

def add_success(country):
    tr = load_json(SUCCESS_FILE, {})
    tr[country] = tr.get(country,0)+1
    save_json(SUCCESS_FILE, tr)

def save_active_number(uid, number, country, service):
    db = load_json(ACTIVE_FILE, {})
    uid=str(uid)
    if uid not in db: db[uid]=[]
    db[uid].append({"number": number, "country": country, "service": service, "time": datetime.now().isoformat()})
    db[uid]=db[uid][-20:]
    save_json(ACTIVE_FILE, db)

def get_active_numbers(uid):
    db = load_json(ACTIVE_FILE, {})
    return db.get(str(uid), [])

def mask_number(num):
    n = num.replace(" ", "").replace("+", "").strip()
    if len(n) <= 6: return "+" + n
    return f"+{n[:4]}XXXXXX{n[-3:]}"

def format_for_inbox(country_code, full_number, service, otp_code):
    cfg = load_config()
    flags = cfg["flags"]
    clean = country_code.upper()
    flag = flags.get(clean, flags.get(clean.split("_")[0], "🌍"))
    otp_digits = ''.join(filter(str.isdigit, str(otp_code)))
    # Display name clean
    display = get_display_name(country_code)
    service_display = "Facebook" if "FACEBOOK" in service.upper() else service.title()
    earn = cfg["prices"].get(clean, cfg["prices"].get("DEFAULT", "0.003$"))
    text = f"{flag} {display}\n📞 `{full_number}`\n💼 {service_display} | {earn}"
    try:
        kb = [[InlineKeyboardButton(f"🔑 {otp_digits}", copy_text=CopyTextButton(otp_digits))]]
    except:
        kb = [[InlineKeyboardButton(f"📋 {otp_digits}", callback_data=f"copy_{otp_digits}")]]
    return text, InlineKeyboardMarkup(kb)

def format_for_group(country_code, full_number, service, otp_code):
    cfg = load_config()
    flags = cfg["flags"]
    clean = country_code.upper()
    masked = mask_number(full_number)
    otp_digits = ''.join(filter(str.isdigit, str(otp_code)))
    display = get_display_name(country_code)
    service_display = "Facebook" if "FACEBOOK" in service.upper() else service.title()
    text = f"APN NUMBER BOT\n💳 #{clean} 📱 {service_display}\n\n╭─────────────────╮\n  {masked}\n╰─────────────────╯\n🗣 {display}"
    try:
        otp_btn = InlineKeyboardButton(f"🔓 {otp_digits}", copy_text=CopyTextButton(otp_digits))
    except:
        otp_btn = InlineKeyboardButton(f"🔓 {otp_digits}", callback_data=f"copy_{otp_digits}")
    kb = [[otp_btn], [InlineKeyboardButton(cfg["buttons"].get("number_btn","🔢 Number"), url=cfg["number_bot_url"]), InlineKeyboardButton(cfg["buttons"].get("channel_btn","📢 Channel"), url=cfg["community_url"])]]
    return text, InlineKeyboardMarkup(kb)

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
    print(f"[WATCHER] {number} {order_id} {country_code}")
    interval = 10
    max_checks = 18  # 3 min
    for i in range(max_checks):
        await asyncio.sleep(interval)
        try:
            otp = await asyncio.to_thread(get_otp, order_id)
            if otp:
                print(f"[OTP FOUND] {number} -> {otp}")
                text_inbox, markup_inbox = format_for_inbox(country_code, number, service, otp)
                text_group, markup_group = format_for_group(country_code, number, service, otp)
                # Send to user inbox
                try:
                    await bot.send_message(chat_id=user_id, text=text_inbox, reply_markup=markup_inbox, parse_mode="Markdown")
                except:
                    await bot.send_message(chat_id=user_id, text=text_inbox, reply_markup=markup_inbox)
                # Send to OTP group
                try:
                    cfg = load_config()
                    await bot.send_message(chat_id=cfg["otp_group_id"], text=text_group, reply_markup=markup_group, parse_mode="Markdown")
                except Exception as e:
                    print(f"[GROUP FAIL] {e}")
                # Balance
                user = get_user(user_id)
                cfg = load_config()
                price_str = cfg["prices"].get(country_code.upper(), cfg["prices"].get("DEFAULT", "0.003$"))
                try:
                    earn = float(price_str.replace("$","").replace("+",""))
                except:
                    earn = 0.003
                user["balance"]+=earn
                save_user(user_id, user)
                add_success(country_code)
                return
        except Exception as e:
            print(f"[WATCHER ERR] {e}")
    print(f"[TIMEOUT] {number}")

# ADMIN
async def bot_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    save_json(MAINT_FILE, {"enabled": True})
    await update.message.reply_text("🔴 Bot OFF")

async def bot_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    save_json(MAINT_FILE, {"enabled": False})
    await update.message.reply_text("🟢 Bot ON")

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    cfg = load_config()
    txt = "⚙️ **ADMIN PANEL**\n\n"
    txt += "Button name change from bot:\n"
    txt += "/set_button <key> <name>\n"
    txt += "/list_buttons\n\n"
    txt += "Ranges (GitHub auto):\n"
    txt += "/add FB MADAGASCAR_NEW_ACCOUNT 12345\n"
    txt += "/add FB NEPAL 26134\n"
    txt += "/list\n/del FB NEPAL\n\n"
    txt += "Numbers come from panel via rid"
    kb = [[InlineKeyboardButton("📱 Buttons", callback_data="admin_buttons"), InlineKeyboardButton("📋 Ranges", callback_data="admin_ranges")]]
    await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def list_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    cfg = load_config()
    txt = "📱 **BUTTONS** - Change with /set_button:\n\n"
    for k,v in cfg["buttons"].items():
        txt += f"`{k}` = {v}\n"
    txt += "\nEx: /set_button get_number 🔥 Get OTP"
    await update.message.reply_text(txt, parse_mode="Markdown")

async def set_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if len(context.args) < 2:
        await update.message.reply_text("❌ /set_button <key> <new_name>\nEx: /set_button get_number 🔥 Get OTP")
        return
    key = context.args[0].lower()
    new_name = " ".join(context.args[1:])
    cfg = load_config()
    if key not in cfg["buttons"]:
        await update.message.reply_text(f"❌ Key not found! Available: {', '.join(cfg['buttons'].keys())}")
        return
    old = cfg["buttons"][key]
    cfg["buttons"][key] = new_name
    save_config(cfg)
    await update.message.reply_text(f"✅ {key}: {old} → {new_name}", parse_mode="Markdown")

async def add_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    try:
        service = context.args[0].upper()
        name = context.args[1].upper()
        rid = context.args[2]
        if service == "FB": service = "FACEBOOK"
        if service == "WS": service = "WHATSAPP"
        data = load_json(RANGES_FILE, {"FACEBOOK":{}, "WHATSAPP":{}})
        if service not in data: data[service] = {}
        data[service][name] = rid
        save_json(RANGES_FILE, data)
        await update.message.reply_text(f"✅ Added {service} - {name} = {rid}\nButton auto created: {get_display_name(name)}")
    except:
        await update.message.reply_text("❌ Use: /add FB NEPAL 26134\n/add FB MADAGASCAR_NEW_ACCOUNT 12345")

async def del_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    try:
        service = context.args[0].upper()
        name = context.args[1].upper()
        if service == "FB": service = "FACEBOOK"
        data = load_json(RANGES_FILE, {})
        if name in data.get(service, {}):
            del data[service][name]
            save_json(RANGES_FILE, data)
            await update.message.reply_text(f"🗑 Deleted {name} from {service}")
        else:
            await update.message.reply_text("❌ Not found - check /list")
    except:
        await update.message.reply_text("❌ /del FB NEPAL")

async def list_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    data = load_json(RANGES_FILE, {})
    txt = "📋 **Ranges - GitHub auto buttons**\n\n"
    for srv, ranges in data.items():
        txt += f"{srv}:\n"
        for n, r in ranges.items():
            txt += f"  {n} = {r} → {get_display_name(n)}\n"
        txt += "\n"
    txt += "Button auto creates from this list"
    await update.message.reply_text(txt, parse_mode="Markdown")

async def debug_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    data = load_json(RANGES_FILE, {})
    txt = "📊 **Ranges**\n\n"
    for srv, ranges in data.items():
        txt += f"{srv}: {len(ranges)} countries\n"
    await update.message.reply_text(txt)

async def get_my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"ID: {update.effective_user.id}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    cfg = load_config()
    if is_maintenance() and uid != ADMIN_ID:
        await update.message.reply_text("🔧 Maintenance")
        return
    if not await is_joined(uid, context):
        txt = cfg["texts"]["join_required"] + "\n\n"
        kb = []
        for ch in cfg["must_join"]:
            ch_name = ch.replace("@","")
            kb.append([InlineKeyboardButton(f"📢 Join {ch_name}", url=f"https://t.me/{ch_name}")])
        kb.append([InlineKeyboardButton("✅ Joined", callback_data="check_join")])
        await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return
    # Professional welcome - NO panel name
    txt = cfg["texts"]["start"]
    buttons = cfg["buttons"]
    kb = [
        [KeyboardButton(buttons.get("get_number","📱 Get Number"))],
        [KeyboardButton(buttons.get("my_numbers","📋 My Numbers")), KeyboardButton(buttons.get("balance","💰 Balance"))],
        [KeyboardButton(buttons.get("refer","👥 Refer")), KeyboardButton(buttons.get("help","❓ Help"))],
    ]
    if uid == ADMIN_ID:
        kb.append([KeyboardButton(buttons.get("admin_panel","⚙️ Admin Panel"))])
    await update.message.reply_text(txt, reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text
    cfg = load_config()
    buttons = cfg["buttons"]
    if text == buttons.get("get_number","📱 Get Number"):
        await show_services(update, context)
    elif text == buttons.get("my_numbers","📋 My Numbers"):
        nums = get_active_numbers(uid)
        if not nums:
            await update.message.reply_text("📋 No numbers yet")
        else:
            txt = "📋 Your Numbers:\n"
            for n in nums[-10:]:
                txt += f"{n['number']} - {get_display_name(n['country'])}\n"
            await update.message.reply_text(txt)
    elif text == buttons.get("balance","💰 Balance"):
        user = get_user(uid)
        await update.message.reply_text(f"💰 Balance: ${user.get('balance',0):.4f}")
    elif text == buttons.get("admin_panel","⚙️ Admin Panel") and uid == ADMIN_ID:
        await admin_panel(update, context)
    elif text == buttons.get("refer","👥 Refer"):
        bot_username = (await context.bot.get_me()).username
        await update.message.reply_text(f"👥 Refer: https://t.me/{bot_username}?start={uid}")
    elif text == buttons.get("help","❓ Help"):
        await update.message.reply_text("Contact support")

async def show_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = load_config()
    buttons = cfg["buttons"]
    txt = cfg["texts"]["select_service"]
    kb = []
    for srv in cfg["services"]:
        key = f"services_{srv.lower()}"
        btn_text = buttons.get(key, srv)
        kb.append([InlineKeyboardButton(btn_text, callback_data=f"s_{srv}")])
    kb.append([InlineKeyboardButton(buttons.get("back","⬅️ Back"), callback_data="main_menu")])
    if isinstance(update, Update) and update.message:
        await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    uid = q.from_user.id
    cfg = load_config()
    buttons = cfg["buttons"]
    
    if data == "check_join":
        if await is_joined(uid, context):
            await start(update, context)
        else:
            await q.edit_message_text("❌ Join all channels first!")
        return
    
    if data in ["main_menu", "services"]:
        await show_services(q, context)
        return
    
    if data.startswith("admin_") and uid == ADMIN_ID:
        if data == "admin_buttons":
            txt = "📱 **BUTTONS**\n"
            for k,v in cfg["buttons"].items():
                txt += f"{k} = {v}\n"
            txt += "\n/set_button get_number New Name"
            await q.edit_message_text(txt, parse_mode="Markdown")
            return
        elif data == "admin_ranges":
            data_r = load_json(RANGES_FILE, {})
            txt = "📋 **Ranges**\n"
            for srv, ranges in data_r.items():
                txt += f"{srv}: {len(ranges)}\n"
            await q.edit_message_text(txt)
            return
    
    if data.startswith("s_"):
        service = data[2:]
        context.user_data['service'] = service
        countries = get_all_countries(service)
        if not countries:
            # Show message for user vs admin
            if uid == ADMIN_ID:
                await q.edit_message_text(f"❌ No ranges for {service}!\n\nUse /add {service} COUNTRY <rid>\nEx: /add {service} NEPAL 26134\n\nThen button auto creates", parse_mode="Markdown")
            else:
                await q.edit_message_text(f"❌ No numbers for {service} yet! Try later.")
            return
        txt = cfg["texts"]["select_country"].format(platform=service.title())
        kb = []
        for code in countries:
            display = get_display_name(code)
            flag = cfg["flags"].get(code.upper(), "🌍")
            price = cfg["prices"].get(code.upper(), cfg["prices"].get("DEFAULT", "0.003$"))
            kb.append([InlineKeyboardButton(f"{flag} {display} {price}", callback_data=f"c_{code}")])
        kb.append([InlineKeyboardButton(buttons.get("back","⬅️ Back"), callback_data="services")])
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data.startswith("c_"):
        country_code = data[2:]
        service = context.user_data.get('service', 'FACEBOOK')
        display = get_display_name(country_code)
        flag = cfg["flags"].get(country_code.upper(), "🌍")
        await q.edit_message_text(cfg["texts"]["fetching"].format(country=display))
        
        try:
            order = await asyncio.to_thread(create_order, service, country_code)
            if not order:
                # Different message for user vs admin
                if uid == ADMIN_ID:
                    await q.edit_message_text(cfg["texts"]["no_stock_admin"].format(country=display, service=service, country_code=country_code), parse_mode="Markdown")
                else:
                    await q.edit_message_text(cfg["texts"]["no_stock_user"].format(country=display), parse_mode="Markdown")
                return
            
            add_request(uid, display)
            save_active_number(uid, order['number'], country_code, service)
            context.application.create_task(otp_watcher(context.bot, order['id'], uid, order['number'], service, country_code))
            
            header = cfg["texts"]["number_header"].format(flag=flag, country=display, platform=service.title())
            txt = header
            kb = []
            try:
                kb.append([InlineKeyboardButton(f"{order['number']}", copy_text=CopyTextButton(order['number']))])
            except:
                kb.append([InlineKeyboardButton(f"{order['number']}", callback_data=f"copy_{order['number']}")])
            kb.append([InlineKeyboardButton(buttons.get("view_otp","📥 View OTP"), url=cfg["otp_group"])])
            kb.append([InlineKeyboardButton(buttons.get("change","🔄 Change"), callback_data=f"c_{country_code}"), InlineKeyboardButton(buttons.get("back","🔙 Back"), callback_data=f"s_{service}")])
            await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
            
        except Exception as e:
            print(f"[C ERR] {e}")
            await q.edit_message_text(f"❌ Error for {display}. Try later.")

from telegram.request import HTTPXRequest
request = HTTPXRequest(connection_pool_size=20, connect_timeout=30, read_timeout=30, write_timeout=30, pool_timeout=30)
app = ApplicationBuilder().token(TOKEN).request(request).build()

async def error_handler(update, context):
    print(f"[BOT ERROR] {context.error}")

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
