import os, json, asyncio, shutil, re
from datetime import datetime, date
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, KeyboardButton, CopyTextButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from panel import create_order, get_otp, get_all_countries, get_display_name

print("[BOT] Starting with ADMIN CONTROL PANEL - Change buttons, prices, texts from bot!")

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 1853202569

# Default channels - can be changed via bot
DEFAULT_MUST_JOIN = ["@APNOfficial", "@APNOTP", "@Proxystore999"]
DEFAULT_CH1 = "https://t.me/APNOfficial"
DEFAULT_CH2 = "https://t.me/APNOTP"
DEFAULT_CH3 = "https://t.me/Proxystore999"
DEFAULT_OTP_GROUP = "https://t.me/APNOTP"
DEFAULT_OTP_GROUP_ID = "@APNOTP"
DEFAULT_SUPPORT_ID = "https://t.me/PolasChandra"
DEFAULT_SERVICES = ["FACEBOOK", "WHATSAPP", "TIKTOK"]
DEFAULT_COMMUNITY_URL = "https://t.me/APNOfficial"
DEFAULT_NUMBER_BOT_URL = "https://t.me/APNNUMBERBOT"

# Railway volume - /data support
for p in ["/data", "/app/data", "."]:
    try:
        if os.path.exists(p) or p in ["/data", "/app/data"]:
            os.makedirs(p, exist_ok=True)
            if os.path.exists(p):
                BASE_DIR = p
                print(f"[DATA] Using {BASE_DIR} (Volume found)" if p=="/data" else f"[DATA] Using {BASE_DIR}")
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
WALLET_FILE = os.path.join(BASE_DIR, "wallets.json")
SUBMIT_FILE = os.path.join(BASE_DIR, "submissions.json")
SUBMIT_TOGGLE_FILE = os.path.join(BASE_DIR, "submit_toggle.json")
SUBMIT_SHEET_FILE = os.path.join(BASE_DIR, "submitted_data.txt")
CONFIG_FILE = os.path.join(BASE_DIR, "bot_config.json")

if not os.path.exists(RANGES_FILE) and os.path.exists("ranges.json"):
    try:
        shutil.copy("ranges.json", RANGES_FILE)
    except: pass

# ===== BOT CONFIG - Change from bot! =====
DEFAULT_CONFIG = {
    "must_join": DEFAULT_MUST_JOIN,
    "ch1": DEFAULT_CH1,
    "ch2": DEFAULT_CH2,
    "ch3": DEFAULT_CH3,
    "otp_group": DEFAULT_OTP_GROUP,
    "otp_group_id": DEFAULT_OTP_GROUP_ID,
    "support_id": DEFAULT_SUPPORT_ID,
    "services": DEFAULT_SERVICES,
    "community_url": DEFAULT_COMMUNITY_URL,
    "number_bot_url": DEFAULT_NUMBER_BOT_URL,
    "flags": {
        "NEPAL": "🇳🇵", "NEPAL_FB": "🇳🇵",
        "CAMEROON": "🇨🇲", "GUINEA": "🇬🇳", "GUNIEA": "🇬🇳",
        "MADAGASCAR": "🇲🇬", "MONTENEGRO": "🇲🇪", "UKRAINE": "🇺🇦",
        "HAITI": "🇭🇹", "SIERRA_LEONE": "🇸🇱", "USA": "🇺🇸", "USA_FB": "🇺🇸",
        "MOROCCO": "🇲🇦", "NIGERIA": "🇳🇬", "MOZAMBIQUE": "🇲🇿", "MYANMAR": "🇲🇲", "MYANMAR_TT": "🇲🇲", "MOZAMBIQUE_TT": "🇲🇿", "ISRAEL": "🇮🇱",
        "BD": "🇧🇩", "BANGLADESH": "🇧🇩", "BANGLADESH_FB": "🇧🇩", "BD_FB": "🇧🇩", "HAD": "🇧🇩", "CAMBODIA": "🇰🇭"
    },
    "prices": {
        "NEPAL": "0.005$", "NEPAL_FB": "0.005$",
        "MOROCCO": "0.003$", "NIGERIA": "0.003$", "MOZAMBIQUE": "0.005$", "MYANMAR": "0.005$", "MYANMAR_TT": "0.005$", "MOZAMBIQUE_TT": "0.005$",
        "CAMEROON": "0.003$", "GUINEA": "0.003$", "MADAGASCAR": "0.003$",
        "MONTENEGRO": "0.003$", "UKRAINE": "0.003$", "HAITI": "0.003$",
        "SIERRA_LEONE": "0.003$", "USA": "0.003$", "USA_FB": "0.003$",
        "BD": "0.005$", "BANGLADESH": "0.005$", "BANGLADESH_FB": "0.005$", "BD_FB": "0.005$", "HAD": "0.005$", "MYANMAR_FB": "0.005$", "CAMBODIA": "0.005$",
        "DEFAULT": "0.003$"
    },
    "buttons": {
        "get_number": "📱 Get Number",
        "my_numbers": "📋 My Numbers",
        "balance": "💰 Balance",
        "refer": "👥 Refer",
        "help": "❓ Help",
        "wallet": "💳 Wallet",
        "submit_file": "📁 Submit File",
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
        "start": "Welcome to APN Number Bot! 🎉\n\nGet fresh numbers for Facebook, WhatsApp, TikTok verification!",
        "select_service": "💳 Select Platform:",
        "select_country": "💳 {platform} - দেশ সিলেক্ট করুন:",
        "fetching": "⏳ Fetching {count} numbers for {country}...",
        "no_stock": "❌ Out of Stock! {country}",
        "number_header": "────────── ⋆⋅☆⋅⋆ ──────────\n{flag} {country} Fresh Number 💸\n📱 {platform}\n────────── ⋆⋅☆⋅⋆ ──────────\n\n💫 Wait 5s Or Check The OTP Grup 🖤",
        "join_required": "⚠️ You must join our channels first!",
        "balance_text": "💰 Your Balance: ${balance:.4f}\n📊 Total Requests: {total}\n✅ Success: {success}"
    }
}

