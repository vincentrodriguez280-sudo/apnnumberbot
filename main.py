import os, json, asyncio
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from panel import create_order, get_otp, get_all_countries, get_display_name

TOKEN = os.getenv("BOT_TOKEN")
MUST_JOIN = ["@ApnNumber", "@APNOTP"]
CH1 = "https://t.me/ApnNumber"
CH2 = "https://t.me/+3N7St38N__ZkMTZl"
BOT_LINK = "https://t.me/Proxystore999"
OTP_GROUP = "https://t.me/APNOTP"
OTP_GROUP_ID = "@APNOTP"
CHANNEL_ID = "@ApnNumber"
SUPPORT_ID = "https://t.me/PolasChandra"
SERVICES = ["FACEBOOK", "WHATSAPP"]
BAL_FILE = "balances.json"
TRAFFIC_FILE = "traffic.json"
SUCCESS_FILE = "success_traffic.json"
RANGES_FILE = "ranges.json"
ADMIN_ID = 8166317954

# ===== YOUR NEW DESIGN SETTINGS =====
GROUP_NAME_TITLE = "APN OTP GROUP"
COMMUNITY_URL = "https://t.me/APNOTP"
NUMBER_BOT_URL = "https://t.me/APNNUMBERBOT"
FLAGS = {
    "NEPAL": "🇳🇵", "MADAGASCAR": "🇲🇬", "HAITI": "🇭🇹",
    "MONTENEGRO": "🇲🇪", "SIERRA_LEONE": "🇸🇱", "SIERRA_LEONE_2": "🇸🇱",
    "USA": "🇺🇸", "INDONESIA": "🇮🇩", "MYANMAR": "🇲🇲"
}

def load_json(f, default):
    if os.path.exists(f):
        try:
            with open(f,'r') as fp: return json.load(fp)
        except: return default
    return default

def save_json(f, data):
    with open(f,'w') as fp: json.dump(data, fp, indent=2)

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

def mask_number(num):
    n = num.replace(" ", "").replace("+", "").strip()
    if len(n) <= 6:
        return "+" + n
    # +5093XXXXXX224 style
    return f"+{n[:4]}XXXXXX{n[-3:]}"

def format_rocket_style(country_code, full_number, service, otp_code):
    clean = country_code.upper().replace("_FB","").replace("_WS","").replace("_2","")
    country_name = clean.replace("_", " ").title()
    flag = FLAGS.get(clean, "🌍")
    masked = mask_number(full_number)
    service_display = "Facebook" if service.upper() in ["FACEBOOK", "FB"] else "WhatsApp"
    # OTP 333069 -> 333-069
    if len(otp_code) >= 6 and "-" not in otp_code:
        otp_show = f"{otp_code[:3]}-{otp_code[3:]}"
    else:
        otp_show = otp_code

    text = (
        f"{GROUP_NAME_TITLE}\n"
        f"🎉 NEW OTP RECEIVED 🎉\n\n"
        f"🌍 Country: {country_name} {flag}\n"
        f"📱 Number: {masked}\n"
        f"🧰 Service: {service_display}\n"
        f"🔍 OTP: {otp_show}"
    )
    keyboard = [[
        InlineKeyboardButton("🚀 Community", url=COMMUNITY_URL),
        InlineKeyboardButton("📱 Number", url=NUMBER_BOT_URL)
    ]]
    return text, InlineKeyboardMarkup(keyboard)

async def is_joined(user_id, context):
    for ch in MUST_JOIN:
        try:
            m = await context.bot.get_chat_member(chat_id=ch, user_id=user_id)
            if m.status in ['left','kicked']: return False
        except: return False
    return True

async def otp_watcher(bot, order_id, user_id, number, service, country_code):
    for _ in range(50):
        await asyncio.sleep(5)
        otp = await asyncio.to_thread(get_otp, order_id)
        if otp:
            text, markup = format_rocket_style(country_code, number, service, otp)
            # 1. User inbox e
            try: await bot.send_message(chat_id=user_id, text=text, reply_markup=markup)
            except: pass
            # 2. OTP Group e same design
            try: await bot.send_message(chat_id=OTP_GROUP_ID, text=text, reply_markup=markup)
            except: pass
            # 3. Channel e optional
            try: await bot.send_message(chat_id=CHANNEL_ID, text=text, reply_markup=markup)
            except: pass

            db = load_json(BAL_FILE, {})
            uid=str(user_id)
            if uid in db:
                db[uid]["balance"]+=0.50
                save_json(BAL_FILE, db)
            add_success(country_code)
            return

