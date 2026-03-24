"""
💾 ADVANCED CACHE MANAGER
Redis-based caching with TTL, compression, and smart invalidation
"""

import json
import hashlib
import zlib
from typing import Any, Optional, Dict
from datetime import timedelta
import asyncio
from utils.logger import logger

# Try Redis first, fallback to in-memory
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("⚠️ Redis not installed. Using in-memory cache. Install: pip install redis")


class CacheManager:
    """
    💾 ENTERPRISE CACHE MANAGER
    
    Features:
    - Redis backend (distributed)
    - In-memory fallback
    - Automatic compression
    - TTL support
    - Cache tags for bulk invalidation
    - Analytics
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.memory_cache: Dict[str, tuple] = {}  # (value, expires_at)
        self.use_redis = False
        
        # Stats
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }
        
        logger.info("💾 CacheManager initialized")
    
    async def connect(self):
        """Connect to Redis"""
        if not REDIS_AVAILABLE:
            logger.info("📋 Using in-memory cache (Redis not available)")
            return
        
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            
            # Test connection
            await self.redis_client.ping()
            self.use_redis = True
            logger.info("✅ Connected to Redis")
            
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}. Using in-memory cache.")
            self.use_redis = False
    
    def _generate_key(self, namespace: str, key: str) -> str:
        """Generate cache key with namespace"""
        return f"aiops:{namespace}:{key}"
    
    def _hash_key(self, data: Any) -> str:
        """Generate hash for complex data"""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(json_str.encode()).hexdigest()
    
    def _compress(self, data: bytes) -> bytes:
        """Compress data if larger than 1KB"""
        if len(data) > 1024:
            return zlib.compress(data)
        return data
    
    def _decompress(self, data: bytes) -> bytes:
        """Decompress data"""
        try:
            return zlib.decompress(data)
        except zlib.error:
            return data  # Not compressed
    
    async def get(
        self, 
        namespace: str, 
        key: str,
        default: Any = None
    ) -> Optional[Any]:
        """
        Get cached value
        
        Args:
            namespace: Cache namespace (e.g., 'query', 'weather')
            key: Cache key
            default: Default value if not found
        """
        cache_key = self._generate_key(namespace, key)
        
        try:
            if self.use_redis and self.redis_client:
                # Redis backend
                data = await self.redis_client.get(cache_key)
                
                if data:
                    self.stats["hits"] += 1
                    
                    # Decompress and deserialize
                    decompressed = self._decompress(data)
                    value = json.loads(decompressed.decode('utf-8'))
                    
                    logger.debug(f"💾 Cache HIT: {namespace}:{key}")
                    return value
                
            else:
                # In-memory backend
                import time
                
                if cache_key in self.memory_cache:
                    value, expires_at = self.memory_cache[cache_key]
                    
                    if expires_at is None or expires_at > time.time():
                        self.stats["hits"] += 1
                        logger.debug(f"💾 Cache HIT (memory): {namespace}:{key}")
                        return value
                    else:
                        # Expired
                        del self.memory_cache[cache_key]
            
            # Cache miss
            self.stats["misses"] += 1
            logger.debug(f"💾 Cache MISS: {namespace}:{key}")
            return default
            
        except Exception as e:
            logger.error(f"❌ Cache get error: {e}")
            self.stats["errors"] += 1
            return default
    
    async def set(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl: int = 3600,  # 1 hour default
        tags: list = None
    ) -> bool:
        """
        Set cache value
        
        Args:
            namespace: Cache namespace
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            tags: Tags for bulk invalidation
        """
        cache_key = self._generate_key(namespace, key)
        
        try:
            # Serialize and compress
            json_data = json.dumps(value).encode('utf-8')
            compressed = self._compress(json_data)
            
            if self.use_redis and self.redis_client:
                # Redis backend
                await self.redis_client.setex(
                    cache_key,
                    ttl,
                    compressed
                )
                
                # Store tags
                if tags:
                    for tag in tags:
                        tag_key = self._generate_key("tags", tag)
                        await self.redis_client.sadd(tag_key, cache_key)
                        await self.redis_client.expire(tag_key, ttl)
                
            else:
                # In-memory backend
                import time
                expires_at = time.time() + ttl if ttl else None
                self.memory_cache[cache_key] = (value, expires_at)
            
            self.stats["sets"] += 1
            logger.debug(f"💾 Cache SET: {namespace}:{key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Cache set error: {e}")
            self.stats["errors"] += 1
            return False
    
    async def delete(self, namespace: str, key: str) -> bool:
        """Delete cache entry"""
        cache_key = self._generate_key(namespace, key)
        
        try:
            if self.use_redis and self.redis_client:
                await self.redis_client.delete(cache_key)
            else:
                self.memory_cache.pop(cache_key, None)
            
            self.stats["deletes"] += 1
            logger.debug(f"💾 Cache DELETE: {namespace}:{key}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Cache delete error: {e}")
            return False
    
    async def invalidate_by_tag(self, tag: str) -> int:
        """Invalidate all cache entries with a specific tag"""
        if not self.use_redis or not self.redis_client:
            logger.warning("⚠️ Tag-based invalidation only works with Redis")
            return 0
        
        try:
            tag_key = self._generate_key("tags", tag)
            keys = await self.redis_client.smembers(tag_key)
            
            if keys:
                await self.redis_client.delete(*keys)
                await self.redis_client.delete(tag_key)
                
                count = len(keys)
                logger.info(f"💾 Invalidated {count} cache entries with tag '{tag}'")
                return count
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ Tag invalidation error: {e}")
            return 0
    
    async def clear_all(self, namespace: str = None) -> bool:
        """Clear all cache or specific namespace"""
        try:
            if self.use_redis and self.redis_client:
                if namespace:
                    pattern = self._generate_key(namespace, "*")
                    cursor = 0
                    
                    while True:
                        cursor, keys = await self.redis_client.scan(
                            cursor=cursor,
                            match=pattern,
                            count=100
                        )
                        
                        if keys:
                            await self.redis_client.delete(*keys)
                        
                        if cursor == 0:
                            break
                else:
                    await self.redis_client.flushdb()
            else:
                if namespace:
                    prefix = f"aiops:{namespace}:"
                    self.memory_cache = {
                        k: v for k, v in self.memory_cache.items()
                        if not k.startswith(prefix)
                    }
                else:
                    self.memory_cache.clear()
            
            logger.info(f"💾 Cache cleared: {namespace or 'ALL'}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Cache clear error: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.stats,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "backend": "redis" if self.use_redis else "memory",
            "memory_size": len(self.memory_cache) if not self.use_redis else None
        }
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("💾 Cache connection closed")


# ============ SINGLETON ============
_cache_manager: Optional[CacheManager] = None


async def get_cache_manager() -> CacheManager:
    """Get or create cache manager instance"""
    global _cache_manager
    
    if _cache_manager is None:
        import os
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _cache_manager = CacheManager(redis_url)
        await _cache_manager.connect()
    
    return _cache_manager


# ============ DECORATOR ============
def cached(namespace: str, ttl: int = 3600, key_func: callable = None):
    """
    Decorator for caching function results
    
    Usage:
        @cached("weather", ttl=600)
        async def get_weather(city: str):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache = await get_cache_manager()
            
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Use function args as key
                key_parts = [str(arg) for arg in args]
                key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
                cache_key = ":".join(key_parts) or "default"
            
            # Try cache
            cached_value = await cache.get(namespace, cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache.set(namespace, cache_key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator