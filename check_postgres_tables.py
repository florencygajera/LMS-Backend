"""Check PostgreSQL tables"""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def check_tables():
    postgres_url = 'postgresql+asyncpg://postgres:postgres@localhost:5432/agniveer_db'
    engine = create_async_engine(postgres_url, echo=False)
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = result.fetchall()
        print('Tables in PostgreSQL:')
        for t in tables:
            print(f'  {t[0]}')
    await engine.dispose()

asyncio.run(check_tables())