# --- ADMIN EASY RANGE SYSTEM ---
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
        await update.message.reply_text(f"✅ Added!\n\nService: {service}\nName: {name}\nRange: {rid}")
    except:
        await update.message.reply_text("❌ Use:\n`/add FB MONTENEGRO 38267437402`")

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
            await update.message.reply_text("❌ Range not found")
    except:
        await update.message.reply_text("❌ Use: `/del FB MONTENEGRO`")

async def list_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    data = load_json(RANGES_FILE, {"FACEBOOK":{}, "WHATSAPP":{}})
    txt = "📋 **Current Ranges:**\n\n"
    for srv, ranges in data.items():
        txt += f"**{srv}:**\n"
        for n, r in ranges.items():
            txt += f"• {n} = {r}\n"
        txt += "\n"
    await update.message.reply_text(txt, parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    info = get_user(uid)
    if await is_joined(uid, context):
        kb = [[InlineKeyboardButton(f"💳 Balance: ${info['balance']:.3f}", callback_data="my_status")],
              [InlineKeyboardButton("📞 GET NUMBER", callback_data="services"), InlineKeyboardButton("💰 WITHDRAWAL", callback_data="withdrawal")],
              [InlineKeyboardButton("📊 LIVE TRAFFIC", callback_data="live"), InlineKeyboardButton("👑 MY STATUS", callback_data="my_status")],
              [InlineKeyboardButton("🆘 SUPPORT", url=SUPPORT_ID)]]
        if uid == ADMIN_ID:
            kb.append([InlineKeyboardButton("👑 ADMIN PANEL", callback_data="admin")])
        await update.message.reply_text("👑 **APN NUMBER BOT**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    else:
        kb = [[InlineKeyboardButton("📢 JOIN: APN OFFICIAL", url=CH1)], [InlineKeyboardButton("📢 JOIN: APN BACKUP", url=CH2)], [InlineKeyboardButton("🤖 JOIN: PROXY BOT", url=BOT_LINK)], [InlineKeyboardButton("👥 JOIN: APN OTP GROUP", url=OTP_GROUP)], [InlineKeyboardButton("✅ CHECK JOINED", callback_data="check")]]
        await update.message.reply_text("⚠ **Bot use korar age channel e join korun**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    uid = q.from_user.id
    if data!= "check" and not await is_joined(uid, context):
        kb = [[InlineKeyboardButton("📢 APN OFFICIAL", url=CH1)], [InlineKeyboardButton("📢 APN BACKUP", url=CH2)], [InlineKeyboardButton("🤖 PROXY BOT", url=BOT_LINK)], [InlineKeyboardButton("👥 APN OTP GROUP", url=OTP_GROUP)], [InlineKeyboardButton("✅ CHECK JOINED", callback_data="check")]]
        await q.edit_message_text("❌ **Channel e join koren ni!**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return
    if data == "check":
        info = get_user(uid)
        if await is_joined(uid, context):
            kb = [[InlineKeyboardButton(f"💳 Balance: ${info['balance']:.3f}", callback_data="my_status")], [InlineKeyboardButton("📞 GET NUMBER", callback_data="services"), InlineKeyboardButton("💰 WITHDRAWAL", callback_data="withdrawal")], [InlineKeyboardButton("📊 LIVE TRAFFIC", callback_data="live"), InlineKeyboardButton("👑 MY STATUS", callback_data="my_status")], [InlineKeyboardButton("🆘 SUPPORT", url=SUPPORT_ID)]]
            if uid == ADMIN_ID: kb.append([InlineKeyboardButton("👑 ADMIN PANEL", callback_data="admin")])
            await q.edit_message_text("✅ **Verification Successful!**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        else:
            await q.edit_message_text("❌ **Join hoy ni.**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ CHECK JOINED", callback_data="check")]]))
        return
    if data == "main":
        info = get_user(uid)
        kb = [[InlineKeyboardButton(f"💳 Balance: ${info['balance']:.3f}", callback_data="my_status")], [InlineKeyboardButton("📞 GET NUMBER", callback_data="services"), InlineKeyboardButton("💰 WITHDRAWAL", callback_data="withdrawal")], [InlineKeyboardButton("📊 LIVE TRAFFIC", callback_data="live"), InlineKeyboardButton("👑 MY STATUS", callback_data="my_status")], [InlineKeyboardButton("🆘 SUPPORT", url=SUPPORT_ID)]]
        if uid == ADMIN_ID: kb.append([InlineKeyboardButton("👑 ADMIN PANEL", callback_data="admin")])
        await q.edit_message_text("👑 **APN NUMBER BOT**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return
    if data == "my_status":
        info = get_user(uid)
        txt = f"👑 **MY STATUS**\n\n💳 Balance: ${info['balance']:.3f}\n📞 Total: {info['total']}"
        kb = [[InlineKeyboardButton("💰 WITHDRAWAL", callback_data="withdrawal")], [InlineKeyboardButton("🔙 BACK", callback_data="main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return
    if data == "withdrawal":
        info = get_user(uid)
        txt = f"💰 **WITHDRAWAL**\n\n💳 Balance: ${info['balance']:.3f}\n\nMin 10 BDT"
        kb = [[InlineKeyboardButton("🆘 SUPPORT", url=SUPPORT_ID)], [InlineKeyboardButton("🔙 BACK", callback_data="main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return
    if data == "live":
        req_tr = load_json(TRAFFIC_FILE, {})
        succ_tr = load_json(SUCCESS_FILE, {})
        txt = "📊 **LIVE TRAFFIC - OTP REPORT**\n\n🔥 **OTP besi asche:**\n"
        if not succ_tr: txt += "No OTP yet\n\n"
        else:
            for c, v in sorted(succ_tr.items(), key=lambda x: x[1], reverse=True)[:15]:
                txt+=f"✅ {c}: {v} OTP\n"
        txt += "\n📞 **Total Request:**\n"
        for c, v in sorted(req_tr.items(), key=lambda x: x[1], reverse=True)[:10]:
            txt+=f"📞 {c}: {v}\n"
        kb = [[InlineKeyboardButton("🔙 BACK", callback_data="main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return
    if data == "admin":
        if uid!= ADMIN_ID: return
        db = load_json(BAL_FILE, {})
        succ = load_json(SUCCESS_FILE, {})
        txt = f"👑 **ADMIN PANEL**\n\n👥 Users: {len(db)}\n✅ Success OTP: {sum(succ.values())}\n\n**Commands:**\n/add FB NAME RANGE\n/del FB NAME\n/list"
        kb = [[InlineKeyboardButton("🔙 BACK", callback_data="main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return
    if data == "services":
        kb = [[InlineKeyboardButton(f"{s}", callback_data=f"s_{s}")] for s in SERVICES]
        kb.append([InlineKeyboardButton("❌ CLOSE", callback_data="main")])
        await q.edit_message_text("🔹 **Select service:**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return
    if data.startswith("s_"):
        service = data[2:]
        context.user_data['service'] = service
        countries = get_all_countries(service)
        if not countries:
            await q.edit_message_text(f"❌ **{service} te kono range nai! /add diye add korun**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="services")]]))
            return
        kb = []
        for code in countries:
            display = get_display_name(code)
            kb.append([InlineKeyboardButton(display, callback_data=f"c_{code}")])
        kb.append([InlineKeyboardButton("↩ CHANGE SERVICE", callback_data="services")])
        await q.edit_message_text(f"Service: **{service}**\nCountry select korun:", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return
    if data.startswith("c_"):
        country_code = data[2:]
        service = context.user_data.get('service', 'FACEBOOK')
        display = get_display_name(country_code)
        await q.edit_message_text(f"⏳ **{display} er jonno 3 ta number nicchi...**")
        nums = []
        for i in range(3):
            order = await asyncio.to_thread(create_order, service, country_code)
            if order:
                nums.append(order)
                add_request(uid, display)
                asyncio.create_task(otp_watcher(context.bot, order['id'], uid, order['number'], service, country_code))
                await asyncio.sleep(1)
        if not nums:
            await q.edit_message_text(f"❌ **Stock Sesh! {display}**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Try Again", callback_data=f"s_{service}")]]))
            return
        kb = [[InlineKeyboardButton("🌐 Change Country", callback_data=f"s_{service}")],
              [InlineKeyboardButton("🔄 Change Number", callback_data=f"c_{country_code}")],
              [InlineKeyboardButton("🛡 OTP Group", url=OTP_GROUP)]]
        txt = f"**YOUR {display} {service} 3 NUMBER**\n\n"
        for o in nums:
            txt += f"`{o['number']}`\n"
        txt += f"\n⏳ **OTP auto asbe Inbox + Group e.**"
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("add", add_range))
app.add_handler(CommandHandler("del", del_range))
app.add_handler(CommandHandler("list", list_range))
app.add_handler(CallbackQueryHandler(handle))
app.run_polling(drop_pending_updates=True)
