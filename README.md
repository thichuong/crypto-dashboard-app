
-----

# 📊 Toàn Cảnh Thị Trường Crypto - Bảng Điều Khiển & Báo Cáo Phân Tích

Một ứng dụng web dashboard cung cấp cái nhìn tổng quan theo thời gian thực về thị trường tiền mã hóa và hiển thị các báo cáo phân tích chuyên sâu được tạo tự động bằng AI.

**(Tùy chọn) Link xem trực tiếp:** [https://crypto-dashboard-app-thichuong.vercel.app/](https://crypto-dashboard-app-thichuong.vercel.app/)

## ✨ Tính năng nổi bật

* **Dữ liệu thị trường trực tiếp:** Theo dõi tổng vốn hóa, khối lượng giao dịch 24h, và giá Bitcoin được cập nhật liên tục.
* **Chỉ báo trực quan:** Các biểu đồ đồng hồ (gauge) hiện đại cho Chỉ số Sợ hãi & Tham lam (Fear & Greed Index) và Chỉ số Sức mạnh Tương đối (RSI) của BTC.
* **Báo cáo chuyên sâu:** Tải và hiển thị động các báo cáo phân tích chi tiết với mục lục điều hướng thông minh.
* **Tự động hóa bằng AI:** Kịch bản Python sử dụng Google Gemini để tự động chuyển đổi tài liệu `.docx` thành bộ ba tệp `HTML`, `CSS`, và `JS`.
* **Giao diện tùy biến:** Hỗ trợ chuyển đổi giữa giao diện Sáng (Light) và Tối (Dark).
* **Thiết kế đáp ứng (Responsive):** Giao diện hoạt động tốt trên cả máy tính và thiết bị di động.

## 🛠️ Công nghệ sử dụng

* **Backend:** Python 3, Flask, Flask-Caching, Gunicorn
* **Frontend:** HTML5, CSS3, Vanilla JavaScript, Font Awesome
* **API & Tự động hóa:** CoinGecko, Alternative.me, TAAPI.IO, Google Gemini API
* **Deployment:** Vercel

## 🚀 Cài đặt và Chạy cục bộ

1.  **Clone kho mã nguồn:**
    ```bash
    git clone [https://github.com/thichuong/crypto-dashboard-app.git](https://github.com/thichuong/crypto-dashboard-app.git)
    cd crypto-dashboard-app
    ```

2.  **Tạo và kích hoạt môi trường ảo:**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Cài đặt các thư viện:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Thiết lập biến môi trường:**
    * Tạo tệp `.env` trong thư mục gốc.
    * Sao chép nội dung từ `.env.example` và điền các API Key của bạn.

5.  **Chạy ứng dụng:**
    ```bash
    flask --app "app:create_app()" run
    ```
    Ứng dụng sẽ có tại `http://127.0.0.1:5000`.

## 🤖 Sử dụng Kịch bản Tạo Báo cáo

1.  **Chuẩn bị:**
    * Đặt tệp `.docx` vào thư mục `create_report`.
    * Điền `GEMINI_API_KEY` trong tệp `.env`.

2.  **Chạy kịch bản:**
    ```bash
    cd create_report
    python create_report.py
    ```
    Các tệp kết quả (`report.html`, `report.css`, `report.js`) sẽ được tạo trong thư mục `app/static`.


## 📁 Cấu trúc dự án

```
/
|-- app/
|   |-- __init__.py             # Khởi tạo ứng dụng Flask và các blueprint
|   |-- blueprints/
|   |   |-- __init__.py
|   |   `-- crypto.py           # Chứa các route cho API crypto
|   |-- services/
|   |   |-- __init__.py
|   |   |-- api_client.py       # Client chung để gọi API bên ngoài
|   |   |-- coingecko.py        # Dịch vụ cho CoinGecko API
|   |   |-- alternative_me.py   # Dịch vụ cho Alternative.me API
|   |   `-- taapi.py            # Dịch vụ cho TAAPI.IO API
|   |-- static/
|   |   |-- chart.js
|   |   |-- main.js
|   |   |-- report.css
|   |   |-- report.html
|   |   |-- report.js
|   |   `-- style.css
|   |-- templates/
|   |   `-- index.html
|   `-- utils/
|       |-- __init__.py
|       `-- cache.py            # Cấu hình và khởi tạo cache
|-- create_report/
|   |-- create_report.py
|   |-- promt_create_report.txt
|   `-- Phân tích thị trường Crypto hôm nay_.docx
|-- requirements.txt
|-- run.py
`-- vercel.json

```
