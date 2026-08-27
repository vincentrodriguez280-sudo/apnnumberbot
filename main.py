import os, json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from panel import get_number

TOKEN = os.getenv("BOT_TOKEN")

SERVICES = ["IMO", "TELEGRAM", "VK", "WHATSAPP"]
COUNTRIES = ["HAITI 🇭🇹", "ITALY 🇮🇹", "MALAYSIA 🇲🇾", "MOROCCO 🇲🇦", "MYANMAR 🇲🇲", "NIGERIA 🇳🇬", "TANZANIA 🇹🇿", "UKRAINE 🇺🇦"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("📢 Join Channel: EARN MASTER (number)", url="https://t.me/")],
        [InlineKeyboardButton("📢 Join Channel: EARN MASTER METHOD", url="https://t.me/")],
        [InlineKeyboardButton("📢 Join Channel: EARN MASTER TOP", url="https://t.me/")],
        [InlineKeyboardButton("✅ Check Joined", callback_data="main")]
    ]
    await update.message.reply_text("⚠️ Please join our channels/groups to use the bot!", reply_markup=InlineKeyboardMarkup(kb))

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    user_data = context.user_data

    if data == "main":
        kb = [
            [InlineKeyboardButton("📞 GET NUMBER", callback_data="services"), InlineKeyboardButton("💰 WITHDRAWAL", callback_data="main")],
            [InlineKeyboardButton("📊 Live Traffic", callback_data="main"), InlineKeyboardButton("👑 My Status", callback_data="main")],
            [InlineKeyboardButton("🆘 SUPPORT", callback_data="main")]
        ]
        await q.edit_message_text("👑 NUMBER BOT\n\n🧭 Welcome to Number & OTP Service", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "services":
        kb = [[InlineKeyboardButton(f" {s}", callback_data=f"s_{s}")] for s in SERVICES]
        kb.append([InlineKeyboardButton("❌ CLOSE", callback_data="main")])
        await q.edit_message_text("🔹 Select a service:", reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith("s_"):
        user_data['service'] = data[2:]
        kb = []
        row = []
        for c in COUNTRIES:
            row.append(InlineKeyboardButton(c, callback_data=f"c_{c}"))
            if len(row)==2:
                kb.append(row); row=[]
        if row: kb.append(row)
        kb.append([InlineKeyboardButton("↩️ Change Service", callback_data="services")])
        await q.edit_message_text(f"Service: {user_data['service']}\nSelect Country:", reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith("c_"):
        country = data[2:]
        service = user_data.get('service', 'TELEGRAM')
        # Ekhane panel.py theke number asbe
        num1 = get_number(service, country)
        num2 = get_number(service, country)
        num3 = get_number(service, country)

        kb = [
            [InlineKeyboardButton(f"{country} {num1}", callback_data="main")],
            [InlineKeyboardButton(f"{country} {num2}", callback_data="main")],
            [InlineKeyboardButton(f"{country} {num3}", callback_data="main")],
            [InlineKeyboardButton("🌐 Change Country", callback_data=f"s_{service}"), InlineKeyboardButton("🔢 Set Prefix", callback_data="main")],
            [InlineKeyboardButton("🔄 Change Number", callback_data=f"c_{country}")],
            [InlineKeyboardButton("🛡️ OTP Group", url="https://t.me/")]
        ]
        await q.edit_message_text(f"YOUR {country} {service} NUMBER", reply_markup=InlineKeyboardMarkup(kb))

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle))
app.run_polling()
