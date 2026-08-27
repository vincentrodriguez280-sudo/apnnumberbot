import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from panel import get_number

TOKEN = os.getenv("BOT_TOKEN")

MUST_JOIN = ["@ApnNumber", "@APNOTP"]

CH1 = "https://t.me/ApnNumber"
CH2 = "https://t.me/+3N7St38N__ZkMTZl"
BOT_LINK = "https://t.me/Proxystore999"
OTP_GROUP = "https://t.me/APNOTP"
SUPPORT_ID = "https://t.me/PolasChandra"

SERVICES = ["TELEGRAM", "WHATSAPP", "FACEBOOK", "TIKTOK"]
COUNTRIES = ["HAITI 🇭🇹", "ITALY 🇮🇹", "MALAYSIA 🇲🇾", "MOROCCO 🇲🇦", "MYANMAR 🇲🇲", "NIGERIA 🇳🇬", "TANZANIA 🇹🇿", "UKRAINE 🇺🇦"]

async def is_joined(user_id, context):
    for ch in MUST_JOIN:
        try:
            member = await context.bot.get_chat_member(chat_id=ch, user_id=user_id)
            if member.status in ['left', 'kicked']:
                return False
        except:
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
        await update.message.reply_text(
            "⚠️ **বট ব্যবহারের পূর্বে চ্যানেলে জয়েন করুন**\n\n"
            "আমাদের সকল আপডেট ও OTP পেতে নিচের চ্যানেলগুলোতে জয়েন করা বাধ্যতামূলক।",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="Markdown"
        )

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    user_id = q.from_user.id

    if data == "check":
        if await is_joined(user_id, context):
            kb = [
                [InlineKeyboardButton("📞 GET NUMBER", callback_data="services"), InlineKeyboardButton("💰 WITHDRAWAL", callback_data="main")],
                [InlineKeyboardButton("📊 LIVE TRAFFIC", callback_data="main"), InlineKeyboardButton("👑 MY STATUS", callback_data="main")],
                [InlineKeyboardButton("🆘 SUPPORT", url=SUPPORT_ID)]
            ]
            await q.edit_message_text("✅ **যাচাইকরণ সফল!**\n\nAPN NUMBER BOT এ আপনাকে স্বাগতম।", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        else:
            kb = [
                [InlineKeyboardButton("📢 JOIN: APN OFFICIAL", url=CH1)],
                [InlineKeyboardButton("📢 JOIN: APN BACKUP", url=CH2)],
                [InlineKeyboardButton("🤖 JOIN: PROXY BOT", url=BOT_LINK)],
                [InlineKeyboardButton("👥 JOIN: APN OTP GROUP", url=OTP_GROUP)],
                [InlineKeyboardButton("✅ CHECK JOINED", callback_data="check")]
            ]
            await q.edit_message_text("❌ **আপনি এখনো সকল চ্যানেলে জয়েন করেননি।**\nঅনুগ্রহ করে জয়েন করে পুনরায় চেষ্টা করুন।", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return

    if not await is_joined(user_id, context):
        kb = [
            [InlineKeyboardButton("📢 JOIN: APN OFFICIAL", url=CH1)],
            [InlineKeyboardButton("📢 JOIN: APN BACKUP", url=CH2)],
            [InlineKeyboardButton("🤖 JOIN: PROXY BOT", url=BOT_LINK)],
            [InlineKeyboardButton("👥 JOIN: APN OTP GROUP", url=OTP_GROUP)],
            [InlineKeyboardButton("✅ CHECK JOINED", callback_data="check")]
        ]
        await q.edit_message_text("⚠️ অনুগ্রহ করে প্রথমে আমাদের চ্যানেলে জয়েন করুন।", reply_markup=InlineKeyboardMarkup(kb))
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
        num = get_number(service, country)
        kb = [
            [InlineKeyboardButton(f"{country} {num}", callback_data="main")],
            [InlineKeyboardButton("🌐 CHANGE COUNTRY", callback_data=f"s_{service}"), InlineKeyboardButton("🔢 SET PREFIX", callback_data="main")],
            [InlineKeyboardButton("🔄 CHANGE NUMBER", callback_data=f"c_{country}")],
            [InlineKeyboardButton("🛡️ OTP GROUP", url=OTP_GROUP)]
        ]
        # EITA HOLO TOR GREEN MARK KORA JAYGA - EKHON PROFESSIONAL BANGLA
        text = (
            f"🎉 **আপনার {country} এর {service} নাম্বার প্রস্তুত:**\n\n"
            f"`{num}`\n\n"
            f"✅ OTP পেতে অনুগ্রহ করে নিচের OTP গ্রুপে নজর রাখুন।"
        )
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle))
app.run_polling()
