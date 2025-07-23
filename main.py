# main.py
import os
from flask import Flask, render_template, jsonify
from flask_caching import Cache
import requests
from dotenv import load_dotenv

# Tải các biến môi trường từ file .env (chỉ cần cho phát triển cục bộ)
load_dotenv()

# Cấu hình cache: lưu trữ trong bộ nhớ đơn giản
config = {
    "DEBUG": True,
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 300  # Thời gian cache mặc định là 300 giây (5 phút)
}

# Khởi tạo Flask
app = Flask(__name__)
app.config.from_mapping(config)

# Khởi tạo cache
cache = Cache(app)

# --- ROUTES CHÍNH ---

@app.route('/')
def index():
    """Phục vụ file index.html từ thư mục templates."""
    return render_template('index.html')

# --- CÁC API PROXY VỚI CACHING ---

@app.route('/api/crypto/global')
@cache.cached(timeout=300) # Cache kết quả của hàm này trong 5 phút
def get_global_data():
    """
    Lấy dữ liệu tổng quan thị trường từ CoinGecko.
    Kết quả được cache để giảm thiểu các cuộc gọi API không cần thiết.
    """
    api_url = os.getenv('COINGECKO_GLOBAL_API_URL', 'https://api.coingecko.com/api/v3/global')
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        
        global_data = response.json().get('data', {})
        
        # Chỉ trích xuất và trả về hai giá trị cần thiết
        data = {
            'market-cap': global_data.get('total_market_cap', {}).get('usd', 0),
            'volume-24h': global_data.get('total_volume', {}).get('usd', 0)
        }
        return jsonify(data)

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/crypto/btc-and-fng')
@cache.cached(timeout=300) # Cache kết quả của hàm này trong 5 phút
def get_btc_and_fng_data():
    """
    Lấy giá BTC và chỉ số Fear & Greed.
    Kết quả được cache để tối ưu hiệu suất.
    """
    btc_api_url = os.getenv('COINGECKO_BTC_PRICE_API_URL', 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true')
    fng_api_url = os.getenv('ALTERNATIVE_ME_FNG_API_URL', 'https://api.alternative.me/fng/?limit=1')
    
    try:
        btc_res = requests.get(btc_api_url)
        fng_res = requests.get(fng_api_url)
        btc_res.raise_for_status()
        fng_res.raise_for_status()
        
        data = {
            "bitcoin": btc_res.json(),
            "fear_and_greed": fng_res.json()
        }
        return jsonify(data)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Chạy ứng dụng ở chế độ debug
    app.run(host='127.0.0.1', port=8080, debug=True)