"""
Distributed Cache Layer
Agniveer Sentinel - Enterprise Production
"""

import redis.asyncio as redis
import json
import os
from typing import Optional, Any
from datetime import timedelta
import hashlib


class CacheManager:
    """Redis distributed cache manager"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.is_connected = False
    
    async def connect(self):
        """Connect to Redis"""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.redis_client = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            self.is_connected = True
            print("Connected to Redis cache")
        except Exception as e:
            print(f"Redis connection failed: {e}")
            self.is_connected = False
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            self.is_connected = False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.is_connected:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            print(f"Cache get error: {e}")
        
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache with TTL"""
        if not self.is_connected:
            return False
        
        try:
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(value)
            )
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str):
        """Delete key from cache"""
        if not self.is_connected:
            return
        
        try:
            await self.redis_client.delete(key)
        except Exception as e:
            print(f"Cache delete error: {e}")
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        if not self.is_connected:
            return
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
        except Exception as e:
            print(f"Cache invalidate error: {e}")
    
    def generate_key(self, prefix: str, *args) -> str:
        """Generate cache key from arguments"""
        key_parts = [prefix] + [str(arg) for arg in args]
        return ":".join(key_parts)


# Cache manager instance
cache_manager = CacheManager()


# Cache decorators
def cached(prefix: str, ttl: int = 3600):
    """Decorator for caching function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key_args = tuple(kwargs.values())
            cache_key = cache_manager.generate_key(prefix, *key_args)
            
            # Try to get from cache
            cached_value = await cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


class CacheService:
    """Specific cache services for different data types"""
    
    # Leaderboard cache
    LEADERBOARD_TTL = 3600  # 1 hour
    LEADERBOARD_PREFIX = "leaderboard"
    
    # Soldier profile cache
    SOLDIER_PROFILE_TTL = 1800  # 30 minutes
    SOLDIER_PROFILE_PREFIX = "soldier_profile"
    
    # Exam questions cache
    EXAM_QUESTIONS_TTL = 86400  # 24 hours
    EXAM_QUESTIONS_PREFIX = "exam_questions"
    
    # Weather cache
    WEATHER_TTL = 900  # 15 minutes
    WEATHER_PREFIX = "weather"
    
    # Training records cache
    TRAINING_TTL = 600  # 10 minutes
    TRAINING_PREFIX = "training_records"
    
    @staticmethod
    async def get_leaderboard(battalion_id: int, month: int, year: int):
        """Get cached leaderboard"""
        key = cache_manager.generate_key(
            CacheService.LEADERBOARD_PREFIX,
            battalion_id, month, year
        )
        return await cache_manager.get(key)
    
    @staticmethod
    async def set_leaderboard(battalion_id: int, month: int, year: int, data: Any):
        """Cache leaderboard"""
        key = cache_manager.generate_key(
            CacheService.LEADERBOARD_PREFIX,
            battalion_id, month, year
        )
        await cache_manager.set(key, data, CacheService.LEADERBOARD_TTL)
    
    @staticmethod
    async def invalidate_leaderboard(battalion_id: int = None):
        """Invalidate leaderboard cache"""
        if battalion_id:
            await cache_manager.invalidate_pattern(f"{CacheService.LEADERBOARD_PREFIX}:{battalion_id}:*")
        else:
            await cache_manager.invalidate_pattern(f"{CacheService.LEADERBOARD_PREFIX}:*")
    
    @staticmethod
    async def get_soldier_profile(soldier_id: int):
        """Get cached soldier profile"""
        key = cache_manager.generate_key(CacheService.SOLDIER_PROFILE_PREFIX, soldier_id)
        return await cache_manager.get(key)
    
    @staticmethod
    async def set_soldier_profile(soldier_id: int, data: Any):
        """Cache soldier profile"""
        key = cache_manager.generate_key(CacheService.SOLDIER_PROFILE_PREFIX, soldier_id)
        await cache_manager.set(key, data, CacheService.SOLDIER_PROFILE_TTL)
    
    @staticmethod
    async def invalidate_soldier_profile(soldier_id: int):
        """Invalidate soldier profile cache"""
        key = cache_manager.generate_key(CacheService.SOLDIER_PROFILE_PREFIX, soldier_id)
        await cache_manager.delete(key)
    
    @staticmethod
    async def get_weather(location: str):
        """Get cached weather data"""
        key = cache_manager.generate_key(CacheService.WEATHER_PREFIX, location)
        return await cache_manager.get(key)
    
    @staticmethod
    async def set_weather(location: str, data: Any):
        """Cache weather data"""
        key = cache_manager.generate_key(CacheService.WEATHER_PREFIX, location)
        await cache_manager.set(key, data, CacheService.WEATHER_TTL)
    
    @staticmethod
    async def get_exam_questions(exam_id: int):
        """Get cached exam questions"""
        key = cache_manager.generate_key(CacheService.EXAM_QUESTIONS_PREFIX, exam_id)
        return await cache_manager.get(key)
    
    @staticmethod
    async def set_exam_questions(exam_id: int, data: Any):
        """Cache exam questions"""
        key = cache_manager.generate_key(CacheService.EXAM_QUESTIONS_PREFIX, exam_id)
        await cache_manager.set(key, data, CacheService.EXAM_QUESTIONS_TTL)


# Cache warming functions
async def warm_cache():
    """Warm up frequently accessed data"""
    # This would be called on application startup
    # Pre-load frequently accessed data into cache
    print("Warming up cache...")
    # Implementation would query database and cache popular data


