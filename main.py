import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from panel import get_number

TOKEN = os.getenv("BOT_TOKEN")

# TOR CHANNEL ID - bot admin thakte hobe
MUST_JOIN = ["@ApnNumber", "@APNOTP"]  # backup er invite link check kora jay na, tai 2 ta main check hobe

CH1 = "https://t.me/ApnNumber"
CH2 = "https://t.me/+3N7St38N__ZkMTZl"
BOT_LINK = "https://t.me/Proxystore999"
OTP_GROUP = "https://t.me/APNOTP"

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
    kb = [
        [InlineKeyboardButton("📢 APN OFFICIAL", url=CH1)],
        [InlineKeyboardButton("📢 APN BACKUP CHANNEL", url=CH2)],
        [InlineKeyboardButton("🤖 PROXY VPN BUY BOT", url=BOT_LINK)],
        [InlineKeyboardButton("👥 APN OTP GROUP", url=OTP_GROUP)],
        [InlineKeyboardButton("✅ Check Joined", callback_data="check")]
    ]
    await update.message.reply_text("⚠️ Bot use korte hole age sob channel e join koro!", reply_markup=InlineKeyboardMarkup(kb))

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    user_id = q.from_user.id

    if data == "check":
        if await is_joined(user_id, context):
            kb = [
                [InlineKeyboardButton("📞 GET NUMBER", callback_data="services"), InlineKeyboardButton("💰 WITHDRAWAL", callback_data="main")],
                [InlineKeyboardButton("📊 Live Traffic", callback_data="main"), InlineKeyboardButton("👑 My Status", callback_data="main")],
                [InlineKeyboardButton("🆘 SUPPORT", callback_data="main")]
            ]
            await q.edit_message_text("✅ Joined! Welcome to APN NUMBER BOT", reply_markup=InlineKeyboardMarkup(kb))
        else:
            kb = [
                [InlineKeyboardButton("📢 APN OFFICIAL", url=CH1)],
                [InlineKeyboardButton("📢 APN BACKUP CHANNEL", url=CH2)],
                [InlineKeyboardButton("🤖 PROXY VPN BUY BOT", url=BOT_LINK)],
                [InlineKeyboardButton("👥 APN OTP GROUP", url=OTP_GROUP)],
                [InlineKeyboardButton("✅ Check Joined", callback_data="check")]
            ]
            await q.edit_message_text("❌ Tumi ekhono join koro nai! Age join koro tarpor Check Joined e click koro.", reply_markup=InlineKeyboardMarkup(kb))
        return

    # jodi join na kore onno button e click kore
    if not await is_joined(user_id, context):
        kb = [
            [InlineKeyboardButton("📢 APN OFFICIAL", url=CH1)],
            [InlineKeyboardButton("📢 APN BACKUP CHANNEL", url=CH2)],
            [InlineKeyboardButton("🤖 PROXY VPN BUY BOT", url=BOT_LINK)],
            [InlineKeyboardButton("👥 APN OTP GROUP", url=OTP_GROUP)],
            [InlineKeyboardButton("✅ Check Joined", callback_data="check")]
        ]
        await q.edit_message_text("⚠️ Age channel e join koro!", reply_markup=InlineKeyboardMarkup(kb))
        return

    user_data = context.user_data
    if data == "main":
        kb = [
            [InlineKeyboardButton("📞 GET NUMBER", callback_data="services"), InlineKeyboardButton("💰 WITHDRAWAL", callback_data="main")],
            [InlineKeyboardButton("📊 Live Traffic", callback_data="main"), InlineKeyboardButton("👑 My Status", callback_data="main")],
            [InlineKeyboardButton("🆘 SUPPORT", callback_data="main")]
        ]
        await q.edit_message_text("👑 APN NUMBER BOT\n\n🧭 Welcome", reply_markup=InlineKeyboardMarkup(kb))
    elif data == "services":
        kb = [[InlineKeyboardButton(f" {s}", callback_data=f"s_{s}")] for s in SERVICES]
        kb.append([InlineKeyboardButton("❌ CLOSE", callback_data="main")])
        await q.edit_message_text("🔹 Select a service:", reply_markup=InlineKeyboardMarkup(kb))
    elif data.startswith("s_"):
        user_data['service'] = data[2:]
        kb = []; row = []
        for c in COUNTRIES:
            row.append(InlineKeyboardButton(c, callback_data=f"c_{c}"))
            if len(row)==2: kb.append(row); row=[]
        if row: kb.append(row)
        kb.append([InlineKeyboardButton("↩️ Change Service", callback_data="services")])
        await q.edit_message_text(f"Service: {user_data['service']}\nSelect Country:", reply_markup=InlineKeyboardMarkup(kb))
    elif data.startswith("c_"):
        country = data[2:]
        service = user_data.get('service', 'TELEGRAM')
        num1 = get_number(service, country)
        kb = [
            [InlineKeyboardButton(f"{country} {num1}", callback_data="main")],
            [InlineKeyboardButton("🌐 Change Country", callback_data=f"s_{service}")],
            [InlineKeyboardButton("🔄 Change Number", callback_data=f"c_{country}")],
            [InlineKeyboardButton("🛡️ APN OTP GROUP", url=OTP_GROUP)]
        ]
        await q.edit_message_text(f"YOUR {country} {service} NUMBER", reply_markup=InlineKeyboardMarkup(kb))

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle))
app.run_polling()
