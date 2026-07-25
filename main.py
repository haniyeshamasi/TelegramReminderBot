from dotenv import load_dotenv
import os

load_dotenv()

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

TOKEN =os.getenv("BOT_TOKEN")

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("I got your message! 🎉")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT, reply))

print("Bot is running...")

app.run_polling()
