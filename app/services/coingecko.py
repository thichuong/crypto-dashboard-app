import os
from .api_client import fetch_json

BASE_GLOBAL_URL = "https://api.coingecko.com/api/v3/global"
BASE_BTC_PRICE_URL = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"

def get_global_market_data():
    """Lấy tổng vốn hóa và khối lượng giao dịch từ CoinGecko."""
    api_url = os.getenv('COINGECKO_GLOBAL_API_URL', BASE_GLOBAL_URL)
    json_data, error, status_code = fetch_json(api_url)

    if error:
        return None, error, status_code

    try:
        global_data = json_data.get('data', {})
        data = {
            'market_cap': global_data.get('total_market_cap', {}).get('usd'),
            'volume_24h': global_data.get('total_volume', {}).get('usd')
        }
        return data, None, 200
    except (AttributeError, KeyError) as e:
        return None, f"Lỗi xử lý dữ liệu từ CoinGecko: {e}", 500


def get_btc_price():
    """Lấy giá và thay đổi 24h của BTC từ CoinGecko."""
    api_url = os.getenv('COINGECKO_BTC_PRICE_API_URL', BASE_BTC_PRICE_URL)
    json_data, error, status_code = fetch_json(api_url)

    if error:
        return None, error, status_code

    try:
        btc_data = json_data.get('bitcoin', {})
        data = {
            "btc_price_usd": btc_data.get('usd'),
            "btc_change_24h": btc_data.get('usd_24h_change'),
        }
        return data, None, 200
    except (AttributeError, KeyError) as e:
        return None, f"Lỗi xử lý dữ liệu giá BTC: {e}", 500