"""Simple test to verify database persistence with SQLite"""
import os
os.environ['USE_SQLITE'] = 'true'

import asyncio
from common.core.database import import_models, get_db_engine, get_async_session_local
from common.core.config import settings

# Import models
import_models()

async def test_db():
    print(f"Database URL: {settings.DATABASE_URL}")
    
    # Get the session factory
    session_factory = get_async_session_local()
    
    # Test inserting a user
    from services.auth_service.models.user import User
    from common.models.base import UserRole
    
    async with session_factory() as session:
        # Create a test user
        user = User(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            hashed_password="hashed",
            role=UserRole.CANDIDATE,
            is_active=True
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        print(f"Created user with ID: {user.id}, UUID: {user.uuid}")
        
        # Query it back
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.email == "test@example.com"))
        fetched_user = result.scalar_one_or_none()
        
        if fetched_user:
            print(f"Successfully retrieved user: {fetched_user.username}")
        else:
            print("ERROR: User not found!")
    
    print("\nDatabase persistence test PASSED!")

asyncio.run(test_db())
