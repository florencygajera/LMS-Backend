"""Migrate data from SQLite to PostgreSQL"""
import sqlite3
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# SQLite connection
sqlite_conn = sqlite3.connect('agniveer.db')
sqlite_cursor = sqlite_conn.cursor()

# Get all tables
sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = sqlite_cursor.fetchall()

print("=" * 50)
print("SQLite Database Analysis")
print("=" * 50)
print(f"Tables found: {len(tables)}\n")

for table in tables:
    table_name = table[0]
    sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = sqlite_cursor.fetchone()[0]
    print(f"  {table_name}: {count} rows")

sqlite_conn.close()
print("\n" + "=" * 50)
print("Migration script ready - run with: python migrate_sqlite_to_postgres.py --execute")
print("=" * 50)
