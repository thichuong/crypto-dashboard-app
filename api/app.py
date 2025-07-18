import os
from flask import Flask, render_template
import requests

# Lấy đường dẫn tuyệt đối của thư mục chứa file script này
basedir = os.path.abspath(os.path.dirname(__file__))

# Khởi tạo ứng dụng Flask
# Vercel sẽ tự động tìm biến 'app' này.
app = Flask(__name__, template_folder=os.path.join(basedir, '../templates'))

def get_market_data():
    """
    Lấy tất cả dữ liệu thị trường cần thiết từ các API khác nhau.
    Bao gồm: Giá BTC, Vốn hóa thị trường, BTC Dominance, và Fear & Greed Index.
    """
    market_data = {
        "btc_price": "N/A",
        "total_market_cap": "N/A",
        "btc_dominance": "N/A",
        "fear_greed_value": "N/A",
        "fear_greed_text": "Unknown"
    }

    # API Endpoints
    coingecko_global_url = "https://api.coingecko.com/api/v3/global"
    coingecko_price_url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    fear_greed_url = "https://api.alternative.me/fng/?limit=1"

    try:
        # Lấy dữ liệu giá BTC
        price_response = requests.get(coingecko_price_url)
        price_response.raise_for_status()
        price_data = price_response.json()
        btc_price = price_data.get('bitcoin', {}).get('usd')
        if btc_price:
            market_data['btc_price'] = f"${btc_price:,.0f}"

        # Lấy dữ liệu thị trường toàn cầu (Vốn hóa, Dominance)
        global_response = requests.get(coingecko_global_url)
        global_response.raise_for_status()
        global_data = global_response.json().get('data', {})
        
        total_market_cap_usd = global_data.get('total_market_cap', {}).get('usd')
        if total_market_cap_usd:
            market_data['total_market_cap'] = f"${total_market_cap_usd / 1_000_000_000_000:.2f}T" # Định dạng thành nghìn tỷ

        btc_dominance = global_data.get('market_cap_percentage', {}).get('btc')
        if btc_dominance:
            market_data['btc_dominance'] = f"{btc_dominance:.1f}%"

        # Lấy chỉ số Fear & Greed
        fg_response = requests.get(fear_greed_url)
        fg_response.raise_for_status()
        fg_data = fg_response.json().get('data', [{}])[0]
        
        if 'value' in fg_data:
            market_data['fear_greed_value'] = fg_data['value']
            market_data['fear_greed_text'] = fg_data.get('value_classification', 'Unknown')

    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gọi API: {e}")
    except (KeyError, TypeError, IndexError) as e:
        print(f"Lỗi khi phân tích dữ liệu API: {e}")

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