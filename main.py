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

SERVICES = ["IMO", "TELEGRAM", "VK", "WHATSAPP"]
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
            [InlineKeyboardButton("📞 নাম্বার নিন", callback_data="services"), InlineKeyboardButton("💰 টাকা উত্তোলন", callback_data="main")],
            [InlineKeyboardButton("📊 লাইভ ট্রাফিক", callback_data="main"), InlineKeyboardButton("👑 আমার স্ট্যাটাস", callback_data="main")],
            [InlineKeyboardButton("🆘 সাপোর্ট", url=SUPPORT_ID)]
        ]
        await update.message.reply_text(
            "👑 **APN NUMBER BOT এ স্বাগতম**\n\n"
            "আপনার নির্ভরযোগ্য নাম্বার এবং OTP পরিষেবা। নিচের মেনু থেকে আপনার কাঙ্খিত সেবাটি নির্বাচন করুন।",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="Markdown"
        )
    else:
        kb = [
            [InlineKeyboardButton("📢 APN OFFICIAL চ্যানেল", url=CH1)],
            [InlineKeyboardButton("📢 APN ব্যাকআপ চ্যানেল", url=CH2)],
            [InlineKeyboardButton("🤖 প্রক্সি ভিপিএন বাই বট", url=BOT_LINK)],
            [InlineKeyboardButton("👥 APN OTP গ্রুপ", url=OTP_GROUP)],
            [InlineKeyboardButton("✅ জয়েন চেক করুন", callback_data="check")]
        ]
        await update.message.reply_text(
            "⚠️ **বট ব্যবহারের আগে অনুগ্রহ করে চ্যানেলগুলোতে জয়েন করুন**\n\n"
            "আমাদের সকল আপডেট এবং OTP পেতে নিচের চ্যানেল ও গ্রুপে জয়েন করা বাধ্যতামূলক। জয়েন করার পর 'জয়েন চেক করুন' বাটনে ক্লিক করুন।",
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
                [InlineKeyboardButton("📞 নাম্বার নিন", callback_data="services"), InlineKeyboardButton("💰 টাকা উত্তোলন", callback_data="main")],
                [InlineKeyboardButton("📊 লাইভ ট্রাফিক", callback_data="main"), InlineKeyboardButton("👑 আমার স্ট্যাটাস", callback_data="main")],
                [InlineKeyboardButton("🆘 সাপোর্ট", url=SUPPORT_ID)]
            ]
            await q.edit_message_text(
                "✅ **ধন্যবাদ! আপনি সফলভাবে জয়েন করেছেন।**\n\n👑 APN NUMBER BOT এ আপনাকে স্বাগতম।",
                reply_markup=InlineKeyboardMarkup(kb),
                parse_mode="Markdown"
            )
        else:
            kb = [
                [InlineKeyboardButton("📢 APN OFFICIAL চ্যানেল", url=CH1)],
                [InlineKeyboardButton("📢 APN ব্যাকআপ চ্যানেল", url=CH2)],
                [InlineKeyboardButton("🤖 প্রক্সি ভিপিএন বাই বট", url=BOT_LINK)],
                [InlineKeyboardButton("👥 APN OTP গ্রুপ", url=OTP_GROUP)],
                [InlineKeyboardButton("✅ জয়েন চেক করুন", callback_data="check")]
            ]
            await q.edit_message_text(
                "❌ **আপনি এখনো সকল চ্যানেলে জয়েন করেননি।**\n\nঅনুগ্রহ করে উপরের সকল চ্যানেলে জয়েন করে আবার চেক করুন।",
                reply_markup=InlineKeyboardMarkup(kb),
                parse_mode="Markdown"
            )
        return

    if not await is_joined(user_id, context):
        kb = [
            [InlineKeyboardButton("📢 APN OFFICIAL চ্যানেল", url=CH1)],
            [InlineKeyboardButton("📢 APN BACKUP চ্যানেল", url=CH2)],
            [InlineKeyboardButton("🤖 PROXY VPN BUY BOT", url=BOT_LINK)],
            [InlineKeyboardButton("👥 APN OTP গ্রুপ", url=OTP_GROUP)],
            [InlineKeyboardButton("✅ জয়েন চেক করুন", callback_data="check")]
        ]
        await q.edit_message_text("⚠️ বট ব্যবহার করতে হলে আপনাকে অবশ্যই আমাদের চ্যানেলে জয়েন করতে হবে।", reply_markup=InlineKeyboardMarkup(kb))
        return

    user_data = context.user_data
    if data == "main":
        kb = [
            [InlineKeyboardButton("📞 নাম্বার নিন", callback_data="services"), InlineKeyboardButton("💰 টাকা উত্তোলন", callback_data="main")],
            [InlineKeyboardButton("📊 লাইভ ট্রাফিক", callback_data="main"), InlineKeyboardButton("👑 আমার স্ট্যাটাস", callback_data="main")],
            [InlineKeyboardButton("🆘 সাপোর্ট", url=SUPPORT_ID)]
        ]
        await q.edit_message_text("👑 **APN NUMBER BOT**\n\nআপনার পছন্দের সেবাটি নির্বাচন করুন।", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    elif data == "services":
        kb = [[InlineKeyboardButton(f"📱 {s}", callback_data=f"s_{s}")] for s in SERVICES]
        kb.append([InlineKeyboardButton("❌ বন্ধ করুন", callback_data="main")])
        await q.edit_message_text("🔹 **অনুগ্রহ করে একটি সার্ভিস নির্বাচন করুন:**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    elif data.startswith("s_"):
        user_data['service'] = data[2:]
        kb = []; row = []
        for c in COUNTRIES:
            row.append(InlineKeyboardButton(c, callback_data=f"c_{c}"))
            if len(row)==2: kb.append(row); row=[]
        if row: kb.append(row)
        kb.append([InlineKeyboardButton("↩️ সার্ভিস পরিবর্তন করুন", callback_data="services")])
        await q.edit_message_text(f"✅ সার্ভিস: **{user_data['service']}**\n\n🌍 এখন দেশ নির্বাচন করুন:", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    elif data.startswith("c_"):
        country = data[2:]
        service = user_data.get('service', 'TELEGRAM')
        num1 = get_number(service, country)
        kb = [
            [InlineKeyboardButton(f"📞 {country} {num1}", callback_data="main")],
            [InlineKeyboardButton("🌐 দেশ পরিবর্তন", callback_data=f"s_{service}"), InlineKeyboardButton("🔢 প্রিফিক্স সেট করুন", callback_data="main")],
            [InlineKeyboardButton("🔄 নাম্বার পরিবর্তন করুন", callback_data=f"c_{country}")],
            [InlineKeyboardButton("🛡️ APN OTP গ্রুপে জয়েন করুন", url=OTP_GROUP)]
        ]
        await q.edit_message_text(f"🎉 আপনার **{country}** এর **{service}** নাম্বার প্রস্তুত:\n\n`{num1}`\n\nOTP পেতে নিচের গ্রুপে নজর রাখুন।", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle))
app.run_polling()
