import sqlite3
import os


DB_NAME = "leads.db"


def get_connection():
    return sqlite3.connect(DB_NAME)



# ─────────────────────────────────────
# Create Database
# ─────────────────────────────────────

def create_database():

    # Reset old broken database
    # Remove this later after migration is complete
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)


    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER,

            company TEXT,

            email TEXT,

            phone TEXT,

            address TEXT,

            reminder TEXT,

            reminder_date TEXT,

            note TEXT,

            completed INTEGER DEFAULT 0

        )
        """
    )


    conn.commit()

    conn.close()



# ─────────────────────────────────────
# Add Lead
# ─────────────────────────────────────

def add_lead(
    user_id,
    company,
    email,
    phone,
    address,
    reminder,
    reminder_date,
    note
):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute(
        """
        INSERT INTO leads
        (
            user_id,
            company,
            email,
            phone,
            address,
            reminder,
            reminder_date,
            note,
            completed
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)

        """,
        (
            user_id,
            company,
            email,
            phone,
            address,
            reminder,
            reminder_date,
            note
        )
    )


    conn.commit()

    conn.close()



# ─────────────────────────────────────
# Get Reminders
# ─────────────────────────────────────

def get_today_reminders(date):

    conn = get_connection()

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
            reminder_date,
            note,
            user_id

        FROM leads

        WHERE reminder_date = ?

        AND completed = 0

        """,
        (date,)
    )


    results = cursor.fetchall()


    conn.close()


    return results



# ─────────────────────────────────────
# Mark Done
# ─────────────────────────────────────

def mark_done(lead_id):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute(
        """
        UPDATE leads

        SET completed = 1

        WHERE id = ?

        """,
        (lead_id,)
    )


    conn.commit()

    conn.close()



# ─────────────────────────────────────
# Update Reminder Date
# ─────────────────────────────────────

def update_reminder_date(
    lead_id,
    new_date
):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute(
        """
        UPDATE leads

        SET
            reminder_date = ?,
            completed = 0

        WHERE id = ?

        """,
        (
            new_date,
            lead_id
        )
    )


    conn.commit()

    conn.close()



# ─────────────────────────────────────
# Snooze
# ─────────────────────────────────────

def snooze_lead(
    lead_id,
    new_date
):

    update_reminder_date(
        lead_id,
        new_date
    )