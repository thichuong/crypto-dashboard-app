"""
Enhanced Cache System với Redis và fallback strategies
"""
from flask_caching import Cache
import json
import os
import redis
import pickle
from datetime import datetime, timedelta
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Khởi tạo cache objects
cache = Cache()
_memory_cache = {}
_redis_client = None

class CacheStrategy:
    """Enum cho cache strategies"""
    REDIS_ONLY = "redis_only"
    MEMORY_ONLY = "memory_only"
    HYBRID = "hybrid"
    FILE_BACKUP = "file_backup"

def init_redis():
    """Khởi tạo Redis client"""
    global _redis_client
    
    redis_url = os.getenv('REDIS_URL')
    if redis_url:
        try:
            _redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            # Test connection
            _redis_client.ping()
            logger.info("Redis connection established successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            _redis_client = None
            return False
    return False

def is_redis_available():
    """Kiểm tra Redis có sẵn không"""
    return _redis_client is not None

class EnhancedCache:
    """Enhanced cache với multiple strategies và automatic failover"""
    
    def __init__(self, strategy=CacheStrategy.HYBRID):
        self.strategy = strategy
        self.backup_dir = "instance/backup_cache"
        self._ensure_backup_dir()
    
    def _ensure_backup_dir(self):
        """Tạo backup directory nếu cần"""
        if not os.path.exists(self.backup_dir):
            try:
                os.makedirs(self.backup_dir, exist_ok=True)
            except OSError:
                logger.warning("Cannot create backup cache directory")
    
    def set(self, key, data, timeout=3600, namespace="default"):
        """
        Set cache với multiple strategies
        Args:
            key: cache key
            data: dữ liệu cần cache
            timeout: thời gian expire (giây)
            namespace: namespace để tránh conflict keys
        """
        cache_key = f"{namespace}:{key}"
        
        success_count = 0
        
        # Redis cache (primary)
        if is_redis_available() and self.strategy != CacheStrategy.MEMORY_ONLY:
            try:
                serialized = json.dumps(data, ensure_ascii=False)
                _redis_client.setex(cache_key, timeout, serialized)
                success_count += 1
                logger.debug(f"Redis cache set: {cache_key}")
            except Exception as e:
                logger.warning(f"Redis cache set failed: {e}")
        
        # Memory cache (secondary)
        if self.strategy in [CacheStrategy.MEMORY_ONLY, CacheStrategy.HYBRID]:
            try:
                expire_time = datetime.now() + timedelta(seconds=timeout)
                _memory_cache[cache_key] = {
                    "data": data,
                    "expires_at": expire_time
                }
                success_count += 1
                logger.debug(f"Memory cache set: {cache_key}")
            except Exception as e:
                logger.warning(f"Memory cache set failed: {e}")
        
        # File backup (tertiary)
        if self.strategy == CacheStrategy.FILE_BACKUP:
            try:
                cache_data = {
                    "data": data,
                    "expires_at": (datetime.now() + timedelta(seconds=timeout)).isoformat()
                }
                cache_file = os.path.join(self.backup_dir, f"{key}.json")
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                success_count += 1
                logger.debug(f"File cache set: {cache_key}")
            except Exception as e:
                logger.warning(f"File cache set failed: {e}")
        
        return success_count > 0
    
    def get(self, key, namespace="default"):
        """
        Get cache với automatic fallback
        """
        cache_key = f"{namespace}:{key}"
        
        # Try Redis first (fastest for production)
        if is_redis_available() and self.strategy != CacheStrategy.MEMORY_ONLY:
            try:
                cached = _redis_client.get(cache_key)
                if cached:
                    data = json.loads(cached)
                    logger.debug(f"Redis cache hit: {cache_key}")
                    return data
            except Exception as e:
                logger.warning(f"Redis cache get failed: {e}")
        
        # Try memory cache
        if self.strategy in [CacheStrategy.MEMORY_ONLY, CacheStrategy.HYBRID]:
            try:
                if cache_key in _memory_cache:
                    cache_data = _memory_cache[cache_key]
                    if datetime.now() <= cache_data["expires_at"]:
                        logger.debug(f"Memory cache hit: {cache_key}")
                        return cache_data["data"]
                    else:
                        # Expired, remove
                        del _memory_cache[cache_key]
            except Exception as e:
                logger.warning(f"Memory cache get failed: {e}")
        
        # Try file backup
        if self.strategy == CacheStrategy.FILE_BACKUP:
            try:
                cache_file = os.path.join(self.backup_dir, f"{key}.json")
                if os.path.exists(cache_file):
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    expires_at = datetime.fromisoformat(cache_data["expires_at"])
                    if datetime.now() <= expires_at:
                        logger.debug(f"File cache hit: {cache_key}")
                        return cache_data["data"]
            except Exception as e:
                logger.warning(f"File cache get failed: {e}")
        
        logger.debug(f"Cache miss: {cache_key}")
        return None
    
    def delete(self, key, namespace="default"):
        """Delete từ tất cả cache layers"""
        cache_key = f"{namespace}:{key}"
        
        # Redis
        if is_redis_available():
            try:
                _redis_client.delete(cache_key)
            except Exception as e:
                logger.warning(f"Redis cache delete failed: {e}")
        
        # Memory
        try:
            if cache_key in _memory_cache:
                del _memory_cache[cache_key]
        except Exception as e:
            logger.warning(f"Memory cache delete failed: {e}")
        
        # File
        try:
            cache_file = os.path.join(self.backup_dir, f"{key}.json")
            if os.path.exists(cache_file):
                os.remove(cache_file)
        except Exception as e:
            logger.warning(f"File cache delete failed: {e}")
    
    def clear_expired(self):
        """Cleanup expired entries từ memory cache"""
        now = datetime.now()
        expired_keys = []
        
        for key, data in _memory_cache.items():
            try:
                if now > data["expires_at"]:
                    expired_keys.append(key)
            except Exception:
                expired_keys.append(key)
        
        for key in expired_keys:
            try:
                del _memory_cache[key]
            except Exception:
                pass
        
        logger.info(f"Cleared {len(expired_keys)} expired cache entries")

# Smart caching decorator
def smart_cache(timeout=300, key_prefix="", strategy=CacheStrategy.HYBRID):
    """
    Decorator for intelligent caching với automatic fallback
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            import hashlib
            func_key = f"{func.__module__}.{func.__name__}"
            args_key = str(args) + str(sorted(kwargs.items()))
            cache_key = hashlib.md5(f"{key_prefix}{func_key}{args_key}".encode()).hexdigest()
            
            # Try cache first
            enhanced_cache = EnhancedCache(strategy)
            cached_result = enhanced_cache.get(cache_key, namespace="smart_cache")
            
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            enhanced_cache.set(cache_key, result, timeout, namespace="smart_cache")
            
            return result
        return wrapper
    return decorator

# Backup cache functions (backward compatibility)
def set_backup_cache(key, data, max_age_hours=24):
    """Backward compatible function"""
    enhanced_cache = EnhancedCache(CacheStrategy.HYBRID)
    return enhanced_cache.set(key, data, timeout=max_age_hours * 3600, namespace="backup")

def get_backup_cache(key):
    """Backward compatible function"""
    enhanced_cache = EnhancedCache(CacheStrategy.HYBRID)
    return enhanced_cache.get(key, namespace="backup")

# Performance monitoring
class CacheStats:
    """Cache performance monitoring"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.errors = 0
    
    def hit(self):
        self.hits += 1
    
    def miss(self):
        self.misses += 1
    
    def set_operation(self):
        self.sets += 1
    
    def error(self):
        self.errors += 1
    
    def get_stats(self):
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "errors": self.errors,
            "hit_rate": round(hit_rate, 2),
            "total_requests": total
        }
    
    def reset(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.errors = 0

# Global stats instance
cache_stats = CacheStats()
