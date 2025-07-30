from flask_caching import Cache
import json
import os
from datetime import datetime, timedelta

# Khởi tạo đối tượng cache nhưng chưa gắn vào app
cache = Cache()

# Backup cache for rate-limited APIs (store in file system)
BACKUP_CACHE_DIR = "instance/backup_cache"

def ensure_backup_cache_dir():
    """Đảm bảo thư mục backup cache tồn tại."""
    if not os.path.exists(BACKUP_CACHE_DIR):
        os.makedirs(BACKUP_CACHE_DIR)

def set_backup_cache(key, data, max_age_hours=24):
    """Lưu dữ liệu vào backup cache với thời gian hết hạn."""
    ensure_backup_cache_dir()
    cache_file = os.path.join(BACKUP_CACHE_DIR, f"{key}.json")
    cache_data = {
        "data": data,
        "timestamp": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(hours=max_age_hours)).isoformat()
    }
    
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass  # Ignore backup cache errors

def get_backup_cache(key):
    """Lấy dữ liệu từ backup cache nếu còn hạn."""
    cache_file = os.path.join(BACKUP_CACHE_DIR, f"{key}.json")
    
    try:
        if not os.path.exists(cache_file):
            return None
            
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
            
        expires_at = datetime.fromisoformat(cache_data["expires_at"])
        if datetime.now() > expires_at:
            return None
            
        return cache_data["data"]
    except Exception:
        return None