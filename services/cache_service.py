"""
Cache Service - Multi-tier caching with Redis and file fallback
"""

import os
import json
import logging
from typing import Optional, Any
import redis.asyncio as redis
import aiofiles
from pathlib import Path

logger = logging.getLogger(__name__)


class CacheService:
    """Service for caching API responses"""
    
    def __init__(self):
        self.redis_client = None
        self.redis_enabled = False
        self.redis_connection_tested = False
        self.cache_dir = Path(os.getenv("CACHE_DIR", "./cache"))
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize Redis only if explicitly configured
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                # Note: Connection is tested lazily on first use
                logger.info("Redis cache configured (will test connection on first use)")
            except Exception as e:
                logger.warning(f"Redis configuration error, using file cache: {str(e)}")
                self.redis_client = None
        else:
            logger.info("Redis not configured, using file cache only")
    
    async def _test_redis_connection(self):
        """Test Redis connection and enable/disable accordingly"""
        if self.redis_connection_tested:
            return
        
        self.redis_connection_tested = True
        
        if not self.redis_client:
            self.redis_enabled = False
            return
        
        try:
            # Test connection by pinging Redis
            await self.redis_client.ping()
            self.redis_enabled = True
            logger.info("Redis cache enabled and connected")
        except Exception as e:
            self.redis_enabled = False
            logger.info(f"Redis not available, using file cache only: {str(e)}")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        # Test Redis connection on first use
        await self._test_redis_connection()
        
        # Try Redis first
        if self.redis_enabled and self.redis_client:
            try:
                value = await self.redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.warning(f"Redis get error: {str(e)}")
                # Disable Redis on persistent errors
                self.redis_enabled = False
        
        # Fallback to file cache
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                async with aiofiles.open(cache_file, 'r') as f:
                    content = await f.read()
                    return json.loads(content)
            except Exception as e:
                logger.warning(f"File cache read error: {str(e)}")
        
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        # Test Redis connection on first use
        await self._test_redis_connection()
        
        json_value = json.dumps(value)
        
        # Try Redis first
        if self.redis_enabled and self.redis_client:
            try:
                await self.redis_client.setex(key, ttl, json_value)
                return True
            except Exception as e:
                logger.warning(f"Redis set error: {str(e)}")
        
        # Fallback to file cache (no TTL for files)
        cache_file = self.cache_dir / f"{key}.json"
        try:
            async with aiofiles.open(cache_file, 'w') as f:
                await f.write(json_value)
            return True
        except Exception as e:
            logger.error(f"File cache write error: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if successful
        """
        success = True
        
        # Delete from Redis
        if self.redis_enabled and self.redis_client:
            try:
                await self.redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Redis delete error: {str(e)}")
                success = False
        
        # Delete from file cache
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                cache_file.unlink()
            except Exception as e:
                logger.warning(f"File cache delete error: {str(e)}")
                success = False
        
        return success
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()

