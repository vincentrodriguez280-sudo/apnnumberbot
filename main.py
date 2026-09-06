import os, json, asyncio, shutil, re
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from panel import create_order, get_otp, get_all_countries, get_display_name

TOKEN = os.getenv("BOT_TOKEN")
MUST_JOIN = ["@APNOfficial", "@APNOTP", "@APNOfficial"]  # 3 channels for UCHIHA style
CH1 = "https://t.me/APNOfficial"
CH2 = "https://t.me/APNOTP"
CH3 = "https://t.me/Proxystore999"
BOT_LINK = "https://t.me/Proxystore999"
OTP_GROUP = "https://t.me/APNOTP"
OTP_GROUP_ID = "@APNOTP"
SUPPORT_ID = "https://t.me/PolasChandra"
SERVICES = ["FACEBOOK", "WHATSAPP"]

BASE_DIR = "/app/data" if os.path.exists("/app/data") else "."
BAL_FILE = os.path.join(BASE_DIR, "balances.json")
TRAFFIC_FILE = os.path.join(BASE_DIR, "traffic.json")
SUCCESS_FILE = os.path.join(BASE_DIR, "success_traffic.json")
RANGES_FILE = os.path.join(BASE_DIR, "ranges.json")
MAINT_FILE = os.path.join(BASE_DIR, "maintenance.json")
ACTIVE_FILE = os.path.join(BASE_DIR, "active_numbers.json")

if not os.path.exists(RANGES_FILE) and os.path.exists("ranges.json"):
    try:
        os.makedirs(BASE_DIR, exist_ok=True)
        shutil.copy("ranges.json", RANGES_FILE)
    except: pass

ADMIN_ID = 1853202569
GROUP_NAME_TITLE = "APN OTP GROUP"
COMMUNITY_URL = "https://t.me/APNOfficial"
NUMBER_BOT_URL = "https://t.me/APNNUMBERBOT"

FLAGS = {
    "NEPAL": "🇳🇵", "NEPAL_FB": "🇳🇵",
    "CAMEROON": "🇨🇲", "GUINEA": "🇬🇳", "GUNIEA": "🇬🇳",
    "MADAGASCAR": "🇲🇬", "MADAGASCAR_NEW_ACCOUNT": "🇲🇬", "MADAGASCAR_OLD_ACCOUNT": "🇲🇬",
    "MONTENEGRO": "🇲🇪", "UKRAINE": "🇺🇦", "HAITI": "🇭🇹",
    "SIERRA_LEONE": "🇸🇱", "USA": "🇺🇸", "USA_FB": "🇺🇸",
    "MOROCCO": "🇲🇦", "NIGERIA": "🇳🇬", "MOZAMBIQUE": "🇲🇿",
    "ISRAEL": "🇮🇱",
}

# Price per country (sample style)
PRICES = {
    "NEPAL": "0.0055$", "NEPAL_FB": "0.0055$",
    "MOROCCO": "0.0065$", "NIGERIA": "0.0072$",
    "MOZAMBIQUE": "0.0055$", "CAMEROON": "0.0060$",
    "GUINEA": "0.0060$", "MADAGASCAR": "0.0065$",
    "MONTENEGRO": "0.0070$", "UKRAINE": "0.0075$",
    "HAITI": "0.0060$", "SIERRA_LEONE": "0.0060$",
    "USA": "0.0080$", "USA_FB": "0.0080$",
}

def load_json(f, default):
    if os.path.exists(f):
        try:
            with open(f,'r') as fp: return json.load(fp)
        except: return default
    return default

def save_json(f, data):
    os.makedirs(os.path.dirname(f) if os.path.dirname(f) else ".", exist_ok=True)
    with open(f,'w') as fp: json.dump(data, fp, indent=2)

def is_maintenance():
    return load_json(MAINT_FILE, {"enabled": False}).get("enabled", False)

def get_user(uid):
    db = load_json(BAL_FILE, {})
    uid=str(uid)
    if uid not in db:
        db[uid]={"balance":0.0,"requests":[],"total":0,"ref":0}
        save_json(BAL_FILE, db)
    return db[uid]

