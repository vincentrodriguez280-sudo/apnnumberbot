
import os, json, asyncio, shutil, re
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, CopyTextButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from panel import create_order, get_otp, get_all_countries, get_display_name

TOKEN = os.getenv("BOT_TOKEN")
MUST_JOIN = ["@APNOfficial", "@APNOTP"]
CH1 = "https://t.me/APNOfficial"
CH2 = "https://t.me/+3N7St38N__ZkMTZl"
BOT_LINK = "https://t.me/Proxystore999"
OTP_GROUP = "https://t.me/APNOTP"
OTP_GROUP_ID = "@APNOTP"
SUPPORT_ID = "https://t.me/PolasChandra"
SERVICES = ["FACEBOOK", "WHATSAPP"]

BASE_DIR = "/data" if os.path.exists("/data") else ("/app/data" if os.path.exists("/app/data") else ".")
try:
    import os as _os
    _os.makedirs(BASE_DIR, exist_ok=True)
except:
    pass
BAL_FILE = os.path.join(BASE_DIR, "balances.json")
TRAFFIC_FILE = os.path.join(BASE_DIR, "traffic.json")
SUCCESS_FILE = os.path.join(BASE_DIR, "success_traffic.json")
RANGES_FILE = os.path.join(BASE_DIR, "ranges.json")
MAINT_FILE = os.path.join(BASE_DIR, "maintenance.json")

ADMIN_ID = 1853202569
GROUP_NAME_TITLE = "APN OTP GROUP"
COMMUNITY_URL = "https://t.me/APNOfficial"
NUMBER_BOT_URL = "https://t.me/APNNUMBERBOT"
FLAGS = {"NEPAL": "🇳🇵", "MADAGASCAR": "🇲🇬", "HAITI": "🇭🇹", "MONTENEGRO": "🇲🇪", "SIERRA_LEONE": "🇸🇱", "USA": "🇺🇸", "CAMEROON": "🇨🇲"}

def load_json(f, default):
    if os.path.exists(f):
        try:
            with open(f,'r') as fp: return json.load(fp)
        except: return default
    return default
def save_json(f, data):
    os.makedirs(os.path.dirname(f) if os.path.dirname(f) else ".", exist_ok=True)
    with open(f,'w') as fp: json.dump(data, fp, indent=2)

def is_maintenance(): return load_json(MAINT_FILE, {"enabled": False}).get("enabled", False)
def get_user(uid):
    db = load_json(BAL_FILE, {})
    uid=str(uid)
    if uid not in db:
        db[uid]={"balance":0.0,"requests":[],"total":0,"ref":0}
        save_json(BAL_FILE, db)
    return db[uid]
def add_request(uid, country):
    db = load_json(BAL_FILE, {}); uid=str(uid)
    if uid not in db: db[uid]={"balance":0.0,"requests":[],"total":0,"ref":0}
    db[uid]["requests"].append(datetime.now().isoformat()); db[uid]["total"]+=1
    save_json(BAL_FILE, db)
    tr = load_json(TRAFFIC_FILE, {}); tr[country]=tr.get(country,0)+1; save_json(TRAFFIC_FILE, tr)
def add_success(country):
    tr = load_json(SUCCESS_FILE, {}); tr[country]=tr.get(country,0)+1; save_json(SUCCESS_FILE, tr)
def mask_number(num):
    n = num.replace(" ", "").replace("+", "").strip()
    if len(n) <= 6: return "+" + n
    return f"+{n[:4]}XXXXXX{n[-3:]}"

def format_for_inbox(country_code, full_number, service, otp_code):
    clean = country_code.upper().replace("_FB","").replace("_WS","").replace("_2","")
    country_name = clean.replace("_", " ").title()
    flag = FLAGS.get(clean, "🌍")
    # Service name - jeta number nise otar nam thakbe (Facebook/WhatsApp), TikTok na
    service_display = "Facebook" if service.upper() in ["FACEBOOK", "FB", "NEPAL", "NEPAL_FB"] else service.title()
    # OTP sudu button e thakbe, text e thakbe na
    text = f"✅ {country_name} {flag}\n📞 Number: {full_number}\n💼 Service: {service_display}"
    # Copy button - 1 click e copy hobe
    otp_digits = ''.join(filter(str.isdigit, str(otp_code)))
    try:
        keyboard = [[InlineKeyboardButton(f"🔑 {otp_digits}", copy_text=CopyTextButton(otp_digits))]]
    except Exception as e:
        # Fallback if CopyTextButton not supported in this version
        keyboard = [[InlineKeyboardButton(f"📋 Copy {otp_digits}", callback_data=f"copy_{otp_digits}")]]
    return text, InlineKeyboardMarkup(keyboard)

