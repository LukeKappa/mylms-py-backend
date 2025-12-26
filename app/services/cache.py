import logging
import time
from typing import Optional, Any
from app.config import settings

logger = logging.getLogger(__name__)

# Simple in-memory cache
_memory_cache = {}

class CacheService:
    def __init__(self):
        # We could initialize Redis here if needed
        # self.redis = redis.Redis(...)
        pass

    async def get(self, key: str) -> Optional[str]:
        # Check memory cache
        if key in _memory_cache:
            data, expiry = _memory_cache[key]
            if expiry and time.time() > expiry:
                del _memory_cache[key]
                return None
            return data
        return None

    async def set(self, key: str, value: str, ttl: int = 3600):
        expiry = time.time() + ttl if ttl else None
        _memory_cache[key] = (value, expiry)
        
    async def delete(self, key: str):
        if key in _memory_cache:
            del _memory_cache[key]
            
    async def clear(self):
        _memory_cache.clear()
        
    @staticmethod
    def url_hash(url: str) -> str:
        import hashlib
        return hashlib.md5(url.encode()).hexdigest()

# Singleton instance
cache = CacheService()
