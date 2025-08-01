import os
import time
from .api_client import fetch_json
from ..utils.cache import get_backup_cache, set_backup_cache

# Global variables for rate limiting
_last_request_time = 0
_min_request_interval = 60  # Minimum 60 seconds between requests

def get_btc_rsi():
    """Lấy chỉ số RSI của Bitcoin từ TAAPI.IO với rate limiting và backup cache."""
    global _last_request_time, _min_request_interval
    
    api_url = os.getenv('TAAPI_RSI_API_URL')


    # Kiểm tra rate limiting
    current_time = time.time()
    time_since_last_request = current_time - _last_request_time
    
    if time_since_last_request < _min_request_interval:
        # Thử lấy từ backup cache khi bị rate limit
        try:
            backup_data = get_backup_cache("taapi_rsi")
            if backup_data:
                return backup_data, None, 200
        except Exception as cache_error:
            print(f"Warning: Could not read from backup cache: {cache_error}")
        
        time_to_wait = _min_request_interval - time_since_last_request
        return None, f"Rate limit: phải chờ {int(time_to_wait)} giây nữa", 429

    _last_request_time = current_time
    json_data, error, status_code = fetch_json(api_url, timeout=3)

    if error:
        # Nếu gặp rate limit, tăng thời gian chờ và thử backup cache
        if status_code == 429:
            _min_request_interval = min(_min_request_interval * 2, 300)  # Tối đa 5 phút
            
            try:
                backup_data = get_backup_cache("taapi_rsi")
                if backup_data:
                    return backup_data, None, 200
            except Exception as cache_error:
                print(f"Warning: Could not read from backup cache: {cache_error}")
                
        return None, f"Lỗi khi gọi TAAPI: {error}", status_code

    try:
        rsi_value = json_data.get('value')
        if rsi_value is None:
            raise KeyError("Không tìm thấy 'value' trong phản hồi của TAAPI.")
        data = {'rsi_14': rsi_value}
        
        # Lưu vào backup cache khi thành công (ignore errors)
        try:
            set_backup_cache("taapi_rsi", data, max_age_hours=6)
        except Exception as cache_error:
            print(f"Warning: Could not save to backup cache: {cache_error}")
        
        # Reset interval sau khi request thành công
        _min_request_interval = 60
        return data, None, 200
    except (AttributeError, KeyError) as e:
        return None, f"Lỗi xử lý dữ liệu RSI từ TAAPI: {e}", 500