def add_request(uid, country):
    db = load_json(BAL_FILE, {})
    uid=str(uid)
    if uid not in db: db[uid]={"balance":0.0,"requests":[],"total":0,"ref":0}
    db[uid]["requests"].append(datetime.now().isoformat())
    db[uid]["total"]+=1
    save_json(BAL_FILE, db)
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
    # keep last 20
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
    clean = country_code.upper().replace("_FB","").replace("_WS","").replace("_2","")
    country_name = clean.replace("_", " ").title()
    flag = FLAGS.get(clean, FLAGS.get(clean.split("_")[0], "🌍"))
    service_display = "Facebook" if service.upper() in ["FACEBOOK", "FB"] else "WhatsApp"
    otp_digits = ''.join(filter(str.isdigit, str(otp_code)))
    # UCHIHA style OTP inbox
    text = f"{flag} {country_name}\n📞 `{full_number}`\n💳 Earned: +$0.0055\n💰 Balance: $0.0660\n\n🔑 OTP: `{otp_digits}`"
    keyboard = [[InlineKeyboardButton(f"📋 {otp_digits}", callback_data=f"copy_{otp_digits}")]]
    return text, InlineKeyboardMarkup(keyboard)

def format_for_group(country_code, full_number, service, otp_code):
    clean = country_code.upper().replace("_FB","").replace("_WS","").replace("_2","")
    country_name = clean.replace("_", " ").title()
    flag = FLAGS.get(clean, FLAGS.get(clean.split("_")[0], "🌍"))
    masked = mask_number(full_number)
    otp_digits = ''.join(filter(str.isdigit, str(otp_code)))
    service_display = "TikTok" if service.upper() == "FACEBOOK" else service.title()
    text = f"APN NUMBER BOT\n💳 #{clean} 📱 {service_display}\n\n╭─────────────────╮\n  {masked}  📱 {otp_digits}\n╰─────────────────╯\n\n🗣 Language: #English"
    keyboard = [[InlineKeyboardButton(f"🔓 {otp_digits}", callback_data=f"copy_{otp_digits}")], [InlineKeyboardButton("🧪 Panel", url=COMMUNITY_URL), InlineKeyboardButton("📢 CHANNEL", url=CH1)]]
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
                    await bot.send_message(chat_id=OTP_GROUP_ID, text=text_group, reply_markup=markup_group, parse_mode="Markdown")
                except Exception as e:
                    print(f"[FAIL GROUP] {e}")
                db = load_json(BAL_FILE, {})
                uid=str(user_id)
                if uid in db:
                    db[uid]["balance"]+=0.50
                    save_json(BAL_FILE, db)
                add_success(country_code)
                return
        except Exception as e:
            print(f"[WATCHER ERR] {e}")
    print(f"[TIMEOUT] {number}")

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
    await update.message.reply_text(f"Bot Status: {status}")

async def add_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID:
        await update.message.reply_text(f"❌ Not admin ID: {update.effective_user.id}")
        return
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

