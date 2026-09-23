
import os, json, asyncio, shutil, re
from datetime import datetime, date
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, KeyboardButton, CopyTextButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from panel import create_order, get_otp, get_all_countries, get_display_name

print("[BOT] ADMIN PANEL + 2oo9.cloud Voltx Panel ONLY!")

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 1853202569

for p in ["/data", "/app/data", "."]:
    try:
        if os.path.exists(p) or p in ["/data", "/app/data"]:
            os.makedirs(p, exist_ok=True)
            if os.path.exists(p):
                BASE_DIR = p
                break
    except:
        continue
else:
    BASE_DIR = "."
    os.makedirs(BASE_DIR, exist_ok=True)

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
        "MOROCCO": "🇲🇦", "NIGERIA": "🇳🇬", "GUINEA": "🇬🇳", "MADAGASCAR": "🇲🇬"
    },
    "prices": {
        "NEPAL": "0.005$", "NEPAL_FB": "0.005$", "USA": "0.003$", "BD": "0.005$",
        "UK": "0.005$", "GB": "0.005$", "DEFAULT": "0.003$"
    },
    "buttons": {
        "get_number": "📱 Get Number",
        "my_numbers": "📋 My Numbers",
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
        "services_tiktok": "🎵 TikTok",
        "admin_panel": "⚙️ Admin Panel"
    },
    "texts": {
        "start": "Welcome to APN Number Bot! 🎉\n\nGet fresh numbers for Facebook, WhatsApp, TikTok verification!\n\nPowered by Voltx API",
        "select_service": "💳 Select Platform:",
        "select_country": "💳 {platform} - দেশ সিলেক্ট করুন:",
        "fetching": "⏳ Fetching {count} numbers for {country}...",
        "no_stock": "❌ Out of Stock! {country}",
        "number_header": "────────── ⋆⋅☆⋅⋆ ──────────\n{flag} {country} Fresh Number 💸\n📱 {platform}\n────────── ⋆⋅☆⋅⋆ ──────────\n\n💫 Wait 10s for OTP 🖤",
        "join_required": "⚠️ You must join our channels first!",
        "balance_text": "💰 Your Balance: ${balance:.4f}"
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
    except Exception as e:
        print(f"[CONFIG SAVE ERR] {e}")

def load_json(f, default):
    for path in [f, os.path.join(".", os.path.basename(f))]:
        if os.path.exists(path):
            try:
                with open(path,'r') as fp: 
                    data = json.load(fp)
                    if data: 
                        return data
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
    clean = country_code.upper().replace("_FB","").replace("_WS","").replace("_2","")
    flag = flags.get(clean, flags.get(clean.split("_")[0], "🌍"))
    otp_digits = ''.join(filter(str.isdigit, str(otp_code)))
    service_display = "Facebook" if "FACEBOOK" in service.upper() else service.title()
    earn_text = cfg["prices"].get(clean, cfg["prices"].get("DEFAULT", "+$0.003"))
    text = f"{flag} {clean.title()}\n📞 `{full_number}`\n💼 Service: {service_display}\n💳 Earned: {earn_text}"
    try:
        keyboard = [[InlineKeyboardButton(f"🔑 {otp_digits}", copy_text=CopyTextButton(otp_digits))]]
    except:
        keyboard = [[InlineKeyboardButton(f"📋 Copy {otp_digits}", callback_data=f"copy_{otp_digits}")]]
    return text, InlineKeyboardMarkup(keyboard)

def format_for_group(country_code, full_number, service, otp_code):
    cfg = load_config()
    flags = cfg["flags"]
    clean = country_code.upper().replace("_FB","").replace("_WS","").replace("_2","")
    masked = mask_number(full_number)
    otp_digits = ''.join(filter(str.isdigit, str(otp_code)))
    service_display = "Facebook" if "FACEBOOK" in service.upper() else service.title()
    text = f"APN NUMBER BOT\n💳 #{clean} 📱 {service_display}\n\n╭─────────────────╮\n  {masked}\n╰─────────────────╯"
    try:
        otp_btn = InlineKeyboardButton(f"🔓 {otp_digits}", copy_text=CopyTextButton(otp_digits))
    except:
        otp_btn = InlineKeyboardButton(f"🔓 {otp_digits}", callback_data=f"copy_{otp_digits}")
    keyboard = [[otp_btn], [InlineKeyboardButton(cfg["buttons"].get("number_btn","🔢 Number"), url=cfg["number_bot_url"]), InlineKeyboardButton(cfg["buttons"].get("channel_btn","📢 Channel"), url=cfg["community_url"])]]
    return text, InlineKeyboardMarkup(keyboard)

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
    print(f"[WATCHER START] {number} {order_id} {country_code}")
    # Voltx API: check every 10 sec for 3 min (18 checks)
    interval = 10
    max_checks = 18
    print(f"[WATCHER] {number} interval={interval}s max={max_checks} via 2oo9 API")
    for i in range(max_checks):
        await asyncio.sleep(interval)
        try:
            otp = await asyncio.to_thread(get_otp, order_id)
            if otp:
                print(f"[OTP FOUND] {number} -> {otp}")
                text_inbox, markup_inbox = format_for_inbox(country_code, number, service, otp)
                text_group, markup_group = format_for_group(country_code, number, service, otp)
                try:
                    await bot.send_message(chat_id=user_id, text=text_inbox, reply_markup=markup_inbox, parse_mode="Markdown")
                except:
                    await bot.send_message(chat_id=user_id, text=text_inbox, reply_markup=markup_inbox)
                try:
                    cfg = load_config()
                    await bot.send_message(chat_id=cfg["otp_group_id"], text=text_group, reply_markup=markup_group, parse_mode="Markdown")
                except Exception as e:
                    print(f"[FAIL GROUP] {e}")
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

# ADMIN COMMANDS
async def bot_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    save_json(MAINT_FILE, {"enabled": True, "reason": "Maintenance"})
    await update.message.reply_text("🔴 Bot OFF")

async def bot_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    save_json(MAINT_FILE, {"enabled": False})
    await update.message.reply_text("🟢 Bot ON")

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    cfg = load_config()
    txt = "⚙️ **ADMIN CONTROL PANEL - 2oo9 Voltx ONLY**\n\n"
    txt += f"📱 Buttons: {len(cfg['buttons'])}\n💰 Prices: {len(cfg['prices'])}\n\n"
    txt += "Commands:\n"
    txt += "/set_button <key> <name> - Button name change\n"
    txt += "/list_buttons - List all buttons\n"
    txt += "/set_price <country> <price>\n"
    txt += "/add <service> <country> <rid> - Add range\n"
    txt += "/del <service> <country>\n"
    txt += "/list - List ranges\n"
    txt += "/debug - Check stock\n"
    txt += "/clear_all_numbers confirm - Delete all\n"
    txt += "\n**2oo9 API:**\n"
    txt += "Base: api.2oo9.cloud\n"
    txt += "Set API key in Railway: VOLTX_API_KEY\n"
    
    kb = [
        [InlineKeyboardButton("📱 Buttons", callback_data="admin_buttons"), InlineKeyboardButton("💰 Prices", callback_data="admin_prices")],
        [InlineKeyboardButton("📋 Ranges", callback_data="admin_ranges"), InlineKeyboardButton("📊 Stats", callback_data="admin_stats")],
    ]
    await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def list_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    cfg = load_config()
    txt = "📱 **BUTTONS** - /set_button diye change koro:\n\n"
    for key, val in cfg["buttons"].items():
        txt += f"`{key}` = {val}\n"
    txt += "\nExample:\n/set_button get_number 🔥 Get OTP"
    await update.message.reply_text(txt, parse_mode="Markdown")

async def set_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        if len(context.args) < 2:
            await update.message.reply_text("❌ Use: /set_button <key> <new_name>\nExample: /set_button get_number 🔥 Get Number")
            return
        key = context.args[0].lower()
        new_name = " ".join(context.args[1:])
        cfg = load_config()
        if key not in cfg["buttons"]:
            await update.message.reply_text(f"❌ Key '{key}' not found! Available: " + ", ".join(cfg["buttons"].keys()))
            return
        old = cfg["buttons"][key]
        cfg["buttons"][key] = new_name
        save_config(cfg)
        await update.message.reply_text(f"✅ Button changed!\n\n`{key}`:\n{old} → {new_name}", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def set_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        if len(context.args) < 2:
            await update.message.reply_text("❌ Use: /set_price <country> <price>")
            return
        country = context.args[0].upper()
        price = context.args[1]
        cfg = load_config()
        old = cfg["prices"].get(country, "Not set")
        cfg["prices"][country] = price
        save_config(cfg)
        await update.message.reply_text(f"✅ Price: {old} → {price}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def clear_all_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if len(context.args) == 0 or context.args[0] != "confirm":
        await update.message.reply_text("⚠️ Delete ALL? Use: /clear_all_numbers confirm")
        return
    # For Voltx API, numbers are from API, not files, so just clear active
    save_json(ACTIVE_FILE, {})
    await update.message.reply_text("✅ Cleared active numbers")

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
        await update.message.reply_text(f"✅ Added {service} - {name} = {rid}\n\nNow /getnum will use rid {rid} for {name}")
    except:
        await update.message.reply_text("❌ Use: /add FB NEPAL 26134\nExample: /add FB NEPAL 26134")

async def del_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    try:
        service = context.args[0].upper()
        name = context.args[1].upper()
        if service == "FB": service = "FACEBOOK"
        if service == "WS": service = "WHATSAPP"
        data = load_json(RANGES_FILE, {"FACEBOOK":{}, "WHATSAPP":{}})
        if name in data.get(service, {}):
            del data[service][name]
            save_json(RANGES_FILE, data)
            await update.message.reply_text(f"🗑 Deleted {name}")
        else:
            await update.message.reply_text("❌ Not found")
    except:
        await update.message.reply_text("❌ Use: /del FB NEPAL")

async def list_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    data = load_json(RANGES_FILE, {"FACEBOOK":{}, "WHATSAPP":{}})
    txt = f"📋 **Ranges (2oo9 API)**\n\n"
    for srv, ranges in data.items():
        txt += f"{srv}:\n"
        for n, r in ranges.items():
            txt += f"- {n} = {r}\n"
        txt += "\n"
    txt += "Add: /add FB NEPAL 26134"
    await update.message.reply_text(txt, parse_mode="Markdown")

async def debug_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    data = load_json(RANGES_FILE, {})
    txt = "📊 **2oo9 API Ranges**\n\n"
    for srv, ranges in data.items():
        txt += f"{srv}: {len(ranges)} countries\n"
        for n, r in list(ranges.items())[:5]:
            txt += f"  {n}={r}\n"
    await update.message.reply_text(txt, parse_mode="Markdown")

async def get_my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Your ID: {update.effective_user.id}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    cfg = load_config()
    if is_maintenance() and uid != ADMIN_ID:
        await update.message.reply_text("🔧 Bot under maintenance")
        return
    if not await is_joined(uid, context):
        txt = "⚠️ Join our channels first!\n\n"
        kb = []
        for ch in cfg["must_join"]:
            ch_name = ch.replace("@","")
            kb.append([InlineKeyboardButton(f"📢 Join {ch_name}", url=f"https://t.me/{ch_name}")])
        kb.append([InlineKeyboardButton("✅ Joined", callback_data="check_join")])
        await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return
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

async def is_joined(user_id, context):
    if user_id == ADMIN_ID: return True
    cfg = load_config()
    for ch in cfg["must_join"]:
        try:
            m = await context.bot.get_chat_member(chat_id=ch, user_id=user_id)
            if m.status in ['left','kicked']: return False
        except: continue
    return True

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
            await update.message.reply_text("📋 No active numbers")
        else:
            txt = "📋 Your Numbers:\n\n"
            for n in nums[-10:]:
                txt += f"{n['number']} - {n['country']}\n"
            await update.message.reply_text(txt)
    elif text == buttons.get("balance","💰 Balance"):
        user = get_user(uid)
        await update.message.reply_text(f"💰 Balance: ${user.get('balance',0):.4f}")
    elif text == buttons.get("admin_panel","⚙️ Admin Panel") and uid == ADMIN_ID:
        await admin_panel(update, context)
    else:
        await update.message.reply_text("Use buttons")

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
            txt = "📱 **BUTTONS**\n\n"
            for k,v in cfg["buttons"].items():
                txt += f"`{k}` = {v}\n"
            txt += "\n/set_button get_number 🔥 Get OTP"
            await q.edit_message_text(txt, parse_mode="Markdown")
            return
        elif data == "admin_ranges":
            await list_range(update, context)
            return
        elif data == "admin_stats":
            data_r = load_json(RANGES_FILE, {})
            total = sum(len(v) for v in data_r.values() if isinstance(v, dict))
            await q.edit_message_text(f"📊 Total ranges: {total}\n\nUse /list to see all")
            return
    
    if data.startswith("s_"):
        service = data[2:]
        context.user_data['service'] = service
        countries = get_all_countries(service)
        if not countries:
            await q.edit_message_text(f"❌ No ranges for {service}! Use /add {service} NEPAL 26134")
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
        num_count = 1  # Voltx API gives 1 number at a time
        await q.edit_message_text(f"⏳ Fetching number for {display}...")
        nums = []
        try:
            order = await asyncio.to_thread(create_order, service, country_code)
            if order:
                nums.append(order)
                add_request(uid, display)
                save_active_number(uid, order['number'], country_code, service)
                context.application.create_task(otp_watcher(context.bot, order['id'], uid, order['number'], service, country_code))
        except Exception as e:
            print(f"[CREATE ERR] {e}")
        
        if not nums:
            await q.edit_message_text(f"❌ Out of Stock! {display}\n\nCheck /list - rid set?\nUse /add {service} {country_code} <rid>", parse_mode="Markdown")
            return
        header = f"{flag} {display} Fresh Number 💸\n📱 {service.title()}\n"
        txt = header
        kb = []
        for o in nums:
            try:
                kb.append([InlineKeyboardButton(f"{o['number']}", copy_text=CopyTextButton(o['number']))])
            except:
                kb.append([InlineKeyboardButton(f"{o['number']}", callback_data=f"copy_{o['number']}")])
        kb.append([InlineKeyboardButton(buttons.get("view_otp","📥 View OTP"), url=cfg["otp_group"])])
        kb.append([InlineKeyboardButton(buttons.get("change","🔄 Change"), callback_data=f"c_{country_code}"), InlineKeyboardButton(buttons.get("back","🔙 Back"), callback_data=f"s_{service}")])
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

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
app.add_handler(CommandHandler("set_price", set_price))
app.add_handler(CommandHandler("clear_all_numbers", clear_all_numbers))
app.add_handler(CommandHandler("list_buttons", list_buttons))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
app.add_handler(CallbackQueryHandler(handle))
app.run_polling(drop_pending_updates=True)
