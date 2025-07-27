

# 📊 Bảng Điều Khiển Crypto & Trình Tạo Báo Cáo AI

Ứng dụng web mạnh mẽ kết hợp bảng điều khiển dữ liệu thị trường tiền mã hóa thời gian thực với một hệ thống **tạo báo cáo phân tích tự động bằng AI** thông qua hai luồng xử lý độc đáo.

**(Tùy chọn) Link xem trực tiếp:** [https://crypto-dashboard-app-thichuong.vercel.app/](https://crypto-dashboard-app-thichuong.vercel.app/)

## ✨ Tính năng nổi bật

  * **Dashboard Dữ liệu Sống:** Theo dõi các chỉ số quan trọng như tổng vốn hóa, khối lượng giao dịch, giá Bitcoin, chỉ số Sợ hãi & Tham lam, và RSI của BTC.
  * **Giao diện Trực quan & Tùy biến:** Thiết kế hiện đại, hỗ trợ chế độ Sáng/Tối, và tương thích tốt trên mọi thiết bị (Responsive).
  * **Trình Tạo Báo Cáo AI Linh Hoạt:** Điểm nhấn của dự án là khả năng biến tài liệu `.docx` thành các báo cáo web chuyên nghiệp bằng Google Gemini, với hai phương pháp riêng biệt:
    1.  **Tích hợp vào Dashboard Chính:** Tạo bộ ba tệp `HTML`, `CSS`, `JS` để tích hợp sâu vào trang tổng quan.
    2.  **Tạo Báo Cáo Độc Lập:** Cho phép người dùng tải lên tài liệu và API key để tạo và xem ngay một báo cáo HTML duy nhất, khép kín.

## 🤖 Hai Phương Pháp Tạo Báo Cáo Bằng AI

Dự án sử dụng Google Gemini để tự động hóa việc chuyển đổi nội dung phân tích từ tệp `.docx` thành giao diện web. Mỗi phương pháp sử dụng một tệp "prompt" riêng để hướng dẫn AI, phục vụ cho các mục đích sử dụng khác nhau.

-----

### 1\. Phương pháp Tích hợp (Script-based)

Phương pháp này dùng để cập nhật báo cáo chính hiển thị trên trang dashboard.

  * **Luồng hoạt động:**
    1.  Người phát triển đặt một tệp `.docx` chứa nội dung phân tích vào thư mục `create_report`.
    2.  Chạy kịch bản `python create_report/create_report.py`.
    3.  Kịch bản đọc nội dung từ `.docx` và sử dụng prompt tại `create_report/promt_create_report.txt` để gửi yêu cầu đến Gemini.
    4.  Prompt này yêu cầu AI tạo ra **ba tệp riêng biệt**: `report.html`, `report.css`, và `report.js`.
    5.  Các tệp này được lưu vào `app/static/`, và nội dung của `report.html` sẽ được tải động vào trang dashboard chính.
  * **Mục đích:** Dành cho việc cập nhật báo cáo phân tích cốt lõi, có cấu trúc phức tạp và được tích hợp chặt chẽ vào giao diện chung của ứng dụng.

-----

### 2\. Phương pháp Độc lập (Web-based)

Phương pháp này cho phép bất kỳ ai cũng có thể tạo nhanh một báo cáo để xem ngay mà không ảnh hưởng đến ứng dụng chính.

  * **Luồng hoạt động:**
    1.  Người dùng truy cập trang `/upload`.
    2.  Họ nhập **Gemini API Key** và tải lên một tệp `.docx` của riêng mình.
    3.  Ứng dụng Flask xử lý yêu cầu, đọc nội dung tệp và sử dụng prompt tại `create_report/promt_create_report_1_file.txt`.
    4.  Prompt này yêu cầu AI tạo ra **một khối mã HTML duy nhất**, trong đó CSS và JavaScript được nhúng trực tiếp vào tệp.
    5.  Kết quả là một trang web hoàn chỉnh, độc lập được hiển thị ngay cho người dùng.
  * **Mục đích:** Cung cấp một tiện ích linh hoạt cho phép người dùng tự tạo và xem các báo cáo của riêng họ một cách nhanh chóng.

## 🛠️ Công nghệ sử dụng

  * **Backend:** Python 3, Flask, Gunicorn
  * **Frontend:** HTML5, CSS3, Tailwind CSS, Vanilla JavaScript
  * **Trực quan hóa Dữ liệu:** Chart.js, D3.js
  * **API & Tự động hóa:** Google Gemini API, CoinGecko, Alternative.me, TAAPI.IO
  * **Deployment:** Vercel

## 🚀 Cài đặt và Chạy cục bộ

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
    source venv/bin/activate
    ```

3.  **Cài đặt các thư viện:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Thiết lập biến môi trường:**

      * Tạo một tệp `.env` trong thư mục gốc.
      * Sao chép nội dung từ `.env.example` (nếu có) hoặc điền các API key cần thiết, đặc biệt là `GEMINI_API_KEY`.

5.  **Chạy ứng dụng:**

    ```bash
    flask --app "app:create_app()" run
    ```

    Ứng dụng sẽ có tại `http://127.0.0.1:5000`.

## 📁 Cấu trúc dự án

```
/
|-- app/
|   |-- __init__.py             # Khởi tạo Flask, chứa route cho Phương pháp 2
|   |-- blueprints/
|   |   `-- crypto.py           # Các route cho API dữ liệu crypto
|   |-- services/               # Logic gọi API bên ngoài (CoinGecko, Gemini, v.v.)
|   |-- static/                 # Chứa CSS, JS, và các tệp báo cáo từ Phương pháp 1
|   |-- templates/
|   |   |-- index.html          # Trang dashboard chính
|   |   |-- upload.html         # Giao diện cho Phương pháp 2
|   |   `-- view_report.html    # Hiển thị kết quả từ Phương pháp 2
|-- create_report/
|   |-- create_report.py        # Kịch bản để chạy Phương pháp 1
|   |-- promt_create_report.txt # Prompt cho Phương pháp 1 (tạo nhiều tệp)
|   |-- promt_create_report_1_file.txt # Prompt cho Phương pháp 2 (tạo 1 tệp)
|   `-- (ví dụ) report.docx
|-- requirements.txt
|-- run.py                      # Điểm khởi chạy ứng dụng
`-- vercel.json                 # Cấu hình cho deployment Vercel
```
