import os
from .api_client import fetch_json

BASE_FNG_URL = "https://api.alternative.me/fng/?limit=1"

def get_fng_index():
    """Lấy chỉ số Fear & Greed từ Alternative.me."""
    json_data, error, status_code = fetch_json(BASE_FNG_URL)

    if error:
        return None, error, status_code

    try:
        fng_data = json_data.get('data', [{}])[0]
        data = {
            "fng_value": fng_data.get('value'),
            "fng_classification": fng_data.get('value_classification')
        }
        return data, None, 200
    except (IndexError, KeyError) as e:
        return None, f"Lỗi xử lý dữ liệu F&G: {e}", 500