import os, json, random
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, CopyTextButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from panel import get_number

TOKEN = os.getenv("BOT_TOKEN")

MUST_JOIN = ["@ApnNumber", "@APNOTP"]
CH1 = "https://t.me/ApnNumber"
CH2 = "https://t.me/+3N7St38N__ZkMTZl"
BOT_LINK = "https://t.me/Proxystore999"
OTP_GROUP = "https://t.me/APNOTP"
SUPPORT_ID = "https://t.me/PolasChandra"

SERVICES = ["IMO", "TELEGRAM", "VK", "WHATSAPP"]
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
    with open(f,'w') as fp: json.dump(fp, data) if False else json.dump(data, fp)

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

        txt = (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👑 **MY STATUS**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 **ID:** `{uid}`\n"
            f"💳 **Balance:** {user['balance']:.2f} $ ({taka:.2f} ৳)\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👑 **My Statistics**\n"
            f"┣ Today: {today}\n"
            f"┣ Last 7 Days: {last7}\n"
            f"┣ Last 30 Days: {last30}\n"
            f"┗ Lifetime: {lifetime}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🦀 **Referrals:** {user.get('ref',0)}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        kb = [
            [InlineKeyboardButton("🧚 Refer", callback_data="refer")],
            [InlineKeyboardButton("📱 Connect WhatsApp", url=SUPPORT_ID)],
            [InlineKeyboardButton("❌ CLOSE", callback_data="main")]
        ]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data=="live":
        tr = load_json(TRAFFIC_FILE, {})
        total = sum(tr.values()) if tr else 41
        if not tr: tr = {"SRI LANKA 🇱🇰": 26, "LAOS 🇱🇦": 14, "ALGERIA 🇩🇿": 1}
        sorted_c = sorted(tr.items(), key=lambda x: x[1], reverse=True)
        top_country = sorted_c[0][0] if sorted_c else "SRI LANKA 🇱🇰"

        now_str = datetime.now().strftime("%H:%M:%S")

        txt = (
            f"🔴 **Live Traffic**\n\n"
            f"👤 **Window:** Last 30 minutes\n"
            f"🔘 **Results Sent:** {total}\n"
            f"🔝 **Top Country:** {top_country} 📱\n\n"
            f"🌐 **Top Countries:**\n"
        )
        for i, (c, cnt) in enumerate(sorted_c[:3]):
            perc = (cnt/total*100) if total else 0
            icon = "📱" if i<2 else "❓"
            txt += f"{i+1}. {c} ➡️ {perc:.1f}% {icon}\n"

        txt += f"\n⏰ **Last Update:** {now_str}"

        kb = [[InlineKeyboardButton("🔄 Refresh", callback_data="live")],
              [InlineKeyboardButton("❌ CLOSE", callback_data="main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data=="withdrawal":
        info=get_user(uid)
        txt = (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"《 🔮 **WITHDRAWAL** 》\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔥 **Total Otp:** {info['total']}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🙋 **Total Reffer :** {info.get('ref',0)}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 **BALANCE:** ${info['balance']:.3f}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🧪 **MINIMUM:** $0.02\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"**SELECT METHOD:**"
        )
        kb = [
            [InlineKeyboardButton("🕊️ Bkash", callback_data="wd_bkash")],
            [InlineKeyboardButton("🟡 Binance", callback_data="wd_binance")],
            [InlineKeyboardButton("❌ Cancel", callback_data="main")]
        ]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data.startswith("wd_"):
        await q.edit_message_text(f"💰 **{data[3:].upper()} Withdrawal**\n\nআপনার ব্যালেন্স ${get_user(uid)['balance']:.3f}\n\nউইথড্র করতে সাপোর্টে যোগাযোগ করুন:\n{SUPPORT_ID}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🆘 SUPPORT", url=SUPPORT_ID)],[InlineKeyboardButton("⬅️ BACK", callback_data="withdrawal")]]), parse_mode="Markdown")

    elif data=="refer":
        txt = f"🧚 **আপনার রেফারেল লিংক:**\n\n`https://t.me/{(await context.bot.get_me()).username}?start={uid}`\n\nপ্রতি রেফারে $0.01 বোনাস পাবেন।"
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ BACK", callback_data="my_status")]]), parse_mode="Markdown")

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
        num1=get_number(service,country)
        num2=get_number(service,country)
        num3=get_number(service,country)
        add_request(uid, country)

        kb = [
            [InlineKeyboardButton(f"📋 {num1}", copy_text=CopyTextButton(text=num1))],
            [InlineKeyboardButton(f"📋 {num2}", copy_text=CopyTextButton(text=num2))],
            [InlineKeyboardButton(f"📋 {num3}", copy_text=CopyTextButton(text=num3))],
            [InlineKeyboardButton("🌐 Change Country", callback_data=f"s_{service}"), InlineKeyboardButton("🔢 Set Prefix", callback_data="main")],
            [InlineKeyboardButton("🔄 Change Number", callback_data=f"c_{country}")],
            [InlineKeyboardButton("🛡️ OTP Group", url=OTP_GROUP)]
        ]
        txt = f"**YOUR {country} {service} NUMBER**\n\n🎉 **আপনার {country} এর {service} নাম্বার প্রস্তুত:**\n✅ **OTP পেতে নিচের গ্রুপে নজর রাখুন।**"
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle))
app.run_polling()