def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                cfg = json.load(f)
                # Merge with default to ensure all keys exist
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
        # Also save to ./ for backup
        with open("./bot_config.json", 'w') as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print(f"[CONFIG SAVE ERR] {e}")

BOT_CONFIG = load_config()

# Use config values
def get_cfg(key, default=None):
    return BOT_CONFIG.get(key, default)

FLAGS = BOT_CONFIG["flags"]
PRICES = BOT_CONFIG["prices"]
BUTTONS = BOT_CONFIG["buttons"]
TEXTS = BOT_CONFIG["texts"]
MUST_JOIN = BOT_CONFIG["must_join"]
CH1 = BOT_CONFIG["ch1"]
CH2 = BOT_CONFIG["ch2"]
CH3 = BOT_CONFIG["ch3"]
OTP_GROUP = BOT_CONFIG["otp_group"]
OTP_GROUP_ID = BOT_CONFIG["otp_group_id"]
SUPPORT_ID = BOT_CONFIG["support_id"]
SERVICES = BOT_CONFIG["services"]
COMMUNITY_URL = BOT_CONFIG["community_url"]
NUMBER_BOT_URL = BOT_CONFIG["number_bot_url"]

# ===== AUTO SYNC number files =====
def sync_number_files():
    try:
        files_to_sync = ["numbers.txt", "numbers_mozambique.txt", "numbers_myanmar.txt", "numbers_nepal.txt", "numbers_151.txt", "numbers_cambodia.txt", "numbers_cameroon.txt", "numbers_usa.txt", "numbers_bd.txt"]
        for fname in files_to_sync:
            src_candidates = [f"./{fname}", f"{fname}", os.path.join(".", fname), f"/app/{fname}"]
            dst = os.path.join(BASE_DIR, fname)
            if BASE_DIR in ["/data", "/app/data"]:
                if not os.path.exists(dst):
                    for src in src_candidates:
                        if os.path.exists(src) and os.path.getsize(src) > 10:
                            try:
                                with open(src,'r') as sf:
                                    src_numbers = [l.strip() for l in sf.readlines() if l.strip() and not l.strip().startswith("#") and any(c.isdigit() for c in l)]
                                if len(src_numbers) > 0:
                                    shutil.copy(src, dst)
                                    print(f"[SYNC] Copied {src} -> {dst} ({len(src_numbers)} numbers)")
                                    break
                            except Exception as e:
                                print(f"[SYNC COPY ERR] {e}")
                                pass
                else:
                    try:
                        with open(dst,'r') as f:
                            dst_numbers = [l.strip() for l in f.readlines() if l.strip() and not l.strip().startswith("#") and any(c.isdigit() for c in l)]
                        if len(dst_numbers) == 0:
                            for src in src_candidates:
                                if os.path.exists(src):
                                    try:
                                        with open(src,'r') as sf:
                                            src_content = sf.read()
                                            src_numbers = [l.strip() for l in src_content.split("\n") if l.strip() and not l.strip().startswith("#") and any(c.isdigit() for c in l)]
                                        if len(src_numbers) > 0:
                                            shutil.copy(src, dst)
                                            print(f"[SYNC] Refreshed {src} -> {dst} ({len(src_numbers)} numbers) - was empty")
                                            break
                                    except:
                                        continue
                    except: pass
    except Exception as e:
        print(f"[SYNC ERR] {e}")

sync_number_files()

BASE_DIR_FALLBACK = "."
try:
    os.makedirs(BASE_DIR, exist_ok=True)
except:
    BASE_DIR = "."

def load_json(f, default):
    for path in [f, os.path.join(".", os.path.basename(f)), os.path.join(BASE_DIR_FALLBACK, os.path.basename(f))]:
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
        db[uid]={"balance":0.0,"requests":[],"total":0,"ref":0,"referrals":0,"level":1,"wallet_method":None,"wallet_address":None,"referred_by":None}
        save_json(BAL_FILE, db)
    if "referrals" not in db[uid]: db[uid]["referrals"]=0
    if "level" not in db[uid]: db[uid]["level"]=1
    if "wallet_method" not in db[uid]: db[uid]["wallet_method"]=None
    if "wallet_address" not in db[uid]: db[uid]["wallet_address"]=None
    if "referred_by" not in db[uid]: db[uid]["referred_by"]=None
    if "balance" not in db[uid]: db[uid]["balance"]=0.0
    return db[uid]

def save_user(uid, data):
    db = load_json(BAL_FILE, {})
    db[str(uid)]=data
    save_json(BAL_FILE, db)

backup_counter = {"count": 0}

def add_request(uid, country):
    user = get_user(uid)
    user["requests"].append(datetime.now().isoformat())
    user["total"]+=1
    save_user(uid, user)
    tr = load_json(TRAFFIC_FILE, {})
    tr[country] = tr.get(country,0)+1
    save_json(TRAFFIC_FILE, tr)

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
    country_name = clean.replace("_", " ").title()
    flag = flags.get(clean, flags.get(clean.split("_")[0], "🌍"))
    otp_digits = ''.join(filter(str.isdigit, str(otp_code)))
    if service.upper() in ["FACEBOOK", "FB", "NEPAL", "NEPAL_FB"]:
        service_display = "Facebook"
    elif service.upper() in ["TIKTOK", "TT", "MOZAMBIQUE", "MOZAMBIQUE_TT"]:
        service_display = "TikTok"
    else:
        service_display = service.title()
    if "NEPAL" in clean.upper():
        earn_text = "+$0.005"
    else:
        earn_text = "+$0.003"
    text = f"{flag} {country_name}\n📞 `{full_number}`\n💼 Service: {service_display}\n💳 Earned: {earn_text}"
    try:
        keyboard = [[InlineKeyboardButton(f"🔑 {otp_digits}", copy_text=CopyTextButton(otp_digits))]]
    except:
        keyboard = [[InlineKeyboardButton(f"📋 Copy {otp_digits}", callback_data=f"copy_{otp_digits}")]]
    return text, InlineKeyboardMarkup(keyboard)

