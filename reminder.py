import sqlite3
import os

from datetime import datetime

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup


DB_NAME = "leads.db"

TOKEN = os.getenv("BOT_TOKEN")


bot = Bot(
    token=TOKEN
)



def get_today_reminders():

    today = datetime.now().strftime("%Y-%m-%d")


    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT
            id,
            company,
            email,
            phone,
            address,
            reminder,
            note,
            user_id

        FROM leads

        WHERE reminder_date = ?
        AND completed = 0

        """,
        (today,)
    )


    leads = cursor.fetchall()


    conn.close()


    return leads




async def send_reminders():


    leads = get_today_reminders()


    for lead in leads:


        (
            lead_id,
            company,
            email,
            phone,
            address,
            reminder,
            note,
            user_id

        ) = lead



        message = f"""
🔔 Reminder Today

🏢 Company:
{company}

📧 Email:
{email}

📞 Phone:
{phone}

📍 Address:
{address}

⏰ Reminder:
{reminder}

📝 Note:
{note}
"""


        keyboard = [

            [
                InlineKeyboardButton(
                    "✅ Done",
                    callback_data=f"done_{lead_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    "⏰ Snooze",
                    callback_data=f"snooze_{lead_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    "📅 Change Date",
                    callback_data=f"date_{lead_id}"
                )
            ]

        ]


        reply_markup = InlineKeyboardMarkup(
            keyboard
        )


        await bot.send_message(
            chat_id=user_id,
            text=message,
            reply_markup=reply_markup
        )