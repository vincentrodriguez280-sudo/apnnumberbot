import os, json
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from panel import get_number, get_otp, create_order

TOKEN = os.getenv("BOT_TOKEN")
MUST_JOIN = ["@ApnNumber", "@APNOTP"]
CH1 = "https://t.me/ApnNumber"
CH2 = "https://t.me/+3N7St38N__ZkMTZl"
BOT_LINK = "https://t.me/Proxystore999"
OTP_GROUP = "https://t.me/APNOTP"
SUPPORT_ID = "https://t.me/PolasChandra"

SERVICES = ["FACEBOOK", "IMO", "TELEGRAM", "VK", "WHATSAPP"]
COUNTRIES = ["TUNISIA 🇹🇳", "HAITI 🇭🇹", "ITALY 🇮🇹", "MALAYSIA 🇲🇾", "MOROCCO 🇲🇦", "MYANMAR 🇲🇲", "NIGERIA 🇳🇬", "SRI LANKA 🇱🇰", "LAOS 🇱🇦", "ALGERIA 🇩🇿"]

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
    order_id = job_data['order_id']
    user_id = job_data['user_id']
    number = job_data['number']
    service = job_data['service']
    country = job_data['country']
    otp = get_otp(order_id)
    if otp:
        try:
            await context.bot.send_message(chat_id=user_id, text=f"✅ **OTP Received!**\n\n📞 Number: `{number}`\n🔑 OTP: `{otp}`\nService: {service}", parse_mode="Markdown")
        except: pass
        try:
            await context.bot.send_message(chat_id="@APNOTP", text=f"✅ **OTP SUCCESS**\n📞 `{number}`\n🔑 OTP: `{otp}`\nService: {service} | {country}\nUser: {user_id}", parse_mode="Markdown")
        except: pass
        if service.upper() == "FACEBOOK":
            db = load_json(BAL_FILE, {})
            reward_bdt = 0.50
            reward_usd = reward_bdt / 125
            if str(user_id) in db:
                db[str(user_id)]["balance"] += reward_usd
                save_json(BAL_FILE, db)
                try:
                    await context.bot.send_message(chat_id=user_id, text=f"💰 **Reward Added!**\nFacebook OTP er jonno **{reward_bdt} BDT** peyechen!", parse_mode="Markdown")
                except: pass
        return False
    return True

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
        kb = [[InlineKeyboardButton("📢 JOIN: APN OFFICIAL", url=CH1)],
              [InlineKeyboardButton("📢 JOIN: APN BACKUP", url=CH2)],
              [InlineKeyboardButton("🤖 JOIN: PROXY BOT", url=BOT_LINK)],
              [InlineKeyboardButton("👥 JOIN: APN OTP GROUP", url=OTP_GROUP)],
              [InlineKeyboardButton("✅ CHECK JOINED", callback_data="check")]]
        await update.message.reply_text("⚠️ **বট ব্যবহারের পূর্বে চ্যানেলে জয়েন করুন**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    uid = q.from_user.id
    if data!="check" and not await is_joined(uid, context):
        kb = [[InlineKeyboardButton("📢 JOIN: APN OFFICIAL", url=CH1)],
              [InlineKeyboardButton("📢 JOIN: APN BACKUP", url=CH2)],
              [InlineKeyboardButton("🤖 JOIN: PROXY BOT", url=BOT_LINK)],
              [InlineKeyboardButton("👥 JOIN: APN OTP GROUP", url=OTP_GROUP)],
              [InlineKeyboardButton("✅ CHECK JOINED", callback_data="check")]]
        await q.edit_message_text("❌ **আপনি চ্যানেল থেকে লিভ নিয়েছেন!**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return
    if data=="check":
        info=get_user(uid)
        if await is_joined(uid, context):
            kb = [[InlineKeyboardButton(f"💳 Balance: ${info['balance']:.3f}", callback_data="my_status")],
                  [InlineKeyboardButton("📞 GET NUMBER", callback_data="services"), InlineKeyboardButton("💰 WITHDRAWAL", callback_data="withdrawal")],
                  [InlineKeyboardButton("📊 LIVE TRAFFIC", callback_data="live"), InlineKeyboardButton("👑 MY STATUS", callback_data="my_status")],
                  [InlineKeyboardButton("🆘 SUPPORT", url=SUPPORT_ID)]]
            await q.edit_message_text("✅ **যাচাইকরণ সফল!**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        else:
            kb = [[InlineKeyboardButton("📢 JOIN: APN OFFICIAL", url=CH1)],
                  [InlineKeyboardButton("📢 JOIN: APN BACKUP", url=CH2)],
                  [InlineKeyboardButton("🤖 JOIN: PROXY BOT", url=BOT_LINK)],
                  [InlineKeyboardButton("👥 JOIN: APN OTP GROUP", url=OTP_GROUP)],
                  [InlineKeyboardButton("✅ CHECK JOINED", callback_data="check")]]
            await q.edit_message_text("❌ **এখনো জয়েন করেননি।**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return
    if data=="main":
        info=get_user(uid)
        kb = [[InlineKeyboardButton(f"💳 Balance: ${info['balance']:.3f}", callback_data="my_status")],
              [InlineKeyboardButton("📞 GET NUMBER", callback_data="services"), InlineKeyboardButton("💰 WITHDRAWAL", callback_data="withdrawal")],
              [InlineKeyboardButton("📊 LIVE TRAFFIC", callback_data="live"), InlineKeyboardButton("👑 MY STATUS", callback_data="my_status")],
              [InlineKeyboardButton("🆘 SUPPORT", url=SUPPORT_ID)]]
        await q.edit_message_text("👑 **APN NUMBER BOT**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    elif data=="my_status":
        db = load_json(BAL_FILE, {})
        user = db.get(str(uid), {"balance":0,"requests":[],"total":0,"ref":0})
        reqs = user.get("requests",[])
        now = datetime.now()
        today = sum(1 for r in reqs if datetime.fromisoformat(r).date()==now.date())
        last7 = sum(1 for r in reqs if datetime.fromisoformat(r) >= now - timedelta(days=7))
        last30 = sum(1 for r in reqs if datetime.fromisoformat(r) >= now - timedelta(days=30))
        lifetime = len(reqs)
        taka = user['balance']*125
        txt = f"━━━━━━━━━━━━━━━━━━━━\n👑 **MY STATUS**\n━━━━━━━━━━━━━━━━━━━━\n🆔 **ID:** `{uid}`\n💳 **Balance:** {user['balance']:.3f} $ ({taka:.2f} ৳)\n━━━━━━━━━━━━━━━━━━━━\n👑 **My Statistics**\n┣ Today: {today}\n┣ Last 7 Days: {last7}\n┣ Last 30 Days: {last30}\n┗ Lifetime: {lifetime}\n━━━━━━━━━━━━━━━━━━━━\n🦀 **Referrals:** {user.get('ref',0)}\n━━━━━━━━━━━━━━━━━━━━"
        kb = [[InlineKeyboardButton("🧚 Refer", callback_data="refer")],[InlineKeyboardButton("📱 Connect WhatsApp", url=SUPPORT_ID)],[InlineKeyboardButton("❌ CLOSE", callback_data="main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    elif data=="live":
        tr = load_json(TRAFFIC_FILE, {})
        total = sum(tr.values()) if tr else 41
        if not tr: tr = {"SRI LANKA 🇱🇰": 26, "LAOS 🇱🇦": 14, "ALGERIA 🇩🇿": 1}
        sorted_c = sorted(tr.items(), key=lambda x: x[1], reverse=True)
        now_str = datetime.now().strftime("%H:%M:%S")
        txt = f"🔴 **Live Traffic**\n\n👤 **Window:** Last 30 minutes\n🔘 **Results Sent:** {total}\n🔝 **Top Country:** {sorted_c[0][0]} 📱\n\n🌐 **Top Countries:**\n"
        for i, (c, cnt) in enumerate(sorted_c[:3]):
            perc = (cnt/total*100) if total else 0
            icon = "📱" if i<2 else "❓"
            txt += f"{i+1}. {c} ➡️ {perc:.1f}% {icon}\n"
        txt += f"\n⏰ **Last Update:** {now_str}"
        kb = [[InlineKeyboardButton("🔄 Refresh", callback_data="live")],[InlineKeyboardButton("❌ CLOSE", callback_data="main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    elif data=="withdrawal":
        info=get_user(uid)
        txt = f"━━━━━━━━━━━━━━━━━━━━\n《 🔮 **WITHDRAWAL** 》\n━━━━━━━━━━━━━━━━━━━━\n🔥 **Total Otp:** {info['total']}\n━━━━━━━━━━━━━━━━━━━━\n🙋 **Total Reffer :** {info.get('ref',0)}\n━━━━━━━━━━━━━━━━━━━━\n💰 **BALANCE:** ${info['balance']:.3f}\n━━━━━━━━━━━━━━━━━━━━\n🧪 **MINIMUM:** $0.02\n━━━━━━━━━━━━━━━━━━━━\n**SELECT METHOD:**"
        kb = [[InlineKeyboardButton("🕊️ Bkash", callback_data="wd_bkash")],[InlineKeyboardButton("🟡 Binance", callback_data="wd_binance")],[InlineKeyboardButton("❌ Cancel", callback_data="main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    elif data=="services":
        kb = [[InlineKeyboardButton(f"{s}", callback_data=f"s_{s}")] for s in SERVICES]
        kb.append([InlineKeyboardButton("❌ CLOSE", callback_data="main")])
        await q.edit_message_text("🔹 **Please select a service:**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    elif data.startswith("s_"):
        context.user_data['service']=data[2:]
        kb=[]; row=[]
        for c in COUNTRIES:
            row.append(InlineKeyboardButton(c, callback_data=f"c_{c}"))
            if len(row)==2: kb.append(row); row=[]
        if row: kb.append(row)
        kb.append([InlineKeyboardButton("↩️ CHANGE SERVICE", callback_data="services")])
        await q.edit_message_text(f"Service: **{context.user_data['service']}**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    elif data.startswith("c_"):
        country=data[2:]
        service=context.user_data.get('service','TELEGRAM')
        order = create_order(service, country)
        if not order:
            await q.edit_message_text("❌ Stock sesh!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Change Country", callback_data=f"s_{service}")]]))
            return
        num1 = order['number']
        order_id = order['id']
        add_request(uid, country)
        context.job_queue.run_repeating(check_otp_job, interval=5, first=5, last=120, data={"order_id": order_id, "user_id": uid, "number": num1, "service": service, "country": country}, name=f"otp_{order_id}")
        # Copy er jonno button e number, click korle alada message e copyable code hisebe pathabe
        kb = [
            [InlineKeyboardButton(f"📋 {num1} - Tap to Copy", callback_data=f"copy_{num1}")],
            [InlineKeyboardButton("🌐 Change Country", callback_data=f"s_{service}"), InlineKeyboardButton("🔢 Set Prefix", callback_data="main")],
            [InlineKeyboardButton("🔄 Change Number", callback_data=f"c_{country}")],
            [InlineKeyboardButton("🛡️ OTP Group", url=OTP_GROUP)]
        ]
        txt = f"**YOUR {country} {service} NUMBER**\n\n🎉 **আপনার {country} এর {service} নাম্বার প্রস্তুত:**\n\n`{num1}`\n\n⏳ **OTP er jonno opekkha korchi...**\n💡 Facebook hole per OTP **0.50 BDT** paben."
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    elif data.startswith("copy_"):
        num = data[5:]
        await q.answer()
        await context.bot.send_message(chat_id=uid, text=f"📋 **Copy this number:**\n\n`{num}`\n\nTap and hold to copy.", parse_mode="Markdown")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle))
app.run_polling()
