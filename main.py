# main.py
import os
from flask import Flask, render_template, jsonify
from flask_caching import Cache
import requests
from dotenv import load_dotenv
from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout

load_dotenv()

# Cấu hình cache: Chuyển sang sử dụng Redis từ Vercel KV
# Kiểm tra xem biến môi trường KV_URL có tồn tại không
if 'KV_URL' in os.environ:
    # Cấu hình cho môi trường Vercel (production)
    config = {
        "DEBUG": False,
        "CACHE_TYPE": "RedisCache",
        "CACHE_DEFAULT_TIMEOUT": 3600, # Tăng cache lên 1 giờ
        "CACHE_REDIS_URL": os.environ['KV_URL']
    }
else:
    # Cấu hình cho môi trường local
    config = {
        "DEBUG": True,
        "CACHE_TYPE": "SimpleCache",
        "CACHE_DEFAULT_TIMEOUT": 3600
    }

app = Flask(__name__)
app.config.from_mapping(config)

# Khởi tạo cache
cache = Cache(app)

# --- ROUTES CHÍNH ---

@app.route('/')
def index():
    """Phục vụ file index.html từ thư mục templates."""
    return render_template('index.html')

# --- CÁC API PROXY VỚI CACHING VÀ XỬ LÝ LỖI NÂNG CAO ---

@app.route('/api/crypto/global')
@cache.cached(timeout=300) # Cache kết quả của hàm này trong 5 phút
def get_global_data():
    """
    Lấy dữ liệu tổng quan thị trường từ CoinGecko.
    Kết quả được cache và chỉ trả về các trường dữ liệu cần thiết.
    Xử lý lỗi chi tiết hơn.
    """
    api_url = os.getenv('COINGECKO_GLOBAL_API_URL', 'https://api.coingecko.com/api/v3/global')
    try:
        response = requests.get(api_url, timeout=10) # Thêm timeout 10 giây
        response.raise_for_status()  # Ném ra HTTPError nếu request không thành công (status code 4xx hoặc 5xx)
        
        global_data = response.json().get('data', {})
        
        # Chỉ trích xuất và trả về hai giá trị cần thiết để tối ưu hóa payload
        data = {
            'market_cap': global_data.get('total_market_cap', {}).get('usd', 0),
            'volume_24h': global_data.get('total_volume', {}).get('usd', 0)
        }
        return jsonify(data)

    except HTTPError as http_err:
        return jsonify({"error": f"Lỗi HTTP: {http_err}", "status_code": http_err.response.status_code}), 500
    except ConnectionError as conn_err:
        return jsonify({"error": f"Lỗi kết nối: {conn_err}"}), 503
    except Timeout:
        return jsonify({"error": "Request timed out"}), 504
    except RequestException as e:
        return jsonify({"error": f"Lỗi không xác định: {e}"}), 500

@app.route('/api/crypto/btc-and-fng')
@cache.cached(timeout=300) # Cache kết quả của hàm này trong 5 phút
def get_btc_and_fng_data():
    """
    Lấy giá BTC và chỉ số Fear & Greed.
    Kết quả được cache, tối ưu hóa và xử lý lỗi chi tiết.
    """
    btc_api_url = os.getenv('COINGECKO_BTC_PRICE_API_URL', 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true')
    fng_api_url = os.getenv('ALTERNATIVE_ME_FNG_API_URL', 'https://api.alternative.me/fng/?limit=1')
    
    try:
        btc_res = requests.get(btc_api_url, timeout=10)
        fng_res = requests.get(fng_api_url, timeout=10)
        btc_res.raise_for_status()
        fng_res.raise_for_status()
        
        btc_data = btc_res.json().get('bitcoin', {})
        fng_data = fng_res.json().get('data', [{}])[0]

        # Trích xuất và cấu trúc lại dữ liệu cần thiết cho frontend
        data = {
            "btc_price_usd": btc_data.get('usd'),
            "btc_change_24h": btc_data.get('usd_24h_change'),
            "fng_value": fng_data.get('value'),
            "fng_classification": fng_data.get('value_classification')
        }
        return jsonify(data)
    
    except HTTPError as http_err:
        return jsonify({"error": f"Lỗi HTTP: {http_err}", "status_code": http_err.response.status_code}), 500
    except ConnectionError as conn_err:
        return jsonify({"error": f"Lỗi kết nối: {conn_err}"}), 503
    except Timeout:
        return jsonify({"error": "Request timed out"}), 504
    except (RequestException, IndexError, KeyError) as e:
        # Bắt thêm IndexError, KeyError phòng trường hợp cấu trúc JSON trả về không như mong đợi
        return jsonify({"error": f"Lỗi xử lý dữ liệu hoặc request: {e}"}), 500

# --- THÊM MỚI: API cho chỉ số RSI của BTC ---
@app.route('/api/crypto/btc-rsi')
@cache.cached(timeout=900) # Cache 15 phút vì RSI không thay đổi quá nhanh
def get_btc_rsi():
    """
    Lấy chỉ số RSI(14) của Bitcoin từ TAAPI.IO.
    """
    api_url = os.getenv('TAAPI_RSI_API_URL')
    if not api_url or 'YOUR_API_KEY' in api_url:
        return jsonify({"error": "API key cho TAAPI.IO chưa được cấu hình"}), 500
        
    try:
        response = requests.get(api_url, timeout=15)
        response.raise_for_status()
        
        # API của TAAPI trả về một object với key là "value" cho chỉ số RSI
        rsi_value = response.json().get('value')
        
        data = {
            'rsi_14': rsi_value
        }
        return jsonify(data)
        
    except HTTPError as http_err:
        return jsonify({"error": f"Lỗi HTTP khi gọi TAAPI: {http_err}", "status_code": http_err.response.status_code}), 500
    except ConnectionError as conn_err:
        return jsonify({"error": f"Lỗi kết nối đến TAAPI: {conn_err}"}), 503
    except Timeout:
        return jsonify({"error": "Request đến TAAPI timed out"}), 504
    except (RequestException, KeyError) as e:
        return jsonify({"error": f"Lỗi xử lý dữ liệu hoặc request đến TAAPI: {e}"}), 500


if __name__ == '__main__':
    # Chạy ứng dụng ở chế độ debug
    app.run(host='127.0.0.1', port=8080, debug=True)