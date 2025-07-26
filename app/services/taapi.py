import os
from .api_client import fetch_json

def get_btc_rsi():
    """Lấy chỉ số RSI của Bitcoin từ TAAPI.IO."""
    api_url = os.getenv('TAAPI_RSI_API_URL')

    if not api_url or 'YOUR_TAAPI_KEY' in api_url:
        return None, "API key cho TAAPI.IO chưa được cấu hình", 500

    json_data, error, status_code = fetch_json(api_url, timeout=15)

    if error:
        return None, f"Lỗi khi gọi TAAPI: {error}", status_code

    try:
        rsi_value = json_data.get('value')
        if rsi_value is None:
            raise KeyError("Không tìm thấy 'value' trong phản hồi của TAAPI.")
        data = {'rsi_14': rsi_value}
        return data, None, 200
    except (AttributeError, KeyError) as e:
        return None, f"Lỗi xử lý dữ liệu RSI từ TAAPI: {e}", 500