import os
from flask import Flask, render_template
import requests
import concurrent.futures

# Lấy đường dẫn tuyệt đối của thư mục chứa file script này
basedir = os.path.abspath(os.path.dirname(__file__))

# Khởi tạo ứng dụng Flask
# Vercel sẽ tự động tìm biến 'app' này.
app = Flask(__name__, template_folder=os.path.join(basedir, '../templates'), static_folder=os.path.join(basedir, '../static'))

from flask import Flask, render_template, jsonify, request
import requests
import concurrent.futures
import os
import redis
import json

# Khởi tạo ứng dụng Flask
# Kết nối đến Vercel KV (Redis)
try:
    kv_url = os.getenv('KV_URL')
    if not kv_url:
        raise ValueError("KV_URL is not set")
    kv = redis.from_url(kv_url)
    CACHE_KEY = "market_data_cache"
except Exception as e:
    print(f"Lỗi khi kết nối đến KV: {e}")
    kv = None

# --- API Endpoints ---
API_URLS = {
    "price": "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
    "global": "https://api.coingecko.com/api/v3/global",
    "fear_greed": "https://api.alternative.me/fng/?limit=1"
}

def fetch_url(url):
    """Hàm để lấy dữ liệu từ một URL và trả về dưới dạng JSON."""
    try:
        response = requests.get(url, timeout=8)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi lấy dữ liệu từ {url}: {e}")
        return None

def fetch_and_cache_data():
    """Lấy dữ liệu từ các API và lưu vào cache."""
    if not kv:
        return {"error": "KV (Redis) is not connected."}

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_url = {executor.submit(fetch_url, url): key for key, url in API_URLS.items()}
        results = {}
        for future in concurrent.futures.as_completed(future_to_url):
            key = future_to_url[future]
            try:
                results[key] = future.result()
            except Exception as exc:
                print(f'{key} generated an exception: {exc}')

    market_data = parse_api_results(results)
    
    # Chỉ lưu vào cache nếu có dữ liệu hợp lệ
    if market_data:
        kv.set(CACHE_KEY, json.dumps(market_data), ex=600) # Hết hạn sau 10 phút
    return market_data

def parse_api_results(results):
    """Phân tích kết quả từ các API."""
    data = {}
    try:
        if results.get("price"):
            data['btc_price'] = f"${results['price']['bitcoin']['usd']:,.0f}"
        if results.get("global"):
            global_data = results["global"]['data']
            data['total_market_cap'] = f"${global_data['total_market_cap']['usd'] / 1_000_000_000_000:.2f}T"
            data['btc_dominance'] = f"{global_data['market_cap_percentage']['btc']:.1f}%"
        if results.get("fear_greed"):
            fg_data = results["fear_greed"]['data'][0]
            data['fear_greed_value'] = fg_data['value']
            data['fear_greed_text'] = fg_data['value_classification']
    except (KeyError, TypeError, IndexError) as e:
        print(f"Lỗi khi phân tích dữ liệu: {e}")
    return data

# --- Routes ---

@app.route('/')
def home():
    """Phục vụ file HTML chính."""
    return render_template('index.html')

@app.route('/api/market-data')
def get_market_data_from_cache():
    """Cung cấp dữ liệu từ cache cho frontend. Phản hồi ngay lập tức."""
    if not kv:
        return jsonify({"error": "KV not connected"}), 500
        
    cached_data = kv.get(CACHE_KEY)
    if cached_data:
        return jsonify(json.loads(cached_data))
    else:
        # Nếu cache trống, báo cho frontend biết để nó tự kích hoạt cập nhật
        return jsonify({"status": "empty_cache"})

@app.route('/api/update-cache')
def update_cache():
    """
    Endpoint được gọi bởi Cron Job hoặc frontend để cập nhật cache.
    Việc kiểm tra CRON_SECRET bị loại bỏ để đơn giản hóa, cho phép frontend có thể gọi.
    Trong môi trường production thực tế, cần có cơ chế bảo mật tốt hơn.
    """
    print("Yêu cầu cập nhật cache...")
    data = fetch_and_cache_data()
    return jsonify({"status": "cache_updated", "data": data})

if __name__ == '__main__':
    app.run(debug=True)