async def get_my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Your ID: {update.effective_user.id}")

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Get Number", callback_data="services"), InlineKeyboardButton("🌍 Status", callback_data="live")],
        [InlineKeyboardButton("📊 Active Number", callback_data="active"), InlineKeyboardButton("👨‍💼 Support", callback_data="support")],
        [InlineKeyboardButton("👥 Refer", callback_data="refer"), InlineKeyboardButton("💰 Wallet", callback_data="my_status")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_maintenance() and uid!= ADMIN_ID:
        await update.message.reply_text("🛠 System Under Maintenance")
        return
    get_user(uid)
    if await is_joined(uid, context):
        txt = "✅ Verification Successful!\nWelcome to our platform.\nEnjoy a smooth and secure experience.\n\nMenu:"
        await update.message.reply_text(txt, reply_markup=main_menu_keyboard())
    else:
        txt = "⚠️ Access Denied!\nPlease join our channels to use the bot."
        kb = [
            [InlineKeyboardButton("Join Channel 1", url=CH1)],
            [InlineKeyboardButton("Join Channel 2", url=CH2)],
            [InlineKeyboardButton("Join Channel 3", url=CH3)],
            [InlineKeyboardButton("✅ Verify", callback_data="check")]
        ]
        await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data
    uid = q.from_user.id
    try:
        await q.answer()
    except: pass

    if data.startswith("copy_"):
        otp = data.split("copy_")[1]
        await q.answer(f"📋 OTP {otp} Copied!", show_alert=False)
        return

    if is_maintenance() and uid!= ADMIN_ID:
        await q.edit_message_text("🛠 System Under Maintenance")
        return
    if data!= "check" and not await is_joined(uid, context):
        txt = "⚠️ Access Denied!\nPlease join our channels to use the bot."
        kb = [
            [InlineKeyboardButton("Join Channel 1", url=CH1)],
            [InlineKeyboardButton("Join Channel 2", url=CH2)],
            [InlineKeyboardButton("Join Channel 3", url=CH3)],
            [InlineKeyboardButton("✅ Verify", callback_data="check")]
        ]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data == "check":
        if await is_joined(uid, context):
            txt = "✅ Verification Successful!\nWelcome to our platform.\nEnjoy a smooth and secure experience.\n\nMenu:"
            await q.edit_message_text(txt, reply_markup=main_menu_keyboard())
        else:
            await q.edit_message_text("❌ Not joined yet. Please join all channels and click Verify.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Verify", callback_data="check")]]))
        return

    if data == "main":
        txt = "Menu:"
        await q.edit_message_text(txt, reply_markup=main_menu_keyboard())
        return

    if data == "my_status":
        info = get_user(uid)
        txt = f"💰 Wallet\n\n💳 Balance: ${info['balance']:.4f}\n📞 Total Orders: {info['total']}\n\nEarned: +$0.0055 per OTP"
        kb = [[InlineKeyboardButton("⬅️ Back", callback_data="main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data == "refer":
        txt = f"👥 Refer System\n\n🔗 Your Refer Link:\nhttps://t.me/{context.bot.username}?start={uid}\n\n👥 Total Refer: 0\n💰 Earn: $0.001 per refer"
        kb = [[InlineKeyboardButton("⬅️ Back", callback_data="main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data == "support":
        txt = "☎️ Contact support:"
        kb = [[InlineKeyboardButton("✉️ Contact Admin", url=SUPPORT_ID)], [InlineKeyboardButton("⬅️ Back", callback_data="main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data == "active":
        actives = get_active_numbers(uid)
        if not actives:
            txt = "📊 Active Number\n\nNo active numbers. Get a number first."
            kb = [[InlineKeyboardButton("📱 Get Number", callback_data="services")], [InlineKeyboardButton("⬅️ Back", callback_data="main")]]
            await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
            return
        last = actives[-1]
        flag = FLAGS.get(last['country'].split("_")[0], "🌍")
        txt = f"✅ Active Number\n\n{flag} {last['country'].replace('_FB','').title()}\nPlatform: {last['service']}\nNumber: {last['number']}"
        kb = [
            [InlineKeyboardButton(f"{last['number']}", callback_data=f"copy_{last['number']}")],
            [InlineKeyboardButton("📥 View OTP", url=OTP_GROUP), InlineKeyboardButton("🔄 Change", callback_data=f"c_{last['country']}")],
            [InlineKeyboardButton("🔙 Back", callback_data="main")]
        ]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data == "live":
        req_tr = load_json(TRAFFIC_FILE, {})
        succ_tr = load_json(SUCCESS_FILE, {})
        from datetime import date
        today = date.today().strftime("%-m/%-d/%Y")
        txt = "🔥 LIVE-STOCK STATUS.💥\n\n"
        # Show Paypal 1 style stock
        txt += "💳 Paypal 1\n"
        if succ_tr:
            for c, v in sorted(succ_tr.items(), key=lambda x: x[1], reverse=True)[:10]:
                flag = FLAGS.get(c.split("_")[0], "🌍")
                price = PRICES.get(c.upper(), "0.0065$")
                txt += f"├─ {flag} {c.replace('_FB','').title()} — {price}\n"
        else:
            txt += "├─ 🇲🇦 Morocco — $0.0065\n├─ 🇳🇬 Nigeria — $0.0072\n├─ 🇳🇵 Nepal — $0.0055$\n"
        txt += "────────────────────\n"
        txt += f"📅 Date: {today}\n"
        txt += "────────────────────"
        kb = [[InlineKeyboardButton("⬅️ Back", callback_data="main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data == "services":
        txt = "⚙️ কোন প্ল্যাটফর্মের জন্য নাম্বার নিবেন?"
        kb = []
        for s in SERVICES:
            icon = "💳" if s == "FACEBOOK" else "💬"
            name = "Paypal 1" if s == "FACEBOOK" else "WhatsApp"
            kb.append([InlineKeyboardButton(f"{icon} {name}", callback_data=f"s_{s}")])
        kb.append([InlineKeyboardButton("⬅️ Back", callback_data="main")])
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data.startswith("s_"):
        service = data[2:]
        context.user_data['service'] = service
        countries = get_all_countries(service)
        if not countries and service.upper() == "FACEBOOK":
            countries = ["NEPAL_FB"]
        if not countries:
            await q.edit_message_text(f"❌ No ranges for {service}!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="services")]]))
            return
        # Deduplicate Nepal
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

        platform_name = "Paypal 1" if service.upper() == "FACEBOOK" else service.title()
        txt = f"💳 {platform_name} - দেশ সিলেক্ট করুন:"
        kb = []
        for code in countries_sorted:
            display = get_display_name(code)
            base_key = code.upper().split("_")[0]
            flag = FLAGS.get(code.upper(), FLAGS.get(base_key, "🌍"))
            price = PRICES.get(code.upper(), PRICES.get(base_key, "0.0065$"))
            btn_text = f"{flag} {display} {price}"
            kb.append([InlineKeyboardButton(btn_text, callback_data=f"c_{code}")])
        kb.append([InlineKeyboardButton("⬅️ Back", callback_data="services")])
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data.startswith("c_"):
        country_code = data[2:]
        service = context.user_data.get('service', 'FACEBOOK')
        display = get_display_name(country_code)
        flag = FLAGS.get(country_code.upper(), FLAGS.get(country_code.upper().split("_")[0], "🌍"))
        is_nepal = "NEPAL" in country_code.upper()
        num_count = 3 if is_nepal else 6
        await q.edit_message_text(f"⏳ Fetching {num_count} numbers for {display}...")

        nums = []
        for i in range(num_count):
            try:
                order = await asyncio.to_thread(create_order, service, country_code)
            except Exception as e:
                print(f"[CREATE THREAD ERR] {e}")
                order = None
            if order:
                nums.append(order)
                add_request(uid, display)
                save_active_number(uid, order['number'], country_code, service)
                context.application.create_task(otp_watcher(context.bot, order['id'], uid, order['number'], service, country_code))
                await asyncio.sleep(0.5)

        if not nums:
            await q.edit_message_text(f"❌ Out of Stock! {display}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Try Again", callback_data=f"s_{service}")]]))
            return

        platform_name = "Paypal 1" if service.upper() == "FACEBOOK" else service.title()
        # Fancy header like UCHIHA
        header = f"────────── ⋆⋅☆⋅⋆ ──────────\n{flag} {display} Fresh Number 💸\n📱 {platform_name}\n────────── ⋆⋅☆⋅⋆ ──────────\n\n💫 Wait 5s Or Check The OTP Grup 🖤"
        txt = header + "\n\n"
        kb = []
        for o in nums:
            kb.append([InlineKeyboardButton(f"{o['number']}", callback_data=f"copy_{o['number']}")])
        kb.append([InlineKeyboardButton("📥 View OTP", url=OTP_GROUP)])
        kb.append([InlineKeyboardButton("🔄 Change", callback_data=f"c_{country_code}"), InlineKeyboardButton("🔙 Back", callback_data=f"s_{service}")])
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

from telegram.request import HTTPXRequest
request = HTTPXRequest(connection_pool_size=20, connect_timeout=30, read_timeout=30, write_timeout=30, pool_timeout=30)
app = ApplicationBuilder().token(TOKEN).request(request).build()

async def error_handler(update, context):
    print(f"[BOT ERROR] {context.error}")
    try:
        if "Timed out" in str(context.error) or "ConnectTimeout" in str(context.error):
            return
    except: pass

app.add_error_handler(error_handler)

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("id", get_my_id))
app.add_handler(CommandHandler("add", add_range))
app.add_handler(CommandHandler("del", del_range))
app.add_handler(CommandHandler("list", list_range))
app.add_handler(CommandHandler("off", bot_off))
app.add_handler(CommandHandler("on", bot_on))
app.add_handler(CommandHandler("botstatus", bot_status))
app.add_handler(CallbackQueryHandler(handle))
app.run_polling(drop_pending_updates=True)
