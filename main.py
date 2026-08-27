import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from panel import get_number

TOKEN = os.getenv("BOT_TOKEN")

# Leave check er jonno bot ke admin rakhte hobe
MUST_JOIN = ["@ApnNumber", "@APNOTP"]

CH1 = "https://t.me/ApnNumber"
CH2 = "https://t.me/+3N7St38N__ZkMTZl"
BOT_LINK = "https://t.me/Proxystore999"
OTP_GROUP = "https://t.me/APNOTP"
SUPPORT_ID = "https://t.me/PolasChandra"

SERVICES = ["IMO", "TELEGRAM", "VK", "WHATSAPP"]
COUNTRIES = ["TUNISIA 🇹🇳", "HAITI 🇭🇹", "ITALY 🇮🇹", "MALAYSIA 🇲🇾", "MOROCCO 🇲🇦", "MYANMAR 🇲🇲", "NIGERIA 🇳🇬", "UKRAINE 🇺🇦"]

async def is_joined(user_id, context):
    for ch in MUST_JOIN:
        try:
            member = await context.bot.get_chat_member(chat_id=ch, user_id=user_id)
            if member.status in ['left', 'kicked', 'kicked']:
                return False
        except Exception as e:
            print(f"Check error {ch}: {e}")
            return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if await is_joined(user_id, context):
        kb = [
            [InlineKeyboardButton("📞 GET NUMBER", callback_data="services"), InlineKeyboardButton("💰 WITHDRAWAL", callback_data="main")],
            [InlineKeyboardButton("📊 LIVE TRAFFIC", callback_data="main"), InlineKeyboardButton("👑 MY STATUS", callback_data="main")],
            [InlineKeyboardButton("🆘 SUPPORT", url=SUPPORT_ID)]
        ]
        await update.message.reply_text(
            "👑 **APN NUMBER BOT এ আপনাকে স্বাগতম**\n\n"
            "আপনার নির্ভরযোগ্য নাম্বার এবং OTP পরিষেবা। অনুগ্রহ করে নিচের মেনু থেকে আপনার কাঙ্খিত সেবাটি নির্বাচন করুন।",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="Markdown"
        )
    else:
        kb = [
            [InlineKeyboardButton("📢 JOIN: APN OFFICIAL", url=CH1)],
            [InlineKeyboardButton("📢 JOIN: APN BACKUP", url=CH2)],
            [InlineKeyboardButton("🤖 JOIN: PROXY BOT", url=BOT_LINK)],
            [InlineKeyboardButton("👥 JOIN: APN OTP GROUP", url=OTP_GROUP)],
            [InlineKeyboardButton("✅ CHECK JOINED", callback_data="check")]
        ]
        await update.message.reply_text("⚠️ **বট ব্যবহারের পূর্বে চ্যানেলে জয়েন করুন**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    user_id = q.from_user.id

    # --- FORCE JOIN LOCK (Prottek click e check hobe, leave korle atke jabe) ---
    if data != "check":
        if not await is_joined(user_id, context):
            kb = [
                [InlineKeyboardButton("📢 JOIN: APN OFFICIAL", url=CH1)],
                [InlineKeyboardButton("📢 JOIN: APN BACKUP", url=CH2)],
                [InlineKeyboardButton("🤖 JOIN: PROXY BOT", url=BOT_LINK)],
                [InlineKeyboardButton("👥 JOIN: APN OTP GROUP", url=OTP_GROUP)],
                [InlineKeyboardButton("✅ CHECK JOINED", callback_data="check")]
            ]
            await q.edit_message_text("❌ **আপনি চ্যানেল থেকে লিভ নিয়েছেন!**\n\nবট ব্যবহার চালিয়ে যেতে অনুগ্রহ করে পুনরায় জয়েন করুন।", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
            return

    if data == "check":
        if await is_joined(user_id, context):
            kb = [
                [InlineKeyboardButton("📞 GET NUMBER", callback_data="services"), InlineKeyboardButton("💰 WITHDRAWAL", callback_data="main")],
                [InlineKeyboardButton("📊 LIVE TRAFFIC", callback_data="main"), InlineKeyboardButton("👑 MY STATUS", callback_data="main")],
                [InlineKeyboardButton("🆘 SUPPORT", url=SUPPORT_ID)]
            ]
            await q.edit_message_text("✅ **যাচাইকরণ সফল!**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        else:
            kb = [
                [InlineKeyboardButton("📢 JOIN: APN OFFICIAL", url=CH1)],
                [InlineKeyboardButton("📢 JOIN: APN BACKUP", url=CH2)],
                [InlineKeyboardButton("🤖 JOIN: PROXY BOT", url=BOT_LINK)],
                [InlineKeyboardButton("👥 JOIN: APN OTP GROUP", url=OTP_GROUP)],
                [InlineKeyboardButton("✅ CHECK JOINED", callback_data="check")]
            ]
            await q.edit_message_text("❌ **আপনি এখনো সকল চ্যানেলে জয়েন করেননি।**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return

    user_data = context.user_data
    if data == "main":
        kb = [
            [InlineKeyboardButton("📞 GET NUMBER", callback_data="services"), InlineKeyboardButton("💰 WITHDRAWAL", callback_data="main")],
            [InlineKeyboardButton("📊 LIVE TRAFFIC", callback_data="main"), InlineKeyboardButton("👑 MY STATUS", callback_data="main")],
            [InlineKeyboardButton("🆘 SUPPORT", url=SUPPORT_ID)]
        ]
        await q.edit_message_text("👑 **APN NUMBER BOT**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    elif data == "services":
        kb = [[InlineKeyboardButton(f"{s}", callback_data=f"s_{s}")] for s in SERVICES]
        kb.append([InlineKeyboardButton("❌ CLOSE", callback_data="main")])
        await q.edit_message_text("🔹 **Please select a service:**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    elif data.startswith("s_"):
        user_data['service'] = data[2:]
        kb = []; row = []
        for c in COUNTRIES:
            row.append(InlineKeyboardButton(c, callback_data=f"c_{c}"))
            if len(row)==2: kb.append(row); row=[]
        if row: kb.append(row)
        kb.append([InlineKeyboardButton("↩️ CHANGE SERVICE", callback_data="services")])
        await q.edit_message_text(f"Service: **{user_data['service']}**\n\n🌍 **Please select a country:**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    elif data.startswith("c_"):
        country = data[2:]
        service = user_data.get('service', 'TELEGRAM')
        
        # --- EARN MASTER ER MOTO 3 TA NUMBER ---
        num1 = get_number(service, country)
        num2 = get_number(service, country)
        num3 = get_number(service, country)

        # Ekhon left side er moto design
        kb = [
            [InlineKeyboardButton(f"📱 {num1}", callback_data="main")],
            [InlineKeyboardButton(f"📱 {num2}", callback_data="main")],
            [InlineKeyboardButton(f"📱 {num3}", callback_data="main")],
            [InlineKeyboardButton("🌐 Change Country", callback_data=f"s_{service}"), InlineKeyboardButton("🔢 Set Prefix", callback_data="main")],
            [InlineKeyboardButton("🔄 Change Number", callback_data=f"c_{country}")],
            [InlineKeyboardButton("🛡️ OTP Group", url=OTP_GROUP)]
        ]
        
        header = f"YOUR {country} {service} NUMBER"
        
        text = (
            f"**{header}**\n\n"
            f"🎉 **আপনার {country} এর {service} নাম্বার প্রস্তুত:**\n\n"
            f"`{num1}`\n`{num2}`\n`{num3}`\n\n"
            f"✅ **OTP পেতে অনুগ্রহ করে নিচের OTP গ্রুপে নজর রাখুন।**"
        )
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle))
app.run_polling()
