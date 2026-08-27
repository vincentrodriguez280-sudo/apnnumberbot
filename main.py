import os, json
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
COUNTRIES = ["TUNISIA 🇹🇳", "HAITI 🇭🇹", "ITALY 🇮🇹", "MALAYSIA 🇲🇾", "MOROCCO 🇲🇦", "MYANMAR 🇲🇲", "NIGERIA 🇳🇬", "UKRAINE 🇺🇦"]

# --- BALANCE SYSTEM ---
BAL_FILE = "balances.json"
def load_bal():
    if os.path.exists(BAL_FILE):
        try:
            with open(BAL_FILE, 'r') as f: return json.load(f)
        except: return {}
    return {}
def save_bal(data):
    with open(BAL_FILE, 'w') as f: json.dump(data, f)
def get_user_info(uid):
    db = load_bal()
    uid = str(uid)
    if uid not in db:
        db[uid] = {"balance": 0.0, "numbers": 0, "ref": 0}
        save_bal(db)
    return db[uid]

async def is_joined(user_id, context):
    for ch in MUST_JOIN:
        try:
            m = await context.bot.get_chat_member(chat_id=ch, user_id=user_id)
            if m.status in ['left', 'kicked']: return False
        except: return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    info = get_user_info(uid)
    if await is_joined(uid, context):
        kb = [
            [InlineKeyboardButton(f"💳 Balance: ${info['balance']:.2f}", callback_data="my_status")],
            [InlineKeyboardButton("📞 GET NUMBER", callback_data="services"), InlineKeyboardButton("💰 WITHDRAWAL", callback_data="withdrawal")],
            [InlineKeyboardButton("📊 LIVE TRAFFIC", callback_data="live"), InlineKeyboardButton("👑 MY STATUS", callback_data="my_status")],
            [InlineKeyboardButton("🆘 SUPPORT", url=SUPPORT_ID)]
        ]
        await update.message.reply_text("👑 **APN NUMBER BOT এ আপনাকে স্বাগতম**\n\nআপনার নির্ভরযোগ্য নাম্বার এবং OTP পরিষেবা।", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
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

    if data!= "check" and not await is_joined(uid, context):
        kb = [[InlineKeyboardButton("📢 JOIN: APN OFFICIAL", url=CH1)],
              [InlineKeyboardButton("📢 JOIN: APN BACKUP", url=CH2)],
              [InlineKeyboardButton("🤖 JOIN: PROXY BOT", url=BOT_LINK)],
              [InlineKeyboardButton("👥 JOIN: APN OTP GROUP", url=OTP_GROUP)],
              [InlineKeyboardButton("✅ CHECK JOINED", callback_data="check")]]
        await q.edit_message_text("❌ **আপনি চ্যানেল থেকে লিভ নিয়েছেন!**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return

    db = load_bal()
    info = get_user_info(uid)

    if data == "check":
        if await is_joined(uid, context):
            kb = [[InlineKeyboardButton(f"💳 Balance: ${info['balance']:.2f}", callback_data="my_status")],
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

    if data == "main":
        kb = [[InlineKeyboardButton(f"💳 Balance: ${info['balance']:.2f}", callback_data="my_status")],
              [InlineKeyboardButton("📞 GET NUMBER", callback_data="services"), InlineKeyboardButton("💰 WITHDRAWAL", callback_data="withdrawal")],
              [InlineKeyboardButton("📊 LIVE TRAFFIC", callback_data="live"), InlineKeyboardButton("👑 MY STATUS", callback_data="my_status")],
              [InlineKeyboardButton("🆘 SUPPORT", url=SUPPORT_ID)]]
        await q.edit_message_text("👑 **APN NUMBER BOT**\n\nমেনু থেকে সেবা নির্বাচন করুন।", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data == "my_status":
        txt = (
            f"👑 **আপনার প্রোফাইল**\n\n"
            f"🆔 User ID: `{uid}`\n"
            f"💳 বর্তমান ব্যালেন্স: **${info['balance']:.2f}**\n"
            f"📞 মোট নাম্বার নিয়েছেন: **{info['numbers']} টি**\n"
            f"👥 রেফারেল: **{info['ref']} জন**\n\n"
            f"💡 ব্যালেন্স বাড়াতে সাপোর্টে যোগাযোগ করুন।"
        )
        kb = [[InlineKeyboardButton("💰 WITHDRAWAL", callback_data="withdrawal")],
              [InlineKeyboardButton("⬅️ BACK", callback_data="main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data == "live":
        total_users = len(db)
        txt = (
            f"📊 **LIVE TRAFFIC**\n\n"
            f"👥 মোট ইউজার: **{total_users} জন**\n"
            f"📞 আজকের নাম্বার সেল: **{sum([u['numbers'] for u in db.values()])} টি**\n"
            f"🟢 বট স্ট্যাটাস: **Online**\n"
            f"⚡ সার্ভার: **Active**"
        )
        kb = [[InlineKeyboardButton("⬅️ BACK", callback_data="main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data == "withdrawal":
        txt = (
            f"💰 **WITHDRAWAL**\n\n"
            f"💳 আপনার ব্যালেন্স: **${info['balance']:.2f}**\n"
            f"💵 মিনিমাম উইথড্র: **$5.00**\n\n"
            f"উইথড্র করতে সাপোর্টে মেসেজ দিন:\n"
            f"👉 {SUPPORT_ID}\n\n"
            f"ফরম্যাট: `Withdraw $amount bKash Number`"
        )
        kb = [[InlineKeyboardButton("🆘 CONTACT SUPPORT", url=SUPPORT_ID)],
              [InlineKeyboardButton("⬅️ BACK", callback_data="main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data == "services":
        kb = [[InlineKeyboardButton(f"{s}", callback_data=f"s_{s}")] for s in SERVICES]
        kb.append([InlineKeyboardButton("❌ CLOSE", callback_data="main")])
        await q.edit_message_text("🔹 **Please select a service:**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data.startswith("s_"):
        context.user_data['service'] = data[2:]
        kb = []; row = []
        for c in COUNTRIES:
            row.append(InlineKeyboardButton(c, callback_data=f"c_{c}"))
            if len(row)==2: kb.append(row); row=[]
        if row: kb.append(row)
        kb.append([InlineKeyboardButton("↩️ CHANGE SERVICE", callback_data="services")])
        await q.edit_message_text(f"Service: **{context.user_data['service']}**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data.startswith("c_"):
        country = data[2:]
        service = context.user_data.get('service', 'TELEGRAM')
        num1 = get_number(service, country)
        num2 = get_number(service, country)
        num3 = get_number(service, country)

        # Number count barbe
        db[str(uid)]["numbers"] += 3
        save_bal(db)

        kb = [
            [InlineKeyboardButton(f"📋 {num1}", copy_text=CopyTextButton(text=num1))],
            [InlineKeyboardButton(f"📋 {num2}", copy_text=CopyTextButton(text=num2))],
            [InlineKeyboardButton(f"📋 {num3}", copy_text=CopyTextButton(text=num3))],
            [InlineKeyboardButton("🌐 Change Country", callback_data=f"s_{service}"), InlineKeyboardButton("🔢 Set Prefix", callback_data="main")],
            [InlineKeyboardButton("🔄 Change Number", callback_data=f"c_{country}")],
            [InlineKeyboardButton("🛡️ OTP Group", url=OTP_GROUP)]
        ]
        txt = (
            f"**YOUR {country} {service} NUMBER**\n\n"
            f"🎉 **আপনার {country} এর {service} নাম্বার প্রস্তুত:**\n\n"
            f"✅ **OTP পেতে অনুগ্রহ করে নিচের OTP গ্রুপে নজর রাখুন।**\n"
            f"👇 নাম্বারে ক্লিক করলে কপি হয়ে যাবে।"
        )
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle))
app.run_polling()
