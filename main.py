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

    return match.group() if match else ""



def extract_phone(text):

    match = re.search(
        r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
        text
    )

    return match.group() if match else ""



def extract_reminder(text):

    patterns = [

        r'follow[- ]?up\s+(?:in|after|at|on)?\s*.*',
        
        r'call\s+back\s+(?:in|after|at|on)?\s*.*',

        r'callback\s+(?:in|after|at|on)?\s*.*',

        r'call\s+(?:in|after|at|on)?\s*.*',

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
        return lines[0][:100]

    return ""



def extract_contact(text):

    names = re.findall(
        r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',
        text
    )

    if names:
        return names[-1]

    return ""



def extract_address(text):

    # Basic address extraction
    # Can be improved later with state/city detection

    match = re.search(
        r'\d{1,6}\s+[A-Za-z0-9\s]+(?:St|Street|Rd|Road|Blvd|Drive|Dr|Ave|Avenue)[^,\n]*',
        text,
        re.IGNORECASE
    )

    return match.group() if match else ""



def create_note(text, reminder):

    note = text

    if reminder:

        note = note.replace(
            reminder,
            ""
        )

    return note.strip()



def parse_lead(text):

    email = extract_email(text)

    phone = extract_phone(text)

    reminder = extract_reminder(text)

    return {

        "company": extract_company(text),

        "contact": extract_contact(text),

        "email": email,

        "phone": phone,

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


    # Split multiple leads by email occurrence
    leads = re.split(
        r'(?=[\w\.-]+@[\w\.-]+\.[A-Za-z]+)',
        text
    )


    saved = 0


    for lead_text in leads:

        if not lead_text.strip():
            continue


        data = parse_lead(
            lead_text
        )


        add_lead(
            user_id,

            data["company"],

            data["contact"],

            data["email"],

            data["phone"],

            data["address"],

            data["reminder"],

            data["note"]
        )


        saved += 1



    await update.message.reply_text(
        f"✅ {saved} Lead(s) Saved"
    )



def run_bot():

    create_database()


    app = ApplicationBuilder() \
        .token(TOKEN) \
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