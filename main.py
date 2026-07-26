import re
import os
import logging
import threading

from dotenv import load_dotenv
from flask import Flask

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)

from database import create_database, add_lead


# ── Logging ────────────────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# ── Config ─────────────────────────────────────────────────────────────────

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise EnvironmentError("BOT_TOKEN is not set")


# ── Flask Keep Alive ────────────────────────────────────────────────────────

web_app = Flask(__name__)


@web_app.route("/")
def home():
    return "Bot is alive!"



def run_web():

    port = int(os.environ.get("PORT", 10000))

    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)

    web_app.run(
        host="0.0.0.0",
        port=port
    )



# ── Extractors ──────────────────────────────────────────────────────────────


def extract_email(text):

    match = re.search(
        r"[\w\.\-]+@[\w\.\-]+\.\w{2,}",
        text,
        re.IGNORECASE
    )

    return match.group().strip() if match else "Not found"



def extract_phone(text):

    match = re.search(
        r"\b(?:\+?1[\s.\-]?)?(?:\(?\d{3}\)?[\s.\-]?)\d{3}[\s.\-]?\d{4}\b",
        text
    )

    return match.group().strip() if match else "Not found"



def extract_address(text):

    street_types = (
        r"(?:St\.?|Street|Rd\.?|Road|Blvd\.?|Boulevard"
        r"|Dr\.?|Drive|Ave\.?|Avenue|Way|Ln\.?|Lane"
        r"|Ct\.?|Court|Pl\.?|Place|Pkwy\.?|Parkway)"
    )

    pattern = (
        r"\d{1,6}"
        r"\s+[A-Za-z0-9\s\.\-]{2,40}?"
        + street_types +
        r"(?:\s+Ste\.?\s+\d+)?"
        r"(?:,\s*[A-Za-z][A-Za-z\s]{1,25},\s*[A-Z]{2}\s*\d{5})?"
    )


    match = re.search(
        pattern,
        text,
        re.IGNORECASE
    )

    return match.group().strip() if match else "Not found"



def extract_reminder(text):

    patterns = [

        r"follow[- ]?up[^\n]*",

        r"call[- ]?back[^\n]*",

        r"callback[^\n]*",

        r"will call[^\n]*",

        r"will contact[^\n]*",

        r"will reach out[^\n]*",

        r"call[^\n]*(?:on|at|in)[^\n]*",

        r"contact[^\n]*(?:on|at|in)[^\n]*",

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

    lines = text.strip().split("\n")


    # Multiline format
    if len(lines) > 1:

        company = lines[0].strip()


    # Single line format
    else:

        parts = re.split(
            r"\s{2,}",
            text.strip()
        )

        company = parts[0].strip()



    company = re.sub(
        r"\b\d{7,}\b",
        "",
        company
    )

    company = re.sub(
        r"[\w\.\-]+@[\w\.\-]+",
        "",
        company
    )


    return company.strip(" ,") if company.strip() else "Not found"



def create_note(
    text,
    reminder,
    address,
    email,
    phone,
    company
):

    note = text


    for item in [
        reminder,
        address,
        email,
        phone,
        company
    ]:

        if item and item != "Not found":

            note = note.replace(
                item,
                ""
            )


    note = re.sub(
        r"[ \t]{2,}",
        " ",
        note
    )


    note = re.sub(
        r"\n{3,}",
        "\n\n",
        note
    )


    return note.strip()



# ── Parser ──────────────────────────────────────────────────────────────────


def parse_lead(text):

    email = extract_email(text)

    phone = extract_phone(text)

    address = extract_address(text)

    reminder = extract_reminder(text)

    company = extract_company(text)

    note = create_note(
        text,
        reminder,
        address,
        email,
        phone,
        company
    )


    return {

        "company": company,

        "email": email,

        "phone": phone,

        "address": address,

        "reminder": reminder,

        "note": note
    }



# ── Telegram Handler ────────────────────────────────────────────────────────


async def add_lead_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text

    user_id = update.message.from_user.id


    try:

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


        reply = (

            "✅ Lead Saved\n\n"

            f"🏢 Company: {data['company']}\n"

            f"📧 Email: {data['email']}\n"

            f"📞 Phone: {data['phone']}\n"

            f"📍 Address: {data['address']}\n"

            f"⏰ Reminder: {data['reminder'] if data['reminder'] else 'None'}\n"

            f"📝 Note: {data['note'] if data['note'] else 'None'}"

        )


        logger.info(
            "Lead saved: %s",
            data["company"]
        )


    except Exception as e:

        logger.exception(e)

        reply = (
            "❌ Error saving lead."
        )


    await update.message.reply_text(reply)



# ── Bot Runner ───────────────────────────────────────────────────────────────


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


    logger.info(
        "Bot is running..."
    )


    app.run_polling()



if __name__ == "__main__":

    threading.Thread(
        target=run_web,
        daemon=True
    ).start()


    run_bot()