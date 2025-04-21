import sqlite3

conn = sqlite3.connect('tpo.db')
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables:", tables)

# Check data in student_profile
cursor.execute("SELECT * FROM student_profile;")
rows = cursor.fetchall()
print("Data in student_profile:", rows)

conn.close()
