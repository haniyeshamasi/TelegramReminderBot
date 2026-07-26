import re
import os
import threading

from dotenv import load_dotenv
from flask import Flask

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters
)

from database import create_database, add_lead


load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")


web_app = Flask(__name__)


@web_app.route("/")
def home():
    return "Bot is alive!"


def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(
        host="0.0.0.0",
        port=port
    )


def parse_lead(text):

    email_match = re.search(
        r'[\w\.-]+@[\w\.-]+',
        text
    )

    phone_match = re.search(
        r'\b\d{10}\b',
        text.replace("-", "")
    )

    address_match = re.search(
        r'\d{1,5}\s+[A-Za-z0-9\s]+(?:St|Street|Blvd|Road|Rd|Ave|Avenue|Dr|Drive)[^,\n]*',
        text,
        re.I
    )


    email = email_match.group() if email_match else ""

    phone = phone_match.group() if phone_match else ""

    address = address_match.group() if address_match else ""


    # Extract company name (temporary simple method)
    words = text.split()
    company = " ".join(words[:3])


    # Detect lead status
    status = "NEW"

    status_words = [
        "potential",
        "voicemail",
        "follow up",
        "call back",
        "not interested",
        "25-Sep",
        "tomorrow"
    ]


    for item in status_words:
        if item.lower() in text.lower():
            status = item.upper()


    return {
        "company": company,
        "contact": "Unknown",
        "email": email,
        "phone": phone,
        "address": address,
        "status": status,
        "note": text
    }



async def add_lead_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text

    user_id = update.message.from_user.id


    # Split multiple leads from one message
    leads = text.split("\n\n")


    saved = 0


    for lead_text in leads:

        data = parse_lead(lead_text)


        add_lead(
    user_id,
    data["company"],
    data["contact"],
    data["email"],
    data["phone"],
    data["address"],
    data["status"],
    data["note"]
)


        saved += 1


    await update.message.reply_text(
        f"✅ {saved} Lead(s) Saved"
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



threading.Thread(
    target=run_web
).start()


run_bot()