import re
import os
import logging
import threading

from datetime import datetime, timedelta

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


# ── Logging ─────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# ── Config ─────────────────────────────────────────────

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise EnvironmentError("BOT_TOKEN is missing")


# ── Flask Keep Alive ───────────────────────────────────

web_app = Flask(__name__)


@web_app.route("/")
def home():
    return "Bot is alive!"



def run_web():

    port = int(os.environ.get("PORT", 10000))

    logging.getLogger("werkzeug").setLevel(logging.ERROR)

    web_app.run(
        host="0.0.0.0",
        port=port
    )


# ── Extractors ─────────────────────────────────────────


def extract_email(text):

    match = re.search(
        r"[\w\.-]+@[\w\.-]+\.\w+",
        text,
        re.IGNORECASE
    )

    return match.group() if match else "Not found"



def extract_phone(text):

    match = re.search(
        r"\b(?:\+?1[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}\b",
        text
    )

    return match.group() if match else "Not found"



def extract_address(text):

    pattern = (
        r"\d{1,6}\s+"
        r"[A-Za-z0-9\s\.]+"
        r"(?:St|Street|Rd|Road|Blvd|Boulevard|"
        r"Dr|Drive|Ave|Avenue|Way|Ln|Lane|"
        r"Ct|Court|Pl|Place|Pkwy|Parkway)"
        r"(?:\s+Ste\.?\s*\d+)?"
        r"(?:,\s*[A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5})?"
    )


    match = re.search(
        pattern,
        text,
        re.IGNORECASE
    )


    return match.group().strip() if match else "Not found"



def extract_company(text):

    lines = text.strip().split("\n")


    if len(lines) > 1:

        company = lines[0].strip()

    else:

        parts = re.split(
            r"\s{2,}",
            text
        )

        company = parts[0]


    company = re.sub(
        r"\d{7,}",
        "",
        company
    )

    company = re.sub(
        r"[\w\.-]+@[\w\.-]+",
        "",
        company
    )


    return company.strip(" ,") or "Not found"



# ── Reminder Parser ────────────────────────────────────


def extract_reminder(text):

    patterns = [

        r'\bin\s+(?:a|an|\d+)\s+(?:minute|minutes|hour|hours|day|days|week|weeks|month|months|year|years)(?:\s+or\s+(?:two|three))?\b',

        r'\bin\s+(?:a\s+)?(?:couple|few|several)\s+(?:of\s+)?(?:days|weeks|months|years)\b',

        r'\b(?:tomorrow|today|tonight|next week|next month|next year)\b',

        r'\b(?:next\s+)?(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',

        r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}\b',

        r'\b\d{1,2}[-/](?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\b',

        r'\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{1,2}\b',

    ]


    found = []


    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE
        )


        for match in matches:

            if match.lower() not in [
                x.lower() for x in found
            ]:

                found.append(match)


    return ", ".join(found)



def convert_reminder_to_date(reminder):

    if not reminder:
        return ""


    today = datetime.now()


    days = {
        "monday":0,
        "tuesday":1,
        "wednesday":2,
        "thursday":3,
        "friday":4,
        "saturday":5,
        "sunday":6
    }


    reminder_lower = reminder.lower()


    for day, number in days.items():

        if day in reminder_lower:

            diff = (number - today.weekday()) % 7

            if diff == 0:
                diff = 7


            return (
                today + timedelta(days=diff)
            ).strftime("%Y-%m-%d")



    months = {

        "january":1,
        "february":2,
        "march":3,
        "april":4,
        "may":5,
        "june":6,
        "jul":7,
        "august":8,
        "september":9,
        "october":10,
        "november":11,
        "december":12

    }


    for month, number in months.items():

        if month in reminder_lower:

            day_match = re.search(
                r'\d{1,2}',
                reminder
            )


            if day_match:

                day = int(day_match.group())


                year = today.year


                date = datetime(
                    year,
                    number,
                    day
                )


                if date < today:

                    date = datetime(
                        year + 1,
                        number,
                        day
                    )


                return date.strftime("%Y-%m-%d")


    return ""



# ── Parser ─────────────────────────────────────────────


def create_note(
    text,
    values
):

    note = text


    for item in values:

        if item and item != "Not found":

            note = note.replace(
                item,
                ""
            )


    return re.sub(
        r"\n{3,}",
        "\n\n",
        note
    ).strip()



def parse_lead(text):

    company = extract_company(text)

    email = extract_email(text)

    phone = extract_phone(text)

    address = extract_address(text)

    reminder = extract_reminder(text)

    reminder_date = convert_reminder_to_date(
        reminder
    )


    note = create_note(
        text,
        [
            company,
            email,
            phone,
            address,
            reminder
        ]
    )


    return {

        "company":company,
        "email":email,
        "phone":phone,
        "address":address,
        "reminder":reminder,
        "reminder_date":reminder_date,
        "note":note

    }



# ── Telegram Handler ───────────────────────────────────


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

        data["reminder_date"],

        data["note"]

    )


    await update.message.reply_text(

        "✅ Lead Saved\n\n"

        f"🏢 Company: {data['company']}\n"

        f"📧 Email: {data['email']}\n"

        f"📞 Phone: {data['phone']}\n"

        f"📍 Address: {data['address']}\n"

        f"⏰ Reminder: {data['reminder'] or 'None'}\n"

        f"📅 Date: {data['reminder_date'] or 'None'}\n"

        f"📝 Note: {data['note'] or 'None'}"

    )



# ── Start ──────────────────────────────────────────────


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


    logger.info("Bot is running...")


    app.run_polling()



if __name__ == "__main__":

    threading.Thread(
        target=run_web,
        daemon=True
    ).start()


    run_bot()