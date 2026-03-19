"""Script to create SQLite database tables"""
import os
os.environ['USE_SQLITE'] = 'true'

from common.core.database import import_models, Base, get_db_engine
import asyncio

async def create_db():
    # Import all models to register them with Base.metadata
    import_models()
    
    engine = get_db_engine()
    print(f'Using database: {engine.url}')
    print(f'Tables to create: {list(Base.metadata.tables.keys())}')
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('Database tables created successfully!')

asyncio.run(create_db())
