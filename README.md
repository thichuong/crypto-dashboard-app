# 📊 Bảng Điều Khiển Crypto & Trình Tạo Báo Cáo AI

Một ứng dụng web Flask toàn diện, cung cấp bảng điều khiển dữ liệu thị trường tiền mã hóa theo thời gian thực và một hệ thống tạo báo cáo phân tích tự động bằng AI, sử dụng API của Google Gemini.

**(Xem trực tiếp tại)** [https://crypto-dashboard-app-thichuong.vercel.app/](https://crypto-dashboard-app-thichuong.vercel.app/)

## ✨ Các Tính Năng Chính

  * **Dashboard Dữ Liệu Sống:** Theo dõi các chỉ số quan trọng được cập nhật tự động:
      * Giá **Bitcoin (BTC)** và biến động trong 24 giờ.
      * Tổng vốn hóa thị trường và khối lượng giao dịch toàn cầu.
      * Chỉ số **Sợ hãi & Tham lam (Fear & Greed Index)** từ Alternative.me.
      * Chỉ số **Sức mạnh Tương đối (RSI)** của BTC từ TAAPI.IO.
  * **Tạo Báo Cáo Tự Động Bằng AI:**
      * **Tích hợp vào Dashboard:** Tải và hiển thị một báo cáo phân tích chi tiết, được tạo tự động từ tệp `.docx`, ngay trên trang chính.
      * **Báo Cáo Độc Lập:** Cung cấp trang cho phép người dùng tải lên tệp `.docx` và nhập API Key của Gemini để tạo và xem ngay một báo cáo hoàn chỉnh.
  * **Giao Diện Người Dùng Hiện Đại:**
      * Thiết kế responsive, tương thích trên máy tính và thiết bị di động.
      * Hỗ trợ **chế độ Sáng/Tối (Light/Dark mode)**.
      * Sử dụng biểu đồ SVG động, có hiệu ứng tương tác để trực quan hóa dữ liệu.
  * **Backend Hiệu Quả:**
      * Sử dụng **Flask** và các blueprint để tổ chức code gọn gàng.
      * Tích hợp **caching** để tối ưu hiệu suất và giảm số lần gọi API không cần thiết.

## 🤖 Luồng Hoạt Động Của Trình Tạo Báo Cáo AI

Dự án triển khai hai phương pháp riêng biệt để biến tài liệu `.docx` thành báo cáo web bằng Google Gemini, phục vụ các nhu cầu khác nhau.

### 1\. Phương pháp Tích hợp (Cập nhật Dashboard chính)

Luồng này được thiết kế cho nhà phát triển để cập nhật nội dung phân tích chính trên trang dashboard.

  * **Cách hoạt động:**
    1.  Nhà phát triển đặt một tệp `.docx` chứa nội dung phân tích vào thư mục `create_report`.
    2.  Chạy kịch bản `python create_report/create_report.py`.
    3.  Kịch bản đọc nội dung từ `.docx`, kết hợp với prompt từ `create_report/promt_create_report.md`, và gửi yêu cầu đến Gemini.
    4.  Prompt này yêu cầu AI tạo ra **ba tệp riêng biệt**: `report.html`, `report.css`, và `report.js`. Các tệp này được lưu vào thư mục `app/static/`.
    5.  Trang `index.html` sẽ tự động tải nội dung từ `report.html` và áp dụng CSS, JS tương ứng để hiển thị báo cáo.

### 2\. Phương pháp Độc lập (Cho người dùng cuối)

Luồng này cung cấp một công cụ linh hoạt cho bất kỳ ai muốn nhanh chóng tạo một báo cáo web từ tài liệu của riêng họ.

  * **Cách hoạt động:**
    1.  Người dùng truy cập trang `/upload`.
    2.  Họ nhập **Gemini API Key** và tải lên một tệp `.docx`.
    3.  Ứng dụng Flask nhận yêu cầu, đọc nội dung và gọi service `report_generator` để xử lý.
    4.  Service này sử dụng một prompt khác, yêu cầu AI tạo ra **một tệp HTML duy nhất**, trong đó mã CSS và JavaScript được nhúng trực tiếp.
    5.  Kết quả là một trang `generated_report.html` hoàn chỉnh, độc lập được hiển thị ngay lập tức cho người dùng.

## 🛠️ Công Nghệ Sử Dụng

  * **Backend:**
      * **Ngôn ngữ:** Python 3
      * **Framework:** Flask
      * **WSGI Server:** Gunicorn
      * **Thư viện:** Requests, python-dotenv, Flask-Caching
  * **AI & Tự động hóa:**
      * Google Gemini API (`google-generativeai`)
      * `python-docx` để đọc file Word.
  * **Frontend:**
      * HTML5, CSS3, Vanilla JavaScript
      * **Framework CSS:** Tailwind CSS
      * **Trực quan hóa:** Chart.js, D3.js, và các hàm vẽ SVG tùy chỉnh.
  * **APIs Dữ Liệu:**
      * CoinGecko
      * Alternative.me
      * TAAPI.IO
  * **Deployment:** Vercel

## 🚀 Cài Đặt Và Chạy Cục Bộ

1.  **Clone kho mã nguồn:**

    ```bash
    git clone https://github.com/thichuong/crypto-dashboard-app.git
    cd crypto-dashboard-app
    ```

2.  **Tạo và kích hoạt môi trường ảo:**

    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # macOS/Linux
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Cài đặt các thư viện cần thiết:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Thiết lập biến môi trường:**

      * Tạo một tệp `.env` ở thư mục gốc của dự án.
      * Sao chép nội dung từ file `env` và điền các giá trị cần thiết, đặc biệt là `GEMINI_API_KEY`.

5.  **Chạy ứng dụng:**

    ```bash
    flask run
    # Hoặc chạy bằng file run.py để có cấu hình chi tiết hơn
    python run.py
    ```

    Ứng dụng sẽ có tại `http://127.0.0.1:8080`.

## 📁 Cấu Trúc Dự Án

```
/
|-- app/
|   |-- __init__.py             # Khởi tạo Flask, chứa route cho trang upload và dashboard
|   |-- blueprints/
|   |   `-- crypto.py           # Các route cho API dữ liệu crypto (global, btc, fng, rsi)
|   |-- services/
|   |   |-- api_client.py       # Hàm GET request chung
|   |   |-- coingecko.py        # Logic gọi API CoinGecko
|   |   |-- alternative_me.py   # Logic gọi API Alternative.me (F&G)
|   |   |-- taapi.py            # Logic gọi API TAAPI.IO (RSI)
|   |   `-- report_generator.py # Service xử lý tạo báo cáo độc lập (Phương pháp 2)
|   |-- static/                 # Chứa CSS, JS, và các tệp báo cáo từ Phương pháp 1
|   |-- templates/
|   |   |-- index.html          # Trang dashboard chính
|   |   |-- upload.html         # Giao diện tải lên cho Phương pháp 2
|   |   `-- generated_report.html # Template để hiển thị kết quả từ Phương pháp 2
|   `-- utils/
|       `-- cache.py            # Khởi tạo Flask-Caching
|-- create_report/
|   |-- create_report.py        # Kịch bản để chạy Phương pháp 1
|   |-- promt_create_report.md  # Prompt cho Phương pháp 1 (tạo 3 tệp)
|   `-- (ví dụ) report.docx
|-- .gitignore
|-- requirements.txt            # Các thư viện Python cần thiết
|-- run.py                      # Điểm khởi chạy ứng dụng (entrypoint)
`-- vercel.json                 # Cấu hình cho deployment Vercel
```