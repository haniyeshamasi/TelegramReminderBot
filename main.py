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



def extract_email(text):

    match = re.search(
        r'[\w\.-]+@[\w\.-]+',
        text
    )

    return match.group() if match else "Not found"



def extract_phone(text):

    match = re.search(
        r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
        text
    )

    return match.group() if match else "Not found"



def extract_reminder(text):

    patterns = [

        r'(?:follow[- ]?up|call back|callback|call)\s+(?:in|after|at|on)?\s+.*',

        r'\b(?:tomorrow|next week|next month)\b'

    ]


    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            return match.group().strip()


    return ""



def extract_company(text):

    lines = text.split("\n")

    if lines:

        company = lines[0]

        company = re.split(
            r'\d{10}',
            company
        )[0]

        return company.strip()


    return "Not found"



def extract_address(text):

    match = re.search(
        r'\d{1,6}\s+[A-Za-z0-9\s]+(?:St|Street|Rd|Road|Blvd|Drive|Dr|Ave|Avenue)[^,\n]*',
        text,
        re.IGNORECASE
    )

    return match.group().strip() if match else "Not found"



def create_note(text, reminder):

    note = text

    if reminder:

        note = note.replace(
            reminder,
            ""
        )

    return note.strip()



def parse_lead(text):

    reminder = extract_reminder(text)

    return {

        "company": extract_company(text),

        "email": extract_email(text),

        "phone": extract_phone(text),

        "address": extract_address(text),

        "reminder": reminder,

        "note": create_note(
            text,
            reminder
        )

    }



async def add_lead_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text

    user_id = update.message.from_user.id


    data = parse_lead(text)


    add_lead(
        user_id,
        data["company"],
        data["email"],
        data["phone"],
        data["address"],
        data["reminder"],
        data["note"]
    )


    await update.message.reply_text(
        f"✅ Lead Saved\n\n"
        f"🏢 Company: {data['company']}\n"
        f"📧 Email: {data['email']}\n"
        f"📞 Phone: {data['phone']}\n"
        f"📍 Address: {data['address']}\n"
        f"⏰ Reminder: {data['reminder']}\n"
        f"📝 Note: {data['note']}"
    )



def run_bot():

    create_database()

    app = ApplicationBuilder()\
        .token(TOKEN)\
        .build()


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