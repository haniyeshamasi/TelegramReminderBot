import sqlite3

DB_NAME = "leads_v5.db"


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
        note
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
    (
        user_id,
        company,
        email,
        phone,
        address,
        reminder,
        note
    ))

    conn.commit()
    conn.close()