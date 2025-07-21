# main.py
from flask import Flask, render_template, jsonify
import requests

# Khởi tạo Flask. Flask sẽ tự động tìm template trong thư mục 'templates'
app = Flask(__name__)

@app.route('/')
def index():
    """Phục vụ file index.html từ thư mục templates."""
    return render_template('index.html')

# --- CÁC API PROXY ---

@app.route('/api/crypto/global')
def get_global_data():
    try:
        response = requests.get('https://api.coingecko.com/api/v3/global')
        response.raise_for_status()
        
        # Lấy dữ liệu gốc từ API
        global_data = response.json().get('data', {})
        
        # Chỉ trích xuất và trả về hai giá trị cần thiết
        market_cap = global_data.get('total_market_cap', {}).get('usd', 0)
        volume_24h = global_data.get('total_volume', {}).get('usd', 0)
        # Trả về JSON với key đã được đổi tên
        data = {
            'market-cap': market_cap,
            'volume-24h': volume_24h
        }
        print(data)
        return jsonify(data)

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/crypto/btc-and-fng')
def get_btc_and_fng_data():
    try:
        btc_res = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true')
        fng_res = requests.get('https://api.alternative.me/fng/?limit=1')
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
    app.run(host='127.0.0.1', port=8080, debug=True)