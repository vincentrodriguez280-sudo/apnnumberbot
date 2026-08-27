import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Token code e likhbi na, Railway theke asbe
TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/")],
          [InlineKeyboardButton("✅ Check Joined", callback_data="ok")]]
    await update.message.reply_text("⚠️ Please join our channels!", reply_markup=InlineKeyboardMarkup(kb))

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    kb = [
        [InlineKeyboardButton("📞 GET NUMBER", callback_data="get"), InlineKeyboardButton("💰 WITHDRAWAL", callback_data="no")],
        [InlineKeyboardButton("📊 Live Traffic", callback_data="no"), InlineKeyboardButton("👑 My Status", callback_data="no")]
    ]
    await q.edit_message_text("👑 NUMBER BOT\nWelcome to Number & OTP Service", reply_markup=InlineKeyboardMarkup(kb))

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(main_menu))
app.run_polling()