def format_for_group(country_code, full_number, service, otp_code):
    clean = country_code.upper().replace("_FB","").replace("_WS","").replace("_2","")
    country_name = clean.replace("_", " ").title()
    flag = FLAGS.get(clean, "🌍")
    masked = mask_number(full_number)
    # Service name - asol service er nam (Facebook/WhatsApp), TikTok na
    service_display = "Facebook" if service.upper() in ["FACEBOOK", "FB", "NEPAL", "NEPAL_FB"] else service.title()
    # OTP sudu button e thakbe, text e thakbe na - box e sudu masked number
    text = f"{GROUP_NAME_TITLE}\n🎉 NEW OTP RECEIVED 🎉\n\n🌍 Country: {country_name} {flag}\n📱 Number: {masked}\n🧰 Service: {service_display}"
    otp_digits = ''.join(filter(str.isdigit, str(otp_code)))
    try:
        otp_btn = InlineKeyboardButton(f"🔓 {otp_digits}", copy_text=CopyTextButton(otp_digits))
    except:
        otp_btn = InlineKeyboardButton(f"🔓 {otp_digits}", callback_data=f"copy_{otp_digits}")
    # Number click korle bot e jabe, Channel click korle channel e jabe
    # Panel lekha bad diye Channel, ar Channel er jaygay Number
    keyboard = [
        [otp_btn],
        [InlineKeyboardButton("🔢 Number", url=NUMBER_BOT_URL), InlineKeyboardButton("📢 Channel", url=COMMUNITY_URL)]
    ]
    return text, InlineKeyboardMarkup(keyboard)

async def is_joined(user_id, context):
    if user_id == ADMIN_ID: return True
    for ch in MUST_JOIN:
        try:
            m = await context.bot.get_chat_member(chat_id=ch, user_id=user_id)
            if m.status in ['left','kicked']: return False
        except: continue
    return True

