import sqlite3

DB_NAME = "leads.db"


def create_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        email TEXT,
        phone TEXT,
        note TEXT,
        status TEXT DEFAULT 'new',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def add_lead(user_id, email, phone, reminder, raw_text):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO leads
    (user_id, email, phone, note)
    VALUES (?, ?, ?, ?)
    """,
    (
        user_id,
        email,
        phone,
        reminder + "\n" + raw_text
    ))

    conn.commit()
    conn.close()