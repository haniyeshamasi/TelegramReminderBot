import sqlite3
import os

from datetime import datetime

from telegram import Bot


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
            company,
            email,
            phone,
            address,
            reminder,
            note,
            user_id

        FROM leads

        WHERE reminder_date = ?

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


        await bot.send_message(
            chat_id=user_id,
            text=message
        )