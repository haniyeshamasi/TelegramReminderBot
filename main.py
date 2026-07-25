import re
from database import add_lead, create_database
from dotenv import load_dotenv
import os
import threading

from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

web_app = Flask(__name__)


@web_app.route("/")
def home():
    return "Bot is alive!"


def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)


async def add_lead_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    user_id = update.message.from_user.id

    email_match = re.search(
        r'[\w\.-]+@[\w\.-]+',
        text
    )

    phone_match = re.search(
        r'\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}',
        text
    )

    email = email_match.group() if email_match else "Not found"
    phone = phone_match.group() if phone_match else "Not found"

    reminder = ""

    if "tomorrow" in text.lower():
        reminder = "Tomorrow"

    add_lead(
        user_id,
        email,
        phone,
        reminder,
        text
    )

    await update.message.reply_text(
        f"✅ Lead saved\n\n"
        f"📧 {email}\n"
        f"📞 {phone}\n"
        f"⏰ {reminder}"
    )


def run_bot():
    create_database()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            add_lead_message
        )
    )

    print("Bot is running...")

    app.run_polling()


threading.Thread(target=run_web).start()

run_bot()