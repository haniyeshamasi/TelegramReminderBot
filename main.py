import re
import os
import logging
import threading

from datetime import datetime, timedelta, time
from reminder import send_reminders
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


# ─────────────────────────────────────
# Logging
# ─────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────
# Config
# ─────────────────────────────────────

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise EnvironmentError("BOT_TOKEN missing")


# ─────────────────────────────────────
# Flask keep alive (Render)
# ─────────────────────────────────────

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



# ─────────────────────────────────────
# Extractors
# ─────────────────────────────────────

def extract_email(text):

    match = re.search(
        r"[\w\.-]+@[\w\.-]+\.\w+",
        text,
        re.IGNORECASE
    )

    return match.group().strip() if match else "Not found"



def extract_phone(text):

    match = re.search(
        r"\b(?:\+?1[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}\b",
        text
    )

    return match.group().strip() if match else "Not found"



def extract_address(text):

    pattern = (
        r"\d{1,6}\s+"
        r"[A-Za-z0-9\s\.\-]+"
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
            text.strip()
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



# ─────────────────────────────────────
# Reminder extraction
# ─────────────────────────────────────

def extract_reminder(text):

    patterns = [

        # Relative time
        r'\bin\s+\d+\s+(?:minute|minutes|hour|hours|day|days|week|weeks|month|months|year|years)\b',

        r'\bin\s+(?:a|an)\s+(?:day|week|month|year)\b',

        r'\b(?:tomorrow|today|tonight|next week|next month|next year)\b',


        # Weekdays
        r'\b(?:next\s+)?(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',


        # Dates
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


    return found



# ─────────────────────────────────────
# Convert reminder text to date
# ─────────────────────────────────────

def convert_reminder_to_date(reminder):

    if not reminder:
        return ""


    today = datetime.now()

    reminder_lower = reminder.lower()


    # Simple relative-day keywords
    # (FIX: these were matched by extract_reminder but never
    # handled here, so "tomorrow" / "today" / "tonight" /
    # "next week" / "next month" / "next year" always produced
    # an empty reminder_date.)

    if "tomorrow" in reminder_lower:

        return (today + timedelta(days=1)).strftime("%Y-%m-%d")


    if "today" in reminder_lower or "tonight" in reminder_lower:

        return today.strftime("%Y-%m-%d")


    if "next week" in reminder_lower:

        return (today + timedelta(weeks=1)).strftime("%Y-%m-%d")


    if "next month" in reminder_lower:

        return (today + timedelta(days=30)).strftime("%Y-%m-%d")


    if "next year" in reminder_lower:

        return (today + timedelta(days=365)).strftime("%Y-%m-%d")


    # in X days/weeks/months/years

    relative = re.search(
        r"in\s+(\d+)\s+(day|days|week|weeks|month|months|year|years)",
        reminder_lower
    )


    if relative:

        number = int(relative.group(1))

        unit = relative.group(2)


        if "day" in unit:

            date = today + timedelta(days=number)


        elif "week" in unit:

            date = today + timedelta(weeks=number)


        elif "month" in unit:

            date = today + timedelta(days=number * 30)


        else:

            date = today + timedelta(days=number * 365)


        return date.strftime("%Y-%m-%d")



    # weekdays

    days = {

        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6

    }


    for day, index in days.items():

        if day in reminder_lower:

            difference = (
                index - today.weekday()
            ) % 7


            if difference == 0:
                difference = 7


            date = today + timedelta(
                days=difference
            )


            return date.strftime("%Y-%m-%d")



    # Month + day

    months = {

        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12

    }


    for month, number in months.items():

        if month in reminder_lower:

            day_match = re.search(
                r"\d{1,2}",
                reminder
            )


            if day_match:

                day = int(day_match.group())


                date = datetime(
                    today.year,
                    number,
                    day
                )


                if date < today:

                    date = datetime(
                        today.year + 1,
                        number,
                        day
                    )


                return date.strftime("%Y-%m-%d")


    return ""



# ─────────────────────────────────────
# Parser
# ─────────────────────────────────────

def create_note(text, remove_items):

    note = text


    for item in remove_items:

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



def parse_lead(text):

    company = extract_company(text)

    email = extract_email(text)

    phone = extract_phone(text)

    address = extract_address(text)

    reminder_matches = extract_reminder(text)

    reminder = ", ".join(reminder_matches)

    reminder_date = convert_reminder_to_date(
        reminder
    )


    # FIX: previously passed the joined "a, b" string as a single
    # removal item, which almost never matches a literal substring
    # of the original text, so reminder phrases were left in the
    # note. Now each matched phrase is removed individually.

    note = create_note(
        text,
        [
            company,
            email,
            phone,
            address,
            *reminder_matches
        ]
    )


    return {

        "company": company,
        "email": email,
        "phone": phone,
        "address": address,
        "reminder": reminder,
        "reminder_date": reminder_date,
        "note": note

    }



# ─────────────────────────────────────
# Telegram handler
# ─────────────────────────────────────

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



# ─────────────────────────────────────
# Run
# ─────────────────────────────────────

def run_bot():

    create_database()


    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .build()
    )


    async def reminder_job(context):

        await send_reminders()


    app.job_queue.run_daily(
        reminder_job,
        time=time(
            hour=9,
            minute=0
        )
    )


    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            add_lead_message
        )
    )


    logger.info("Reminder system started")
    logger.info("Bot is running...")

    # FIX: removed the duplicated logger.info(...) + app.run_polling()
    # block that was pasted twice at the end of this function. Since
    # run_polling() blocks, the second copy was dead code, but it's
    # gone now for clarity.

    app.run_polling()



if __name__ == "__main__":

    threading.Thread(
        target=run_web,
        daemon=True
    ).start()


    run_bot()