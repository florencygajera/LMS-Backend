"""Debug init_db to see what's happening"""
import asyncio
import logging

logging.basicConfig(level=logging.INFO)

async def main():
    # Force PostgreSQL mode (no SQLite fallback)
    import os
    os.environ.pop('USE_SQLITE', None)
    
    from common.core import database
    from common.core.database import init_db, import_models, _test_connection
    
    # First test connection
    print("Testing PostgreSQL connection...")
    result = await _test_connection('postgresql+asyncpg://postgres:postgres@localhost:5432/agniveer_db')
    print(f"Connection test result: {result}")
    
    # Now init
    print("\nRunning init_db...")
    db_url = await init_db()
    print(f"Database URL: {db_url}")

asyncio.run(main())
