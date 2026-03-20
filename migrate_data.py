"""Migrate data from SQLite to PostgreSQL"""
import sqlite3
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Configuration
SQLITE_DB = 'agniveer.db'
POSTGRES_URL = 'postgresql+asyncpg://postgres:postgres@localhost:5432/agniveer_db'

def get_sqlite_data():
    """Fetch all data from SQLite database"""
    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    
    data = {}
    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        if rows:
            # Get column names
            columns = [description[0] for description in cursor.description]
            data[table] = {
                'columns': columns,
                'rows': [dict(row) for row in rows]
            }
        else:
            data[table] = {'columns': [], 'rows': []}
    
    conn.close()
    return data

async def migrate_to_postgres(data):
    """Insert data into PostgreSQL"""
    engine = create_async_engine(POSTGRES_URL, echo=False)
    
    async with engine.begin() as conn:
        for table_name, table_data in data.items():
            if not table_data['rows']:
                print(f"  Skipping {table_name} (no data)")
                continue
            
            columns = table_data['columns']
            placeholders = ', '.join([f'${i+1}' for i in range(len(columns))])
            column_names = ', '.join(columns)
            
            insert_sql = text(f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})")
            
            for row in table_data['rows']:
                # Convert values - handle special types
                values = []
                for col in columns:
                    val = row.get(col)
                    # Handle None and special values
                    if val is None:
                        values.append(None)
                    elif isinstance(val, (int, float, str)):
                        values.append(val)
                    else:
                        values.append(str(val))
                
                try:
                    await conn.execute(insert_sql, values)
                except Exception as e:
                    print(f"  Error inserting into {table_name}: {e}")
                    raise
    
    await engine.dispose()

async def verify_migration(data):
    """Verify data was migrated"""
    engine = create_async_engine(POSTGRES_URL, echo=False)
    
    print("\n" + "=" * 50)
    print("Verification - Comparing row counts")
    print("=" * 50)
    
    async with engine.connect() as conn:
        for table_name, table_data in data.items():
            if not table_data['rows']:
                continue
            
            sqlite_count = len(table_data['rows'])
            result = await conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            pg_count = result.scalar()
            
            status = "OK" if sqlite_count == pg_count else "MISMATCH"
            print(f"  {table_name}: SQLite={sqlite_count}, PG={pg_count} [{status}]")
    
    await engine.dispose()

async def main():
    print("=" * 50)
    print("Migrating SQLite to PostgreSQL")
    print("=" * 50)
    
    # Step 1: Get SQLite data
    print("\n1. Reading SQLite data...")
    data = get_sqlite_data()
    total_rows = sum(len(td['rows']) for td in data.values())
    print(f"   Found {len(data)} tables with {total_rows} total rows")
    
    # Step 2: Migrate data
    print("\n2. Migrating data to PostgreSQL...")
    for table_name, table_data in data.items():
        if table_data['rows']:
            print(f"   {table_name}: {len(table_data['rows'])} rows")
    
    await migrate_to_postgres(data)
    print("   Migration complete!")
    
    # Step 3: Verify
    await verify_migration(data)

if __name__ == "__main__":
    asyncio.run(main())
