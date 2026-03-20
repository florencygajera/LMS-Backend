import sys
sys.path.insert(0, '.')

from core.security import verify_password, get_password_hash

# Test password verification
test_hash = get_password_hash('admin123')
print(f"Test hash generated: {test_hash}")

result = verify_password('admin123', test_hash)
print(f"Password verification result: {result}")

# Now check the database
import sqlite3
conn = sqlite3.connect('agniveer.db')
cursor = conn.cursor()
cursor.execute("SELECT username, hashed_password FROM users LIMIT 3")
users = cursor.fetchall()
print("\nUsers in database:")
for user in users:
    print(f"  {user[0]}: {user[1][:50]}...")

# Test verification with database hash
cursor.execute("SELECT hashed_password FROM users WHERE username = 'admin'")
db_hash = cursor.fetchone()[0]
print(f"\nAdmin hash from DB: {db_hash}")

result = verify_password('admin123', db_hash)
print(f"Verification with DB hash: {result}")
conn.close()