async def otp_watcher(bot, order_id, user_id, number, service, country_code):
    print(f"[WATCHER START] {number} {order_id}")
    for i in range(180):
        await asyncio.sleep(5)
        try:
            otp = get_otp(order_id)
            if otp:
                print(f"[OTP FOUND] {number} -> {otp}")
                text_inbox, markup_inbox = format_for_inbox(country_code, number, service, otp)
                text_group, markup_group = format_for_group(country_code, number, service, otp)
                try: await bot.send_message(chat_id=user_id, text=text_inbox, reply_markup=markup_inbox)
                except: pass
                try: await bot.send_message(chat_id=OTP_GROUP_ID, text=text_group, reply_markup=markup_group)
                except Exception as e: print(f"[FAIL GROUP] {e}")
                db = load_json(BAL_FILE, {}); uid=str(user_id)
                if uid in db:
                    db[uid]["balance"]+=0.50; save_json(BAL_FILE, db)
                add_success(country_code)
                return
        except Exception as e: print(f"[WATCHER ERR] {e}")
    print(f"[TIMEOUT] {number}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_maintenance() and uid!= ADMIN_ID:
        await update.message.reply_text("🛠 System Under Maintenance"); return
    get_user(uid)
    if await is_joined(uid, context):
        kb = [[InlineKeyboardButton("📞 GET NUMBER", callback_data="services"), InlineKeyboardButton("💰 WITHDRAWAL", callback_data="withdrawal")], [InlineKeyboardButton("📊 LIVE TRAFFIC", callback_data="live"), InlineKeyboardButton("👑 MY STATUS", callback_data="my_status")], [InlineKeyboardButton("🆘 SUPPORT", url=SUPPORT_ID)]]
        if uid == ADMIN_ID: kb.append([InlineKeyboardButton("👑 ADMIN PANEL", callback_data="admin")])
        await update.message.reply_text("👑 APN NUMBER BOT\n\nWelcome!", reply_markup=InlineKeyboardMarkup(kb))
    else:
        kb = [[InlineKeyboardButton("📢 JOIN: APN OFFICIAL", url=CH1)], [InlineKeyboardButton("📢 JOIN: APN BACKUP", url=CH2)], [InlineKeyboardButton("🤖 JOIN: PROXY BOT", url=BOT_LINK)], [InlineKeyboardButton("👥 JOIN: APN OTP GROUP", url=OTP_GROUP)], [InlineKeyboardButton("✅ CHECK JOINED", callback_data="check")]]
        await update.message.reply_text("⚠ Access Required", reply_markup=InlineKeyboardMarkup(kb))

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data
    uid = q.from_user.id
    if data.startswith("copy_"):
        code = data.replace("copy_","")
        try:
            await q.answer(f"📋 Copied: {code}", show_alert=True)
        except:
            await q.answer()
        return
    try:
        await q.answer()
    except:
        pass
    if is_maintenance() and uid!= ADMIN_ID:
        await q.edit_message_text("🛠 System Under Maintenance"); return
    if data!= "check" and not await is_joined(uid, context):
        kb = [[InlineKeyboardButton("📢 APN OFFICIAL", url=CH1)], [InlineKeyboardButton("📢 APN BACKUP", url=CH2)], [InlineKeyboardButton("🤖 PROXY BOT", url=BOT_LINK)], [InlineKeyboardButton("👥 APN OTP GROUP", url=OTP_GROUP)], [InlineKeyboardButton("✅ CHECK JOINED", callback_data="check")]]
        await q.edit_message_text("❌ Access Denied", reply_markup=InlineKeyboardMarkup(kb)); return
    if data == "check":
        if await is_joined(uid, context):
            kb = [[InlineKeyboardButton("📞 GET NUMBER", callback_data="services"), InlineKeyboardButton("💰 WITHDRAWAL", callback_data="withdrawal")], [InlineKeyboardButton("📊 LIVE TRAFFIC", callback_data="live"), InlineKeyboardButton("👑 MY STATUS", callback_data="my_status")], [InlineKeyboardButton("🆘 SUPPORT", url=SUPPORT_ID)]]
            if uid == ADMIN_ID: kb.append([InlineKeyboardButton("👑 ADMIN PANEL", callback_data="admin")])
            await q.edit_message_text("✅ Verified!", reply_markup=InlineKeyboardMarkup(kb))
        else: await q.edit_message_text("❌ Not joined yet.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ CHECK JOINED", callback_data="check")]]))
        return
    if data == "main":
        kb = [[InlineKeyboardButton("📞 GET NUMBER", callback_data="services"), InlineKeyboardButton("💰 WITHDRAWAL", callback_data="withdrawal")], [InlineKeyboardButton("📊 LIVE TRAFFIC", callback_data="live"), InlineKeyboardButton("👑 MY STATUS", callback_data="my_status")], [InlineKeyboardButton("🆘 SUPPORT", url=SUPPORT_ID)]]
        if uid == ADMIN_ID: kb.append([InlineKeyboardButton("👑 ADMIN PANEL", callback_data="admin")])
        await q.edit_message_text("👑 APN NUMBER BOT", reply_markup=InlineKeyboardMarkup(kb)); return
    if data == "services":
        kb = [[InlineKeyboardButton(f"{s}", callback_data=f"s_{s}")] for s in SERVICES]
        kb.append([InlineKeyboardButton("❌ CLOSE", callback_data="main")])
        await q.edit_message_text("🔹 Select Service:", reply_markup=InlineKeyboardMarkup(kb)); return
    if data.startswith("s_"):
        service = data[2:]; context.user_data['service'] = service
        countries = get_all_countries(service)
        if not countries:
            await q.edit_message_text(f"❌ No ranges for {service}!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="services")]])); return
        kb = []
        ranges_data = load_json(RANGES_FILE, {"FACEBOOK":{}, "WHATSAPP":{}})
        for code in countries:
            display = get_display_name(code)
            rid = ranges_data.get(service, {}).get(code.upper(), "")
            btn_text = f"{display} {rid}" if rid else display
            kb.append([InlineKeyboardButton(btn_text, callback_data=f"c_{code}")])
        kb.append([InlineKeyboardButton("↩ CHANGE SERVICE", callback_data="services")])
        await q.edit_message_text(f"Service: {service}\nSelect country:", reply_markup=InlineKeyboardMarkup(kb)); return
    if data.startswith("c_"):
        country_code = data[2:]; service = context.user_data.get('service', 'FACEBOOK'); display = get_display_name(country_code)
        await q.edit_message_text(f"⏳ Fetching 3 numbers for {display}...")
        nums = []
        for i in range(3):
            order = create_order(service, country_code)
            if order:
                nums.append(order)
                add_request(uid, display)
                context.application.create_task(otp_watcher(context.bot, order['id'], uid, order['number'], service, country_code))
                await asyncio.sleep(1)
        if not nums:
            await q.edit_message_text(f"❌ Out of Stock! {display}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Try Again", callback_data=f"s_{service}")]])); return
        kb = [[InlineKeyboardButton("🌐 Change Country", callback_data=f"s_{service}")], [InlineKeyboardButton("🔄 Change Number", callback_data=f"c_{country_code}")], [InlineKeyboardButton("🛡 OTP Group", url=OTP_GROUP)]]
        txt = f"YOUR {display} {service} 3 NUMBERS\n\n"
        for o in nums: txt += f"`{o['number']}`\n"
        txt += f"\n⏳ OTP will be automatically forwarded to your Inbox and Group.\n👉 Tap number to copy!"
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"); return

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle))
app.run_polling(drop_pending_updates=True)
