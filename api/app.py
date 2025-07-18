import os
from flask import Flask, render_template
import requests
import concurrent.futures

# Lấy đường dẫn tuyệt đối của thư mục chứa file script này
basedir = os.path.abspath(os.path.dirname(__file__))

# Khởi tạo ứng dụng Flask
# Vercel sẽ tự động tìm biến 'app' này.
app = Flask(__name__, template_folder=os.path.join(basedir, '../templates'))

# API Endpoints
API_URLS = {
    "price": "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
    "global": "https://api.coingecko.com/api/v3/global",
    "fear_greed": "https://api.alternative.me/fng/?limit=1"
}

def fetch_url(url):
    """Hàm để lấy dữ liệu từ một URL và trả về dưới dạng JSON."""
    try:
        response = requests.get(url, timeout=5) # Thêm timeout 5 giây cho mỗi request
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi lấy dữ liệu từ {url}: {e}")
        return None

def get_market_data():
    """
    Lấy tất cả dữ liệu thị trường cần thiết bằng cách gọi các API đồng thời.
    """
    market_data = {
        "btc_price": "N/A",
        "total_market_cap": "N/A",
        "btc_dominance": "N/A",
        "fear_greed_value": "N/A",
        "fear_greed_text": "Unknown"
    }

    # Sử dụng ThreadPoolExecutor để thực hiện các request đồng thời
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Gửi các request đến các API
        future_to_url = {executor.submit(fetch_url, url): key for key, url in API_URLS.items()}
        results = {}
        for future in concurrent.futures.as_completed(future_to_url):
            key = future_to_url[future]
            try:
                results[key] = future.result()
            except Exception as exc:
                print(f'{key} generated an exception: {exc}')

    # Xử lý kết quả sau khi đã có
    try:
        if results.get("price"):
            btc_price = results["price"].get('bitcoin', {}).get('usd')
            if btc_price:
                market_data['btc_price'] = f"${btc_price:,.0f}"

        if results.get("global"):
            global_data = results["global"].get('data', {})
            total_market_cap_usd = global_data.get('total_market_cap', {}).get('usd')
            if total_market_cap_usd:
                market_data['total_market_cap'] = f"${total_market_cap_usd / 1_000_000_000_000:.2f}T"
            
            btc_dominance = global_data.get('market_cap_percentage', {}).get('btc')
            if btc_dominance:
                market_data['btc_dominance'] = f"{btc_dominance:.1f}%"

        if results.get("fear_greed"):
            fg_data = results["fear_greed"].get('data', [{}])[0]
            if 'value' in fg_data:
                market_data['fear_greed_value'] = fg_data['value']
                market_data['fear_greed_text'] = fg_data.get('value_classification', 'Unknown')

    except (KeyError, TypeError, IndexError) as e:
        print(f"Lỗi khi phân tích dữ liệu API đã xử lý: {e}")

    return market_data

@app.route('/')
def home():
    """
    Render trang chủ với dữ liệu thị trường thời gian thực.
    """
    market_data = get_market_data()
    return render_template('index.html', data=market_data)
if __name__ == '__main__':
    app.run(debug=True)