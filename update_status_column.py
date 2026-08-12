import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("ALTER TABLE reports ADD COLUMN status TEXT DEFAULT 'Pending'")

conn.commit()
conn.close()

print("Status column added successfully!")