def format_for_group(country_code, full_number, service, otp_code):
    cfg = load_config()
    flags = cfg["flags"]
    number_bot_url = cfg["number_bot_url"]
    community_url = cfg["community_url"]
    buttons = cfg["buttons"]
    clean = country_code.upper().replace("_FB","").replace("_WS","").replace("_2","")
    masked = mask_number(full_number)
    otp_digits = ''.join(filter(str.isdigit, str(otp_code)))
    if service.upper() in ["FACEBOOK", "FB", "NEPAL", "NEPAL_FB"]:
        service_display = "Facebook"
    elif service.upper() in ["TIKTOK", "TT", "MOZAMBIQUE", "MOZAMBIQUE_TT"]:
        service_display = "TikTok"
    else:
        service_display = service.title()
    text = f"APN NUMBER BOT\n💳 #{clean} 📱 {service_display}\n\n╭─────────────────╮\n  {masked}\n╰─────────────────╯\n\n🗣 Language: #English"
    try:
        otp_btn = InlineKeyboardButton(f"🔓 {otp_digits}", copy_text=CopyTextButton(otp_digits))
    except:
        otp_btn = InlineKeyboardButton(f"🔓 {otp_digits}", callback_data=f"copy_{otp_digits}")
    keyboard = [
        [otp_btn],
        [InlineKeyboardButton(buttons.get("number_btn","🔢 Number"), url=number_bot_url), InlineKeyboardButton(buttons.get("channel_btn","📢 Channel"), url=community_url)]
    ]
    return text, InlineKeyboardMarkup(keyboard)

async def is_joined(user_id, context):
    if user_id == ADMIN_ID: return True
    cfg = load_config()
    must_join = cfg["must_join"]
    for ch in must_join:
        try:
            m = await context.bot.get_chat_member(chat_id=ch, user_id=user_id)
            if m.status in ['left','kicked']: return False
        except: continue
    return True

async def otp_watcher(bot, order_id, user_id, number, service, country_code):
    print(f"[WATCHER START] {number} {order_id} {country_code}")
    is_had = "had" in order_id.lower() or "MOZAMBIQUE" in country_code.upper() or "BD" in country_code.upper() or "BANGLADESH" in country_code.upper()
    interval = 25 if is_had else 20
    max_checks = 36 if is_had else 48
    print(f"[WATCHER] {number} interval={interval}s max={max_checks} (is_had={is_had})")
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
                    otp_group_id = cfg["otp_group_id"]
                    await bot.send_message(chat_id=otp_group_id, text=text_group, reply_markup=markup_group, parse_mode="Markdown")
                except Exception as e:
                    print(f"[FAIL GROUP] {e}")
                user = get_user(user_id)
                if "NEPAL" in country_code.upper():
                    earn = 0.005
                else:
                    earn = 0.003
                user["balance"]+=earn
                save_user(user_id, user)
                backup_counter["count"] += 1
                if backup_counter["count"] >= 20:
                    backup_counter["count"] = 0
                    try:
                        await auto_backup_task(bot)
                    except: pass
                print(f"[BALANCE] User {user_id} +${earn} -> ${user['balance']:.4f} | {country_code} {service}")
                if user.get("referred_by"):
                    ref_user = get_user(user["referred_by"])
                    refs = ref_user.get("referrals",0)
                    if refs >= 5000: comm = 0.0100
                    elif refs >= 2000: comm = 0.0070
                    elif refs >= 500: comm = 0.0006
                    elif refs >= 100: comm = 0.0005
                    else: comm = 0.0002
                    ref_user["balance"]+=comm
                    save_user(user["referred_by"], ref_user)
                add_success(country_code)
                return
        except Exception as e:
            print(f"[WATCHER ERR] {e}")
    print(f"[TIMEOUT] {number}")

# ========== ADMIN COMMANDS ==========

async def bot_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    reason = " ".join(context.args) if context.args else "Scheduled maintenance"
    save_json(MAINT_FILE, {"enabled": True, "reason": reason})
    await update.message.reply_text("🔴 Bot OFF")

async def bot_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    save_json(MAINT_FILE, {"enabled": False})
    await update.message.reply_text("🟢 Bot ON")

