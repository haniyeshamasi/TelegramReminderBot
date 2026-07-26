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
    print("RECEIVED:", update.message.text)
    text = update.message.text
    user_id = update.message.from_user.id

    # پیدا کردن ایمیل
    email_match = re.search(
        r'[\w\.-]+@[\w\.-]+',
        text
    )

    email = email_match.group() if email_match else "Not found"


    # پیدا کردن شماره
    phone_match = re.search(
        r'(?:\(?\d{3}\)?[\s-]?)?\d{3}[\s-]?\d{4}',
        text
    )

    phone = (
        phone_match.group()
        .replace(" ", "")
        .replace("-", "")
        if phone_match else "Not found"
    )


    # پیدا کردن وضعیت
    if "POTENTIAL" in text.upper():
        status = "POTENTIAL"
    else:
        status = "NEW"


    # حدس شرکت (فعلاً چند کلمه اول)
    parts = text.split()

    company = " ".join(parts[:3]) if len(parts) >= 3 else text


    # پیدا کردن اسم تماس
    contact = "Unknown"

    if "Ms." in parts:
        index = parts.index("Ms.")

        if index + 1 < len(parts):
            contact = parts[index] + " " + parts[index + 1]

    elif "Mr." in parts:
        index = parts.index("Mr.")

        if index + 1 < len(parts):
            contact = parts[index] + " " + parts[index + 1]


    note = text


    add_lead(
        user_id,
        company,
        contact,
        email,
        phone,
        status,
        note
    )


    await update.message.reply_text(
        f"✅ Lead Saved\n\n"
        f"🏢 Company: {company}\n"
        f"👤 Contact: {contact}\n"
        f"📧 Email: {email}\n"
        f"📞 Phone: {phone}\n"
        f"📌 Status: {status}"
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