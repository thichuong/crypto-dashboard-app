from flask_caching import Cache
import json
import os
from datetime import datetime, timedelta

# Khởi tạo đối tượng cache nhưng chưa gắn vào app
cache = Cache()

# In-memory backup cache for serverless environments
_memory_cache = {}

# Backup cache for rate-limited APIs (store in file system or memory)
BACKUP_CACHE_DIR = "instance/backup_cache"

def is_serverless_environment():
    """Kiểm tra xem có đang chạy trên môi trường serverless không."""
    # Vercel sets VERCEL environment variable
    # AWS Lambda sets AWS_LAMBDA_FUNCTION_NAME
    return os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME') or os.getenv('RAILWAY_ENVIRONMENT')

def ensure_backup_cache_dir():
    """Đảm bảo thư mục backup cache tồn tại (chỉ cho local environment)."""
    if is_serverless_environment():
        return  # Skip file operations on serverless
        
    if not os.path.exists(BACKUP_CACHE_DIR):
        try:
            os.makedirs(BACKUP_CACHE_DIR)
        except OSError:
            # If we can't create directory, fall back to memory cache
            pass

def set_backup_cache(key, data, max_age_hours=24):
    """Lưu dữ liệu vào backup cache với thời gian hết hạn."""
    cache_data = {
        "data": data,
        "timestamp": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(hours=max_age_hours)).isoformat()
    }
    
    # Try file system first (for local development)
    if not is_serverless_environment():
        try:
            ensure_backup_cache_dir()
            cache_file = os.path.join(BACKUP_CACHE_DIR, f"{key}.json")
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            return
        except Exception:
            pass  # Fall through to memory cache
    
    # Fall back to memory cache (for serverless or when file system fails)
    _memory_cache[key] = cache_data

def get_backup_cache(key):
    """Lấy dữ liệu từ backup cache nếu còn hạn."""
    # Try file system first (for local development)
    if not is_serverless_environment():
        cache_file = os.path.join(BACKUP_CACHE_DIR, f"{key}.json")
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    
                expires_at = datetime.fromisoformat(cache_data["expires_at"])
                if datetime.now() <= expires_at:
                    return cache_data["data"]
        except Exception:
            pass
    
    # Try memory cache
    try:
        if key in _memory_cache:
            cache_data = _memory_cache[key]
            expires_at = datetime.fromisoformat(cache_data["expires_at"])
            if datetime.now() <= expires_at:
                return cache_data["data"]
            else:
                # Remove expired entry
                del _memory_cache[key]
    except Exception:
        pass
        
    return None