async def bot_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    status = "🔴 OFF" if is_maintenance() else "🟢 ON"
    cfg = load_config()
    txt = f"Bot Status: {status} | Path: {BASE_DIR}\n\n"
    txt += f"Buttons: {len(cfg['buttons'])}\n"
    txt += f"Prices: {len(cfg['prices'])}\n"
    txt += f"Flags: {len(cfg['flags'])}\n"
    txt += f"Services: {cfg['services']}"
    await update.message.reply_text(txt)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    cfg = load_config()
    txt = "⚙️ **ADMIN CONTROL PANEL**\n\n"
    txt += "Change everything from bot - no code edit needed!\n\n"
    txt += f"📱 Buttons: {len(cfg['buttons'])}\n"
    txt += f"💰 Prices: {len(cfg['prices'])}\n"
    txt += f"🏳️ Flags: {len(cfg['flags'])}\n"
    txt += f"📢 Channels: {len(cfg['must_join'])}\n"
    txt += f"🔧 Services: {cfg['services']}\n\n"
    txt += "Use buttons below or commands:\n"
    txt += "/set_button <key> <new_name>\n"
    txt += "/set_price <country> <price>\n"
    txt += "/set_flag <country> <emoji>\n"
    txt += "/set_text <key> <text>\n"
    txt += "/clear_all_numbers - Delete all numbers\n"
    txt += "/clear_country <country> - Clear country numbers\n"
    txt += "/list_buttons - List all buttons\n"
    txt += "/list_prices - List all prices\n"
    txt += "/set_channel <new_channel>\n"
    txt += "/add_channel <channel>\n"
    txt += "/del_channel <channel>\n"
    txt += "/backup - Backup data\n"
    txt += "/botstatus - Bot status"
    
    kb = [
        [InlineKeyboardButton("📱 Buttons", callback_data="admin_buttons"), InlineKeyboardButton("💰 Prices", callback_data="admin_prices")],
        [InlineKeyboardButton("🏳️ Flags", callback_data="admin_flags"), InlineKeyboardButton("📢 Channels", callback_data="admin_channels")],
        [InlineKeyboardButton("🔧 Services", callback_data="admin_services"), InlineKeyboardButton("📝 Texts", callback_data="admin_texts")],
        [InlineKeyboardButton("🗑️ Clear All Numbers", callback_data="admin_clear_all"), InlineKeyboardButton("📊 Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("🔙 Back", callback_data="services")]
    ]
    await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def list_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    cfg = load_config()
    txt = "📱 **BUTTONS LIST**\n\n"
    for key, val in cfg["buttons"].items():
        txt += f"`{key}` = {val}\n"
    txt += "\nChange: /set_button <key> <new_name>\nExample: /set_button get_number 🔥 Get OTP"
    await update.message.reply_text(txt, parse_mode="Markdown")

async def list_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    cfg = load_config()
    txt = "💰 **PRICES LIST**\n\n"
    for key, val in cfg["prices"].items():
        txt += f"`{key}` = {val}\n"
    txt += "\nChange: /set_price <country> <price>\nExample: /set_price NEPAL 0.010$"
    await update.message.reply_text(txt, parse_mode="Markdown")

async def set_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        if len(context.args) < 2:
            await update.message.reply_text("❌ Use: /set_button <key> <new_name>\nExample: /set_button get_number 🔥 Get Number\n\nKeys: get_number, my_numbers, balance, refer, help, wallet, back, change, view_otp, number_btn, channel_btn, etc")
            return
        key = context.args[0].lower()
        new_name = " ".join(context.args[1:])
        cfg = load_config()
        if key not in cfg["buttons"]:
            await update.message.reply_text(f"❌ Key '{key}' not found!\n\nAvailable keys:\n" + "\n".join(cfg["buttons"].keys()))
            return
        old = cfg["buttons"][key]
        cfg["buttons"][key] = new_name
        save_config(cfg)
        global BUTTONS
        BUTTONS = cfg["buttons"]
        await update.message.reply_text(f"✅ Button changed!\n\n`{key}`: {old} → {new_name}", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def set_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        if len(context.args) < 2:
            await update.message.reply_text("❌ Use: /set_price <country> <price>\nExample: /set_price NEPAL 0.010$\nExample: /set_price DEFAULT 0.005$")
            return
        country = context.args[0].upper()
        price = context.args[1]
        cfg = load_config()
        old = cfg["prices"].get(country, "Not set")
        cfg["prices"][country] = price
        save_config(cfg)
        global PRICES
        PRICES = cfg["prices"]
        await update.message.reply_text(f"✅ Price changed!\n\n{country}: {old} → {price}", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def set_flag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        if len(context.args) < 2:
            await update.message.reply_text("❌ Use: /set_flag <country> <emoji>\nExample: /set_flag NEPAL 🇳🇵")
            return
        country = context.args[0].upper()
        flag = context.args[1]
        cfg = load_config()
        old = cfg["flags"].get(country, "Not set")
        cfg["flags"][country] = flag
        save_config(cfg)
        global FLAGS
        FLAGS = cfg["flags"]
        await update.message.reply_text(f"✅ Flag changed!\n\n{country}: {old} → {flag}", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def set_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        if len(context.args) < 2:
            cfg = load_config()
            txt = "📝 **TEXTS LIST**\n\n"
            for k, v in cfg["texts"].items():
                txt += f"`{k}` = {v[:50]}...\n"
            txt += "\nChange: /set_text <key> <new_text>"
            await update.message.reply_text(txt, parse_mode="Markdown")
            return
        key = context.args[0].lower()
        new_text = " ".join(context.args[1:])
        cfg = load_config()
        if key not in cfg["texts"]:
            await update.message.reply_text(f"❌ Key '{key}' not found! Available: " + ", ".join(cfg["texts"].keys()))
            return
        old = cfg["texts"][key]
        cfg["texts"][key] = new_text
        save_config(cfg)
        global TEXTS
        TEXTS = cfg["texts"]
        await update.message.reply_text(f"✅ Text changed!\n\n`{key}`:\nOld: {old[:100]}\nNew: {new_text[:100]}", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        if len(context.args) < 1:
            cfg = load_config()
            await update.message.reply_text(f"Current channels: {cfg['must_join']}\n\nUse: /set_channel @NewChannel\n/add_channel @Channel\n/del_channel @Channel")
            return
        new_ch = context.args[0]
        cfg = load_config()
        cfg["must_join"] = [new_ch]
        cfg["ch1"] = f"https://t.me/{new_ch.replace('@','')}"
        save_config(cfg)
        await update.message.reply_text(f"✅ Main channel set to {new_ch}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        if len(context.args) < 1:
            await update.message.reply_text("❌ Use: /add_channel @ChannelName")
            return
        new_ch = context.args[0]
        cfg = load_config()
        if new_ch not in cfg["must_join"]:
            cfg["must_join"].append(new_ch)
            save_config(cfg)
            await update.message.reply_text(f"✅ Added channel {new_ch}\nNow: {cfg['must_join']}")
        else:
            await update.message.reply_text(f"⚠️ Channel {new_ch} already exists!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def del_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        if len(context.args) < 1:
            await update.message.reply_text("❌ Use: /del_channel @ChannelName")
            return
        ch = context.args[0]
        cfg = load_config()
        if ch in cfg["must_join"]:
            cfg["must_join"].remove(ch)
            save_config(cfg)
            await update.message.reply_text(f"✅ Removed {ch}\nNow: {cfg['must_join']}")
        else:
            await update.message.reply_text(f"❌ Channel {ch} not found! Current: {cfg['must_join']}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def clear_all_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        # Confirm
        if len(context.args) == 0 or context.args[0] != "confirm":
            await update.message.reply_text("⚠️ **DELETE ALL NUMBERS?**\n\nThis will delete ALL number files!\n\nConfirm: /clear_all_numbers confirm", parse_mode="Markdown")
            return
        
        files = ["numbers.txt", "numbers_mozambique.txt", "numbers_myanmar.txt", "numbers_nepal.txt", "numbers_151.txt", "numbers_cambodia.txt", "numbers_cameroon.txt", "numbers_usa.txt", "numbers_bd.txt"]
        deleted = 0
        for fname in files:
            for base in [BASE_DIR, ".", "/data", "/app/data"]:
                fpath = os.path.join(base, fname)
                if os.path.exists(fpath):
                    try:
                        # Clear file content but keep file
                        with open(fpath, 'w') as f:
                            f.write("# Cleared by admin\n")
                        deleted += 1
                        print(f"[CLEAR] Cleared {fpath}")
                    except: pass
        
        await update.message.reply_text(f"✅ Cleared {deleted} number files! All numbers deleted.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def clear_country_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        if len(context.args) < 1:
            await update.message.reply_text("❌ Use: /clear_country <country>\nExample: /clear_country NEPAL\nExample: /clear_country MOZAMBIQUE")
            return
        country = context.args[0].upper()
        file_map = {
            "MOZAMBIQUE": "numbers_mozambique.txt",
            "MYANMAR": "numbers_myanmar.txt",
            "NEPAL": "numbers_nepal.txt",
            "CAMEROON": "numbers_cameroon.txt",
            "USA": "numbers_usa.txt",
            "BD": "numbers_bd.txt",
            "CAMBODIA": "numbers_cambodia.txt",
            "NEPAL_FB": "numbers_nepal.txt",
            "MOZAMBIQUE_TT": "numbers_mozambique.txt",
            "MYANMAR_TT": "numbers_myanmar.txt",
        }
        fname = file_map.get(country, f"numbers_{country.lower()}.txt")
        cleared = 0
        for base in [BASE_DIR, ".", "/data"]:
            fpath = os.path.join(base, fname)
            if os.path.exists(fpath):
                try:
                    with open(fpath, 'w') as f:
                        f.write(f"# Cleared {country} by admin\n")
                    cleared += 1
                except: pass
        
        if cleared > 0:
            await update.message.reply_text(f"✅ Cleared {country} numbers! File: {fname}")
        else:
            await update.message.reply_text(f"❌ File not found for {country}! Tried: {fname}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

# ========== EXISTING COMMANDS (Keep same) ==========

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
        await update.message.reply_text(f"✅ Added {service} - {name} = {rid}")
    except:
        await update.message.reply_text("❌ Use: /add FB CAMEROON 23762")

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
        await update.message.reply_text("❌ Use: /del FB CAMEROON")

async def list_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    data = load_json(RANGES_FILE, {"FACEBOOK":{}, "WHATSAPP":{}})
    txt = f"📋 Ranges ({BASE_DIR}):\n\n"
    for srv, ranges in data.items():
        txt += f"{srv}:\n"
        for n, r in ranges.items():
            txt += f"- {n} = {r}\n"
        txt += "\n"
    await update.message.reply_text(txt)

async def auto_backup_task(bot):
    try:
        if not os.path.exists(BAL_FILE): return
        db = load_json(BAL_FILE, {})
        count = len(db)
        total_bal = sum([u.get("balance",0) for u in db.values()])
        txt = f"🔄 Auto Backup - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n👥 Users: {count}\n💰 Total: ${total_bal:.4f}"
        try:
            await bot.send_message(chat_id=ADMIN_ID, text=txt)
            await bot.send_document(chat_id=ADMIN_ID, document=open(BAL_FILE, 'rb'), filename=f"backup_{datetime.now().strftime('%Y%m%d_%H%M')}_balances.json")
        except Exception as e:
            print(f"[AUTO BACKUP ERR] {e}")
    except Exception as e:
        print(f"[AUTO BACKUP ERR] {e}")

async def backup_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        db = load_json(BAL_FILE, {})
        count = len(db)
        total_bal = sum([u.get("balance",0) for u in db.values()])
        txt = f"💾 Backup Info (FREE MODE)\n\n📁 Path: {BAL_FILE}\n👥 Users: {count}\n💰 Total Balance: ${total_bal:.4f}\n📂 Also saved in: ./balances.json"
        await update.message.reply_text(txt)
        for fp in [BAL_FILE, "./balances.json"]:
            if os.path.exists(fp):
                try:
                    await update.message.reply_document(document=open(fp, 'rb'), filename="balances.json")
                    break
                except: continue
    except Exception as e:
        await update.message.reply_text(f"❌ Backup error: {e}")

async def restore_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    txt = f"📂 Data Path: {BASE_DIR} + ./\n\nFiles:\n"
    for fn in ["balances.json", "traffic.json", "success_traffic.json", "ranges.json", "wallets.json", "bot_config.json"]:
        found = []
        for base in [BASE_DIR, "."]:
            fp = os.path.join(base, fn)
            if os.path.exists(fp):
                size = os.path.getsize(fp)
                found.append(f"{base}/{fn} ({size}b)")
        if found:
            txt += f"✅ {fn}: {' , '.join(found)}\n"
        else:
            txt += f"❌ {fn}: not found\n"
    await update.message.reply_text(txt)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if context.user_data.get("awaiting_file_submit") or (update.message.document and not (update.effective_user.id == ADMIN_ID and ("balances" in update.message.document.file_name.lower() or "backup" in update.message.document.file_name.lower()))):
        if not is_file_submit_enabled():
            await update.message.reply_text("❌ File Submit is disabled")
            context.user_data["awaiting_file_submit"] = False
            return
        
        doc = update.message.document
        if not doc:
            return
        
        fname = doc.file_name.lower()
        allowed = ['xls', 'xlsx', 'txt', 'csv', 'doc', 'docx']
        is_allowed = any(fname.endswith(ext) for ext in allowed)
        
        if not is_allowed and not context.user_data.get("awaiting_file_submit"):
            if uid != ADMIN_ID:
                return
        
        if uid == ADMIN_ID and ("balances" in fname or "backup" in fname):
            try:
                file = await context.bot.get_file(doc.file_id)
                for path in [BAL_FILE, "./balances.json"]:
                    try:
                        await file.download_to_drive(path)
                    except: pass
                db = load_json(BAL_FILE, {})
                await update.message.reply_text(f"✅ Restored! Users: {len(db)}")
            except Exception as e:
                await update.message.reply_text(f"❌ Restore failed: {e}")
            return
        
        try:
            file = await context.bot.get_file(doc.file_id)
            submit_dir = os.path.join(BASE_DIR, "submitted_files")
            os.makedirs(submit_dir, exist_ok=True)
            file_path = os.path.join(submit_dir, f"{uid}_{int(datetime.now().timestamp())}_{doc.file_name}")
            await file.download_to_drive(file_path)
            
            content_text = ""
            try:
                if fname.endswith('.txt') or fname.endswith('.csv'):
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content_text = f.read()
                elif fname.endswith('.xls') or fname.endswith('.xlsx'):
                    try:
                        import pandas as pd
                        df = pd.read_excel(file_path)
                        if len(df.columns) >= 3:
                            lines = []
                            for _, row in df.iterrows():
                                uid_c = str(row.iloc[0])
                                pwd = str(row.iloc[1])
                                cookies = str(row.iloc[2])
                                lines.append(f"{uid_c}  {pwd}  {cookies}")
                            content_text = "\n".join(lines)
                        else:
                            content_text = df.to_string()
                    except:
                        content_text = f"File: {doc.file_name}"
            except:
                content_text = f"File: {doc.file_name}"
            
            await update.message.reply_text(f"✅ File submitted! {len(content_text)} chars")
            context.user_data["awaiting_file_submit"] = False
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

# ... (rest of existing handlers - keep same as before, truncated for brevity)
# We'll include full existing logic below

def is_file_submit_enabled():
    try:
        data = load_json(SUBMIT_TOGGLE_FILE, {"enabled": True})
        return data.get("enabled", True)
    except:
        return True

async def file_submit_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    cmd = update.message.text.split()[0].lower()
    enabled = "on" in cmd or "file_on" in cmd
    if "off" in cmd:
        enabled = False
    save_json(SUBMIT_TOGGLE_FILE, {"enabled": enabled})
    await update.message.reply_text(f"{'✅ File Submit ON' if enabled else '❌ File Submit OFF'}")

async def file_submit_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    enabled = is_file_submit_enabled()
    await update.message.reply_text(f"File Submit: {'✅ ON' if enabled else '❌ OFF'}")

async def view_submissions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        data = load_json(SUBMIT_FILE, [])
        await update.message.reply_text(f"📁 Submissions: {len(data)}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def export_submissions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        if os.path.exists(SUBMIT_SHEET_FILE):
            await update.message.reply_document(document=open(SUBMIT_SHEET_FILE, 'rb'), filename="submissions.txt")
        else:
            await update.message.reply_text("❌ No submissions file")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def get_my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Your ID: {update.effective_user.id}")

async def debug_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    txt = "📊 **NUMBERS STOCK**\n\n"
    files = ["numbers.txt", "numbers_mozambique.txt", "numbers_myanmar.txt", "numbers_nepal.txt", "numbers_151.txt", "numbers_cambodia.txt", "numbers_cameroon.txt", "numbers_usa.txt", "numbers_bd.txt"]
    for fname in files:
        for base in [BASE_DIR, "."]:
            fpath = os.path.join(base, fname)
            if os.path.exists(fpath):
                try:
                    with open(fpath, 'r') as f:
                        lines = [l.strip() for l in f.readlines() if l.strip() and not l.strip().startswith("#") and any(c.isdigit() for c in l)]
                    txt += f"{fname}: {len(lines)}\n"
                except: pass
                break
    await update.message.reply_text(txt, parse_mode="Markdown")

async def refresh_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    sync_number_files()
    await update.message.reply_text("🔄 Refreshed number files from GitHub")

async def clear_mozambique(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        for base in [BASE_DIR, "."]:
            fpath = os.path.join(base, "numbers_mozambique.txt")
            if os.path.exists(fpath):
                with open(fpath, 'w') as f:
                    f.write("# Cleared\n")
        await update.message.reply_text("✅ Cleared Mozambique numbers")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

# START and HANDLE (Main bot logic)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    cfg = load_config()
    buttons = cfg["buttons"]
    texts = cfg["texts"]
    must_join = cfg["must_join"]
    
    # Check maintenance
    if is_maintenance() and uid != ADMIN_ID:
        data = load_json(MAINT_FILE, {})
        await update.message.reply_text(f"🔧 Bot under maintenance\n\nReason: {data.get('reason','Maintenance')}")
        return
    
    # Check join
    if not await is_joined(uid, context):
        txt = texts.get("join_required", "⚠️ You must join our channels first!") + "\n\n"
        kb = []
        for ch in must_join:
            ch_name = ch.replace("@","")
            kb.append([InlineKeyboardButton(f"📢 Join {ch_name}", url=f"https://t.me/{ch_name}")])
        kb.append([InlineKeyboardButton("✅ Joined", callback_data="check_join")])
        await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return
    
    # Referral
    if context.args and len(context.args) > 0:
        try:
            ref_id = int(context.args[0])
            if ref_id != uid:
                user = get_user(uid)
                if not user.get("referred_by"):
                    user["referred_by"] = ref_id
                    save_user(uid, user)
                    ref_user = get_user(ref_id)
                    ref_user["referrals"] = ref_user.get("referrals",0) + 1
                    save_user(ref_id, ref_user)
        except: pass
    
    # Main menu
    txt = texts.get("start", "Welcome to APN Number Bot! 🎉")
    kb = [
        [KeyboardButton(buttons.get("get_number","📱 Get Number"))],
        [KeyboardButton(buttons.get("my_numbers","📋 My Numbers")), KeyboardButton(buttons.get("balance","💰 Balance"))],
        [KeyboardButton(buttons.get("refer","👥 Refer")), KeyboardButton(buttons.get("help","❓ Help"))],
    ]
    if uid == ADMIN_ID:
        kb.append([KeyboardButton(buttons.get("admin_panel","⚙️ Admin Panel"))])
    
    reply_markup = ReplyKeyboardMarkup(kb, resize_keyboard=True)
    await update.message.reply_text(txt, reply_markup=reply_markup)

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text
    cfg = load_config()
    buttons = cfg["buttons"]
    
    # Map button texts to actions
    if text == buttons.get("get_number","📱 Get Number"):
        await show_services(update, context)
    elif text == buttons.get("my_numbers","📋 My Numbers"):
        nums = get_active_numbers(uid)
        if not nums:
            await update.message.reply_text("📋 No active numbers")
        else:
            txt = "📋 **Your Active Numbers**\n\n"
            for n in nums[-10:]:
                txt += f"📞 {n['number']} - {n['country']} ({n['service']})\n"
            await update.message.reply_text(txt, parse_mode="Markdown")
    elif text == buttons.get("balance","💰 Balance"):
        user = get_user(uid)
        tr = load_json(TRAFFIC_FILE, {})
        total = user.get("total",0)
        txt = cfg["texts"].get("balance_text","💰 Balance: ${balance:.4f}").format(balance=user.get("balance",0), total=total, success=len(tr))
        await update.message.reply_text(txt, parse_mode="Markdown")
    elif text == buttons.get("admin_panel","⚙️ Admin Panel") and uid == ADMIN_ID:
        await admin_panel(update, context)
    elif text == buttons.get("refer","👥 Refer"):
        bot_username = (await context.bot.get_me()).username
        txt = f"👥 **Refer & Earn**\n\nYour referral link:\nhttps://t.me/{bot_username}?start={uid}\n\nEarn commission on each referral!"
        await update.message.reply_text(txt, parse_mode="Markdown")
    elif text == buttons.get("help","❓ Help"):
        await update.message.reply_text("❓ Help: Contact @PolasChandra")
    else:
        await update.message.reply_text(f"Unknown command: {text}")

async def show_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = load_config()
    buttons = cfg["buttons"]
    texts = cfg["texts"]
    txt = texts.get("select_service","💳 Select Platform:")
    kb = []
    for srv in cfg["services"]:
        key = f"services_{srv.lower()}"
        btn_text = buttons.get(key, srv)
        kb.append([InlineKeyboardButton(btn_text, callback_data=f"s_{srv}")])
    kb.append([InlineKeyboardButton(buttons.get("back","⬅️ Back"), callback_data="main_menu")])
    if isinstance(update, Update) and update.message:
        await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
    else:
        # Callback query
        await update.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    uid = q.from_user.id
    cfg = load_config()
    buttons = cfg["buttons"]
    texts = cfg["texts"]
    
    if data == "check_join":
        if await is_joined(uid, context):
            await start(update, context)
        else:
            await q.edit_message_text("❌ You haven't joined all channels yet!")
        return
    
    if data == "main_menu":
        await show_services(q, context)
        return
    
    if data == "services":
        await show_services(q, context)
        return
    
    # Admin panel callbacks
    if data.startswith("admin_") and uid == ADMIN_ID:
        if data == "admin_buttons":
            await list_buttons(update, context)
            return
        elif data == "admin_prices":
            await list_prices(update, context)
            return
        elif data == "admin_flags":
            cfg = load_config()
            txt = "🏳️ **FLAGS LIST**\n\n"
            for k,v in cfg["flags"].items():
                txt += f"`{k}` = {v}\n"
            txt += "\nChange: /set_flag <country> <emoji>"
            await q.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_panel")]]))
            return
        elif data == "admin_channels":
            cfg = load_config()
            txt = f"📢 **CHANNELS**\n\nCurrent: {cfg['must_join']}\n\nCommands:\n/add_channel @Channel\n/del_channel @Channel\n/set_channel @Channel"
            await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_panel")]]))
            return
        elif data == "admin_services":
            cfg = load_config()
            txt = f"🔧 **SERVICES**\n\nCurrent: {cfg['services']}\n\nEdit bot_config.json to change services"
            await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_panel")]]))
            return
        elif data == "admin_texts":
            cfg = load_config()
            txt = "📝 **TEXTS LIST**\n\n"
            for k,v in cfg["texts"].items():
                txt += f"`{k}` = {v[:40]}...\n"
            txt += "\nChange: /set_text <key> <text>"
            await q.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_panel")]]))
            return
        elif data == "admin_clear_all":
            await q.edit_message_text("⚠️ Delete ALL numbers?\n\nUse: /clear_all_numbers confirm", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_panel")]]))
            return
        elif data == "admin_stats":
            db = load_json(BAL_FILE, {})
            tr = load_json(TRAFFIC_FILE, {})
            txt = f"📊 **STATS**\n\nUsers: {len(db)}\nRequests: {sum(tr.values())}\n\n"
            for k,v in tr.items():
                txt += f"{k}: {v}\n"
            await q.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_panel")]]))
            return
        elif data == "admin_panel":
            await admin_panel(update, context)
            return
    
    if data.startswith("s_"):
        service = data[2:]
        context.user_data['service'] = service
        countries = get_all_countries(service)
        if not countries:
            await q.edit_message_text(f"❌ No ranges for {service}!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="services")]]))
            return
        seen_base = set()
        unique_countries = []
        for c in countries:
            base = c.upper().split("_")[0]
            if base not in seen_base or "NEPAL" in base:
                if "NEPAL" in base:
                    if "NEPAL" not in seen_base:
                        unique_countries.append("NEPAL_FB")
                        seen_base.add("NEPAL")
                else:
                    unique_countries.append(c.upper())
                    seen_base.add(base)
        unique_countries = [c for c in unique_countries if "NEPAL" not in c]
        if service.upper() == "FACEBOOK":
            unique_countries.insert(0, "NEPAL_FB")
        countries_sorted = unique_countries
        platform_name = "Facebook" if service.upper() == "FACEBOOK" else service.title()
        txt = cfg["texts"].get("select_country","💳 {platform} - দেশ সিলেক্ট করুন:").format(platform=platform_name)
        kb = []
        for code in countries_sorted:
            display = get_display_name(code)
            base_key = code.upper().split("_")[0]
            flag = cfg["flags"].get(code.upper(), cfg["flags"].get(base_key, "🌍"))
            price = cfg["prices"].get(code.upper(), cfg["prices"].get(base_key, cfg["prices"].get("DEFAULT", "0.003$")))
            btn_text = f"{flag} {display} {price}"
            kb.append([InlineKeyboardButton(btn_text, callback_data=f"c_{code}")])
        kb.append([InlineKeyboardButton(buttons.get("back","⬅️ Back"), callback_data="services")])
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data.startswith("c_"):
        country_code = data[2:]
        service = context.user_data.get('service', 'FACEBOOK')
        display = get_display_name(country_code)
        cfg = load_config()
        flag = cfg["flags"].get(country_code.upper(), cfg["flags"].get(country_code.upper().split("_")[0], "🌍"))
        num_count = 8
        await q.edit_message_text(cfg["texts"].get("fetching","⏳ Fetching {count} numbers for {country}...").format(count=num_count, country=display))
        nums = []
        max_attempts = num_count * 3
        attempts = 0
        while len(nums) < num_count and attempts < max_attempts:
            attempts += 1
            try:
                order = await asyncio.to_thread(create_order, service, country_code)
            except Exception as e:
                print(f"[CREATE THREAD ERR] {e}")
                order = None
            
            if order:
                if not any(o['number'] == order['number'] for o in nums):
                    nums.append(order)
                    add_request(uid, display)
                    save_active_number(uid, order['number'], country_code, service)
                    context.application.create_task(otp_watcher(context.bot, order['id'], uid, order['number'], service, country_code))
                    print(f"[FETCH] Got {len(nums)}/{num_count}: {order['number']} for {display}")
                else:
                    print(f"[FETCH] Duplicate skipped: {order['number']}")
            else:
                print(f"[FETCH] Failed attempt {attempts}/{max_attempts} for {display}")
            
            await asyncio.sleep(0.5)
        
        print(f"[FETCH DONE] Requested {num_count}, got {len(nums)} for {display}")
        if not nums:
            await q.edit_message_text(cfg["texts"].get("no_stock","❌ Out of Stock! {country}").format(country=display), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Try Again", callback_data=f"s_{service}")]]))
            return
        platform_name = "Facebook" if service.upper() == "FACEBOOK" else service.title()
        header = cfg["texts"].get("number_header","────────── ⋆⋅☆⋅⋆ ──────────\n{flag} {country} Fresh Number 💸\n📱 {platform}\n────────── ⋆⋅☆⋅⋆ ──────────\n\n💫 Wait 5s Or Check The OTP Grup 🖤").format(flag=flag, country=display, platform=platform_name)
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
app.add_handler(CommandHandler("mynumbers", debug_numbers))
app.add_handler(CommandHandler("refresh", refresh_numbers))
app.add_handler(CommandHandler("clearmoz", clear_mozambique))
app.add_handler(CommandHandler("clear_mozambique", clear_mozambique))
app.add_handler(CommandHandler("file_on", file_submit_toggle))
app.add_handler(CommandHandler("file_off", file_submit_toggle))
app.add_handler(CommandHandler("file", file_submit_toggle))
app.add_handler(CommandHandler("filesubmit", file_submit_toggle))
app.add_handler(CommandHandler("file_status", file_submit_status))
app.add_handler(CommandHandler("submissions", view_submissions))
app.add_handler(CommandHandler("export_submissions", export_submissions))
app.add_handler(CommandHandler("id", get_my_id))
app.add_handler(CommandHandler("add", add_range))
app.add_handler(CommandHandler("del", del_range))
app.add_handler(CommandHandler("list", list_range))
app.add_handler(CommandHandler("off", bot_off))
app.add_handler(CommandHandler("on", bot_on))
app.add_handler(CommandHandler("botstatus", bot_status))
app.add_handler(CommandHandler("backup", backup_data))
app.add_handler(CommandHandler("data", restore_info))
# NEW ADMIN COMMANDS - Change everything from bot!
app.add_handler(CommandHandler("set_button", set_button))
app.add_handler(CommandHandler("set_price", set_price))
app.add_handler(CommandHandler("set_flag", set_flag))
app.add_handler(CommandHandler("set_text", set_text))
app.add_handler(CommandHandler("set_channel", set_channel))
app.add_handler(CommandHandler("add_channel", add_channel))
app.add_handler(CommandHandler("del_channel", del_channel))
app.add_handler(CommandHandler("clear_all_numbers", clear_all_numbers))
app.add_handler(CommandHandler("clear_country", clear_country_numbers))
app.add_handler(CommandHandler("list_buttons", list_buttons))
app.add_handler(CommandHandler("list_prices", list_prices))

app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
app.add_handler(CallbackQueryHandler(handle))
app.run_polling(drop_pending_updates=True)
