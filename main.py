import os, json
from datetime import datetime, timedelta
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

SERVICES = ["FACEBOOK", "WHATSAPP", "TELEGRAM"]

BAL_FILE = "balances.json"
TRAFFIC_FILE = "traffic.json"

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

async def check_otp_job(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    otp = get_otp(job_data['order_id'])
    if otp:
        try:
            await context.bot.send_message(chat_id=job_data['user_id'], text=f"✅ **OTP Received!**\n\n📞 Number: `{job_data['number']}`\n🔑 OTP: `{otp}`\n🌍 Service: {job_data['service']}", parse_mode="Markdown")
        except: pass
        try:
            await context.bot.send_message(chat_id="@APNOTP", text=f"✅ **OTP SUCCESS**\n📞 `{job_data['number']}`\n🔑 OTP: `{otp}`\nService: {job_data['service']} | {job_data['country']}\nUser: {job_data['user_id']}")
        except: pass
        if job_data['service'] == "FACEBOOK":
            db = load_json(BAL_FILE, {})
            if str(job_data['user_id']) in db:
                db[str(job_data['user_id'])]["balance"] += 0.50/125
                save_json(BAL_FILE, db)
        context.job.schedule_removal()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    info = get_user(uid)
    if await is_joined(uid, context):
        kb = [[InlineKeyboardButton(f"💳 Balance: ${info['balance']:.3f}", callback_data="my_status")],
              [InlineKeyboardButton("📞 GET NUMBER", callback_data="services"), InlineKeyboardButton("💰 WITHDRAWAL", callback_data="withdrawal")],
              [InlineKeyboardButton("📊 LIVE TRAFFIC", callback_data="live"), InlineKeyboardButton("👑 MY STATUS", callback_data="my_status")],
              [InlineKeyboardButton("🆘 SUPPORT", url=SUPPORT_ID)]]
        await update.message.reply_text("👑 **APN NUMBER BOT**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    else:
        kb = [[InlineKeyboardButton("📢 JOIN: APN OFFICIAL", url=CH1)], [InlineKeyboardButton("📢 JOIN: APN BACKUP", url=CH2)], [InlineKeyboardButton("🤖 JOIN: PROXY BOT", url=BOT_LINK)], [InlineKeyboardButton("👥 JOIN: APN OTP GROUP", url=OTP_GROUP)], [InlineKeyboardButton("✅ CHECK JOINED", callback_data="check")]]
        await update.message.reply_text("⚠️ **বট ব্যবহারের পূর্বে চ্যানেলে জয়েন করুন**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    uid = q.from_user.id

    if data!="check" and not await is_joined(uid, context):
        kb = [[InlineKeyboardButton("📢 APN OFFICIAL", url=CH1)], [InlineKeyboardButton("📢 APN BACKUP", url=CH2)], [InlineKeyboardButton("🤖 PROXY BOT", url=BOT_LINK)], [InlineKeyboardButton("👥 APN OTP GROUP", url=OTP_GROUP)], [InlineKeyboardButton("✅ CHECK JOINED", callback_data="check")]]
        await q.edit_message_text("❌ **আপনি চ্যানেল থেকে লিভ নিয়েছেন!**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return

    if data=="check":
        info=get_user(uid)
        if await is_joined(uid, context):
            kb = [[InlineKeyboardButton(f"💳 Balance: ${info['balance']:.3f}", callback_data="my_status")], [InlineKeyboardButton("📞 GET NUMBER", callback_data="services"), InlineKeyboardButton("💰 WITHDRAWAL", callback_data="withdrawal")], [InlineKeyboardButton("📊 LIVE TRAFFIC", callback_data="live"), InlineKeyboardButton("👑 MY STATUS", callback_data="my_status")], [InlineKeyboardButton("🆘 SUPPORT", url=SUPPORT_ID)]]
            await q.edit_message_text("✅ **যাচাইকরণ সফল!**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        else:
            await q.edit_message_text("❌ **এখনো জয়েন করেননি।**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ CHECK JOINED", callback_data="check")]]))
        return

    if data=="main":
        info=get_user(uid)
        kb = [[InlineKeyboardButton(f"💳 Balance: ${info['balance']:.3f}", callback_data="my_status")], [InlineKeyboardButton("📞 GET NUMBER", callback_data="services"), InlineKeyboardButton("💰 WITHDRAWAL", callback_data="withdrawal")], [InlineKeyboardButton("📊 LIVE TRAFFIC", callback_data="live"), InlineKeyboardButton("👑 MY STATUS", callback_data="my_status")], [InlineKeyboardButton("🆘 SUPPORT", url=SUPPORT_ID)]]
        await q.edit_message_text("👑 **APN NUMBER BOT**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data=="my_status":
        db = load_json(BAL_FILE, {})
        user = db.get(str(uid), {"balance":0,"requests":[],"total":0,"ref":0})
        reqs = user.get("requests",[])
        now = datetime.now()
        today = sum(1 for r in reqs if datetime.fromisoformat(r).date()==now.date())
        last7 = sum(1 for r in reqs if datetime.fromisoformat(r) >= now - timedelta(days=7))
        last30 = sum(1 for r in reqs if datetime.fromisoformat(r) >= now - timedelta(days=30))
        taka = user['balance']*125
        txt = f"👑 **MY STATUS**\n🆔 ID: `{uid}`\n💳 Balance: {user['balance']:.3f} $ ({taka:.2f} ৳)\nToday: {today} | 7D: {last7} | 30D: {last30}"
        kb = [[InlineKeyboardButton("❌ CLOSE", callback_data="main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data=="live":
        tr = load_json(TRAFFIC_FILE, {})
        total = sum(tr.values()) if tr else 41
        if not tr: tr = {"MADAGASCAR": 41}
        txt = f"🔴 **Live Traffic**\nResults Sent: {total}\nTop: MADAGASCAR 🇲🇬"
        kb = [[InlineKeyboardButton("🔄 Refresh", callback_data="live")],[InlineKeyboardButton("❌ CLOSE", callback_data="main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data=="withdrawal":
        info=get_user(uid)
        txt = f"💰 **BALANCE:** ${info['balance']:.3f}\nMINIMUM: $0.02"
        kb = [[InlineKeyboardButton("🕊️ Bkash", callback_data="wd_bkash")],[InlineKeyboardButton("❌ Cancel", callback_data="main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data=="services":
        kb = [[InlineKeyboardButton(f"{s}", callback_data=f"s_{s}")] for s in SERVICES]
        kb.append([InlineKeyboardButton("❌ CLOSE", callback_data="main")])
        await q.edit_message_text("🔹 **Please select a service:**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data.startswith("s_"):
        service = data[2:]
        context.user_data['service']=service
        if service == "TELEGRAM":
            await q.edit_message_text(f"**{service} SERVICE**\n\n❌ **Stock Nai!**\nTelegram ekhon stock e nai.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="services")]]), parse_mode="Markdown")
            return
        # Country button - emoji dekhabe kintu callback emoji chara
        countries = get_all_countries()
        kb = []
        for code in countries:
            display = get_display_name(code)
            kb.append([InlineKeyboardButton(display, callback_data=f"c_{code}")])
        kb.append([InlineKeyboardButton("↩️ CHANGE SERVICE", callback_data="services")])
        await q.edit_message_text(f"Service: **{service}**\nDesh select koro:", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data.startswith("c_"):
        country_code = data[2:] # MADAGASCAR
        service = context.user_data.get('service','FACEBOOK')
        display = get_display_name(country_code)
        await q.edit_message_text(f"⏳ **Number nichhi {display} er jonno...**")

        order = create_order(service, country_code)
        if not order:
            await q.edit_message_text(f"❌ **Stock Sesh!**\nRange 26134 e number nai.\nNP panel e check koro.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Try Again", callback_data=f"s_{service}")]]), parse_mode="Markdown")
            return

        num1 = order['number']
        order_id = order['id']
        add_request(uid, display)
        context.job_queue.run_repeating(check_otp_job, interval=5, first=5, last=180, data={"order_id": order_id, "user_id": uid, "number": num1, "service": service, "country": display}, name=f"otp_{order_id}_{uid}")

        kb = [[InlineKeyboardButton(f"📋 {num1}", callback_data=f"copy_{num1}")], [InlineKeyboardButton("🌐 Change Country", callback_data=f"s_{service}")], [InlineKeyboardButton("🔄 Change Number", callback_data=f"c_{country_code}")], [InlineKeyboardButton("🛡️ OTP Group", url=OTP_GROUP)]]
        txt = f"**YOUR {display} {service} NUMBER**\n\n`{num1}`\n\n⏳ **OTP wait korchi...**"
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data.startswith("copy_"):
        num = data[5:]
        await context.bot.send_message(chat_id=uid, text=f"📋 **Copy:**\n\n`{num}`", parse_mode="Markdown")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle))
app.run_polling()
