import sqlite3

DB_NAME = "reminders.db"


def create_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        message TEXT,
        remind_time TEXT,
        done INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


def add_reminder(user_id, message, remind_time):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO reminders (user_id, message, remind_time)
    VALUES (?, ?, ?)
    """, (user_id, message, remind_time))

    conn.commit()
    conn.close()