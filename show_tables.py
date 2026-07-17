import sqlite3

conn = sqlite3.connect("bookings.db")
cursor = conn.cursor()

tables = ["bookings", "drivers", "vehicles"]

for table in tables:

    print("\n" + "=" * 50)
    print("TABLE:", table.upper())
    print("=" * 50)

    cursor.execute(f"SELECT * FROM {table}")

    rows = cursor.fetchall()

    for row in rows:
        print(row)

conn.close()