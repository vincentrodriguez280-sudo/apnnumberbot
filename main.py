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
SUPPORT_ID = "https://t.me/PolasChandra"
SERVICES = ["FACEBOOK", "WHATSAPP"]
BAL_FILE = "balances.json"
TRAFFIC_FILE = "traffic.json"
ADMIN_ID = 8166317954

def load_json(f, default):
    if os.path.exists(f):
        try:
            with open(f,'r') as fp: return json.load(fp)
        except: return default
    return default

def save_json(f, data):
    with open(f,'w') as fp: json.dump(data, fp)

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

async def is_joined(user_id, context):
    for ch in MUST_JOIN:
        try:
            m = await context.bot.get_chat_member(chat_id=ch, user_id=user_id)
            if m.status in ['left','kicked']: return False
        except: return False
    return True

async def otp_watcher(bot, order_id, user_id, number, service, country):
    for _ in range(40):
        await asyncio.sleep(5)
        otp = await asyncio.to_thread(get_otp, order_id)
        if otp:
            try:
                await bot.send_message(chat_id=user_id, text=f"✅ **OTP Received!**\n\n📞 Number: `{number}`\n🔑 OTP: `{otp}`\n🌍 Service: {service}", parse_mode="Markdown")
            except: pass
            try:
                await bot.send_message(chat_id="@APNOTP", text=f"✅ **OTP SUCCESS**\n📞 `{number}`\n🔑 OTP: `{otp}`\nService: {service} | {country}\nUser: {user_id}")
            except: pass
            try:
                await bot.send_message(chat_id="@ApnNumber", text=f"📞 `{number}`\n🔑 OTP: `{otp}`\nService: {service}")
            except: pass
            db = load_json(BAL_FILE, {})
            uid=str(user_id)
            if uid in db:
                db[uid]["balance"]+=0.50
                save_json(BAL_FILE, db)
            return

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
        await update.message.reply_text("👑 **APN NUMBER BOT**\n\nProfessional OTP Service", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
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
        txt = f"👑 **MY STATUS**\n\n💳 Balance: ${info['balance']:.3f}\n📞 Total Number: {info['total']}\n\nPer OTP 0.50 BDT"
        kb = [[InlineKeyboardButton("💰 WITHDRAWAL", callback_data="withdrawal")], [InlineKeyboardButton("🔙 BACK", callback_data="main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return

    if data == "withdrawal":
        info = get_user(uid)
        txt = f"💰 **WITHDRAWAL**\n\n💳 Balance: ${info['balance']:.3f}\n\nMinimum Withdraw 10 BDT\n\nWithdraw er jonno SUPPORT e message din"
        kb = [[InlineKeyboardButton("🆘 SUPPORT", url=SUPPORT_ID)], [InlineKeyboardButton("🔙 BACK", callback_data="main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return

    if data == "live":
        tr = load_json(TRAFFIC_FILE, {})
        txt = "📊 **LIVE TRAFFIC**\n\n"
        if not tr: txt+="No traffic yet"
        else:
            for c, v in sorted(tr.items(), key=lambda x: x[1], reverse=True)[:20]:
                txt+=f"{c}: {v} requests\n"
        kb = [[InlineKeyboardButton("🔙 BACK", callback_data="main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return

    if data == "admin":
        if uid!= ADMIN_ID: return
        db = load_json(BAL_FILE, {})
        total_users = len(db)
        total_req = sum([v['total'] for v in db.values()])
        txt = f"👑 **ADMIN PANEL**\n\n👥 Total Users: {total_users}\n📞 Total Requests: {total_req}"
        kb = [[InlineKeyboardButton("🔙 BACK", callback_data="main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return

    if data == "services":
        kb = [[InlineKeyboardButton(f"{s}", callback_data=f"s_{s}")] for s in SERVICES]
        kb.append([InlineKeyboardButton("❌ CLOSE", callback_data="main")])
        await q.edit_message_text("🔹 **Please select a service:**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return

    if data.startswith("s_"):
        service = data[2:]
        context.user_data['service'] = service
        # FIXED: service onujayi country list
        countries = get_all_countries(service)
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
                asyncio.create_task(otp_watcher(context.bot, order['id'], uid, order['number'], service, display))
                await asyncio.sleep(1)
        if not nums:
            await q.edit_message_text(f"❌ **Stock Sesh! {display}**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Try Again", callback_data=f"s_{service}")]]))
            return
        kb = [[InlineKeyboardButton("🌐 Change Country", callback_data=f"s_{service}")],
              [InlineKeyboardButton("🔄 Change Number (3 New)", callback_data=f"c_{country_code}")],
              [InlineKeyboardButton("🛡 OTP Group", url=OTP_GROUP)]]
        txt = f"**YOUR {display} {service} 3 NUMBER**\n\n"
        for o in nums:
            txt += f"`{o['number']}`\n"
        txt += f"\n⏳ **OTP auto asbe. OTP Group e o post hobe.**"
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle))
app.run_polling(drop_pending_updates=True)
