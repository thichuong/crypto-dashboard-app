
-----

# 📊 Toàn Cảnh Thị Trường Crypto - Bảng Điều Khiển & Báo Cáo Phân Tích

Một ứng dụng web dashboard cung cấp cái nhìn tổng quan theo thời gian thực về thị trường tiền mã hóa và hiển thị các báo cáo phân tích chuyên sâu được tạo tự động bằng AI.

[](https://www.google.com/search?q=https://vercel.com/new/clone%3Frepository-url%3Dhttps://github.com/thichuong/crypto-dashboard-app)

**(Tùy chọn) Link xem trực tiếp:** [https://crypto-dashboard-app-sooty.vercel.app/](https://www.google.com/search?q=https://crypto-dashboard-app-sooty.vercel.app/)

## ✨ Tính năng nổi bật

  * **Dữ liệu thị trường trực tiếp:** Theo dõi tổng vốn hóa, khối lượng giao dịch 24h, và giá Bitcoin được cập nhật liên tục.
  * **Chỉ báo trực quan:** Các biểu đồ đồng hồ (gauge) hiện đại cho Chỉ số Sợ hãi & Tham lam (Fear & Greed Index) và Chỉ số Sức mạnh Tương đối (RSI) của BTC.
  * **Báo cáo chuyên sâu:** Tải và hiển thị động các báo cáo phân tích chi tiết với mục lục điều hướng thông minh, giúp theo dõi các phần nội dung một cách dễ dàng.
  * **Tự động hóa bằng AI:** Đi kèm một kịch bản Python mạnh mẽ sử dụng Google Gemini API để tự động chuyển đổi tài liệu báo cáo từ file `.docx` sang bộ ba tệp `HTML`, `CSS`, và `JS` sẵn sàng để hiển thị trên web.
  * **Giao diện tùy biến:** Hỗ trợ chuyển đổi giữa giao diện Sáng (Light) và Tối (Dark) để phù hợp với sở thích người dùng.
  * **Thiết kế đáp ứng (Responsive):** Giao diện được xây dựng để hoạt động tốt trên cả máy tính và thiết bị di động.

## 🛠️ Công nghệ sử dụng

  * **Backend:**
      * **Python 3**
      * **Flask:** Micro-framework để xây dựng web server và API.
      * **Flask-Caching:** Tối ưu hóa hiệu suất bằng cách cache các phản hồi từ API.
      * **Gunicorn:** WSGI server để triển khai ứng dụng.
  * **Frontend:**
      * HTML5, CSS3
      * **JavaScript (Vanilla):** Không sử dụng framework, giúp ứng dụng nhẹ và nhanh.
      * **Thư viện biểu đồ tùy chỉnh:** Một thư viện vẽ biểu đồ tùy chỉnh, có hiệu ứng động và hỗ trợ theme.
      * **Font Awesome:** Cho các icon.
  * **API & Tự động hóa:**
      * **CoinGecko, Alternative.me, TAAPI.IO:** Các nguồn cung cấp dữ liệu thị trường.
      * **Google Gemini API:** Nền tảng cho kịch bản tự động tạo báo cáo.
      * **python-docx:** Thư viện để đọc nội dung từ file `.docx`.
  * **Deployment:**
      * **Vercel:** Nền tảng chính để triển khai ứng dụng Flask dưới dạng Serverless Function.

## 🚀 Cài đặt và Chạy cục bộ

Để chạy dự án này trên máy của bạn, hãy làm theo các bước sau:

1.  **Clone kho mã nguồn:**

    ```bash
    git clone https://github.com/thichuong/crypto-dashboard-app.git
    cd crypto-dashboard-app
    ```

2.  **Tạo và kích hoạt môi trường ảo:**

    ```bash
    python -m venv venv
    # Trên Windows
    venv\Scripts\activate
    # Trên macOS/Linux
    source venv/bin/activate
    ```

3.  **Cài đặt các thư viện cần thiết:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Thiết lập biến môi trường:**

      * Tạo một file mới tên là `.env` trong thư mục gốc.
      * Sao chép toàn bộ nội dung từ file `.env` được cung cấp vào file `.env` mới tạo.
      * Điền các giá trị API Key của bạn vào file `.env`.
        ```env
        # .env
        COINGECKO_GLOBAL_API_URL="https://api.coingecko.com/api/v3/global"
        COINGECKO_BTC_PRICE_API_URL="https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
        ALTERNATIVE_ME_FNG_API_URL="https://api.alternative.me/fng/?limit=1"
        TAAPI_RSI_API_URL="https://api.taapi.io/rsi?secret=YOUR_TAAPI_KEY&exchange=binance&symbol=BTC/USDT&interval=1d"
        GEMINI_API_KEY="AIzaSy...Your...Key"
        ```

5.  **Chạy ứng dụng Flask:**

    ```bash
    flask run
    ```

    Ứng dụng sẽ có thể truy cập tại `http://127.0.0.1:5000`.

## 🤖 Sử dụng Kịch bản Tạo Báo cáo

Kịch bản `create_report.py` cho phép bạn tự động tạo các tệp báo cáo `report.html`, `report.css`, và `report.js` từ một tệp `.docx`.

1.  **Chuẩn bị:**

      * Đặt file báo cáo `.docx` của bạn vào thư mục `create_report`.
      * Đảm bảo bạn đã điền `GEMINI_API_KEY` trong file `.env`.

2.  **Chạy kịch bản:**
    Mở terminal, điều hướng đến thư mục `create_report` và chạy lệnh sau:

    ```bash
    cd create_report
    python create_report.py
    ```

    Các tệp kết quả sẽ được tự động tạo và lưu vào thư mục `static`, sẵn sàng để ứng dụng web sử dụng.

## 📁 Cấu trúc dự án

```
.
├── .github/workflows/       # Cấu hình GitHub Actions
│   └── static.yml
├── create_report/           # Chứa kịch bản và tài liệu để tạo báo cáo
│   ├── create_report.py
│   ├── promt_create_report.txt
│   └── Crypto_.docx
├── static/                  # Chứa các tệp frontend
│   ├── chart.js
│   ├── main.js
│   ├── report.css
│   ├── report.html
│   ├── report.js
│   └── style.css
├── templates/               # Chứa các template HTML của Flask
│   └── index.html
├── .env                     # File biến môi trường (cần tự tạo)
├── main.py                  # File chính của ứng dụng Flask
├── requirements.txt         # Danh sách các thư viện Python
└── vercel.json              # Cấu hình triển khai trên Vercel
```
