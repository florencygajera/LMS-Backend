"""Check tables in SQLite database"""
import sqlite3

conn = sqlite3.connect('agniveer.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = cursor.fetchall()

print('Tables created:')
for table in tables:
    print(f'  - {table[0]}')
print(f'\nTotal: {len(tables)} tables')
conn.close()
