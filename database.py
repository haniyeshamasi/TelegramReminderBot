import sqlite3

DB_NAME = "leads.db"


def create_database():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
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

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)

    conn.commit()
    conn.close()



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

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()


    cursor.execute("""
    INSERT INTO leads
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

    VALUES (?, ?, ?, ?, ?, ?, ?, ?)

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
    ))


    conn.commit()
    conn.close()