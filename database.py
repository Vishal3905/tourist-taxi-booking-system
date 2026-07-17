import sqlite3

conn = sqlite3.connect("bookings.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phone TEXT,
    pickup TEXT,
    drop_location TEXT,
    datetime TEXT,
    package_type TEXT,
    passengers INTEGER,
    distance REAL,
    fare REAL
)
""")

conn.commit()
conn.close()

print("Database Created Successfully")