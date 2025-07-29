# 📊 Bảng Điều Khiển Crypto & Trình Tạo Báo Cáo AI

Một ứng dụng web Flask toàn diện, cung cấp bảng điều khiển dữ liệu thị trường tiền mã hóa theo thời gian thực và một công cụ cho phép người dùng tự tạo báo cáo phân tích bằng AI từ tài liệu của riêng họ.

**Xem trực tiếp tại:** [https://crypto-dashboard-app-thichuong.vercel.app/](https://crypto-dashboard-app-thichuong.vercel.app/)

## ✨ Các Tính Năng Chính

  * **Dashboard Dữ Liệu Sống:** Theo dõi các chỉ số quan trọng được cập nhật tự động, với cơ chế caching để tối ưu hiệu suất:
      * Giá **Bitcoin (BTC)** và biến động trong 24 giờ.
      * Tổng vốn hóa thị trường và khối lượng giao dịch toàn cầu.
      * Chỉ số **Sợ hãi & Tham lam (Fear & Greed Index)** từ nhiều nguồn.
      * Chỉ số **Sức mạnh Tương đối (RSI)** của BTC.
  * **Tạo Báo Cáo Tự Động Bằng AI:**
      * Một công cụ mạnh mẽ cho phép bất kỳ ai cũng có thể biến một tài liệu văn bản (`.docx` hoặc `.odt`) thành một trang web báo cáo hoàn chỉnh chỉ trong vài cú nhấp chuột.
  * **Lưu Trữ và Xem Lại Lịch Sử:**
      * Mỗi báo cáo được tạo ra sẽ được lưu trữ an toàn trong cơ sở dữ liệu.
      * Trang `/reports` cho phép xem lại toàn bộ lịch sử các báo cáo đã được tạo.
  * **Giao Diện Người Dùng Hiện Đại:**
      * Thiết kế responsive, sử dụng Tailwind CSS.
      * Hỗ trợ **chế độ Sáng/Tối (Light/Dark mode)**.
      * Sử dụng các biểu đồ SVG động, có hiệu ứng tương tác được viết bằng JavaScript thuần túy để trực quan hóa dữ liệu.

---

## 🤖 Luồng Hoạt Động Của Trình Tạo Báo Cáo AI

Tính năng cốt lõi của dự án là cho phép người dùng cuối tự tạo ra các báo cáo phân tích dưới dạng trang web một cách nhanh chóng.

* **Cách hoạt động:**
    1.  **Truy cập:** Người dùng truy cập vào trang `/upload` trên ứng dụng.
    2.  **Cung cấp thông tin:** Trên trang này, người dùng cần điền hai thông tin:
        * **Gemini API Key:** Khóa API cá nhân của họ từ Google AI Studio để có quyền sử dụng mô hình Gemini.
        * **Tải tệp lên:** Người dùng chọn và tải lên một tệp tài liệu từ máy tính. Hệ thống hỗ trợ hai định dạng phổ biến: **`.docx`** (Microsoft Word) và **`.odt`** (OpenDocument Text).
    3.  **Xử lý ở Backend:** Khi người dùng nhấn nút "Generate Report", ứng dụng Flask sẽ:
        * Nhận và xác thực tệp đã tải lên.
        * Sử dụng thư viện `python-docx` hoặc `odfpy` để đọc và trích xuất toàn bộ nội dung văn bản từ tệp.
        * Gọi service `report_generator`, nơi nội dung văn bản này được kết hợp với một "prompt" (câu lệnh chỉ dẫn) được thiết kế đặc biệt cho AI.
        * Gửi yêu cầu hoàn chỉnh đến API của Google Gemini. Prompt này hướng dẫn AI biến nội dung văn bản thô thành ba khối mã nguồn riêng biệt: **HTML** cho cấu trúc, **CSS** cho giao diện, và **JavaScript**.
    4.  **Tạo mã nguồn:**
        * **HTML:** Tạo cấu trúc nội dung cho trang báo cáo.
        * **CSS:** Tạo các quy tắc định dạng để trang báo cáo có giao diện đẹp mắt.
        * **JavaScript:** Tạo mã nguồn để gọi các hàm vẽ biểu đồ đã được code sẵn trong tệp `chart.js`. AI sẽ xác định loại biểu đồ phù hợp (ví dụ: line chart, bar chart, doughnut chart) và chuẩn bị dữ liệu cần thiết để truyền vào các hàm đó, giúp trực quan hóa thông tin một cách sinh động ngay trong báo cáo.
    5.  **Lưu trữ và Hiển thị:**
        * Sau khi nhận được phản hồi từ Gemini, ứng dụng sẽ lưu ba khối mã nguồn (HTML, CSS, JS) vào một bản ghi mới trong cơ sở dữ liệu.
        * Người dùng sẽ được tự động chuyển hướng về trang chủ, nơi báo cáo họ vừa tạo sẽ được hiển thị ngay lập tức.
-----

## 🗄️ Lưu Trữ Báo Cáo Trong Cơ Sở Dữ Liệu

Để đảm bảo tính bền vững và khả năng truy xuất, mỗi báo cáo được tạo ra đều được lưu vào cơ sở dữ liệu (PostgreSQL trên Vercel hoặc SQLite khi chạy local) thông qua mô hình `Report` của SQLAlchemy.

  * **Cấu trúc bảng `Report`:** Bảng này được thiết kế để lưu trữ riêng biệt từng thành phần của trang báo cáo:
      * `id` (Integer, Primary Key): Mã định danh duy nhất cho mỗi báo cáo.
      * `created_at` (DateTime): Dấu thời gian ghi lại thời điểm báo cáo được tạo.
      * `html_content` (Text): Lưu trữ toàn bộ mã **HTML** của báo cáo.
      * `css_content` (Text): Lưu trữ toàn bộ mã **CSS** để định dạng cho báo cáo đó.
      * `js_content` (Text): Lưu trữ mã **JavaScript** để thêm các hiệu ứng hoặc tương tác.

Khi một trang cần hiển thị một báo cáo (ví dụ: trang chủ hiển thị báo cáo mới nhất), ứng dụng sẽ truy vấn bản ghi tương ứng từ cơ sở dữ liệu và chèn các nội dung `html_content`, `css_content`, và `js_content` vào template một cách linh động.

-----

## 🛠️ Công Nghệ Sử Dụng

  * **Backend:** Python 3, Flask, SQLAlchemy
  * **Cơ sở dữ liệu:** PostgreSQL (Production), SQLite (Development)
  * **Caching:** Redis (Production), SimpleCache (Development)
  * **AI:** Google Gemini API (`google-generativeai`)
  * **Xử lý tài liệu:** `python-docx`, `odfpy`
  * **Frontend:** HTML5, CSS3, JavaScript (ES6+), Tailwind CSS
  * **Deployment:** Vercel

-----

## 🚀 Cài Đặt Và Chạy Cục Bộ

1.  **Clone kho mã nguồn:**
    ```bash
    git clone https://github.com/thichuong/crypto-dashboard-app.git
    cd crypto-dashboard-app
    ```
2.  **Tạo và kích hoạt môi trường ảo:**
    ```bash
    # Windows
    python -m venv venv && venv\Scripts\activate
    # macOS/Linux
    python -m venv venv && source venv/bin/activate
    ```
3.  **Cài đặt các thư viện:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Thiết lập biến môi trường:**
      * Tạo một tệp `.env` ở thư mục gốc, sao chép nội dung từ `.env_example` và điền các giá trị API key cần thiết.
5.  **Build tệp JavaScript cho biểu đồ:**
      * Kịch bản này sẽ nối các module JavaScript trong `app/static/js/chart_modules/` thành một tệp `chart.js` duy nhất để ứng dụng sử dụng.
    <!-- end list -->
    ```bash
    python build.py
    ```
6.  **Chạy ứng dụng:**
    ```bash
    flask run
    ```
    Ứng dụng sẽ có tại `http://127.0.0.1:5000` (hoặc cổng do Flask chỉ định).

-----

## 🧪 Kiểm Thử Biểu Đồ với `chart_tester.html`

Trong thư mục gốc của dự án có tệp **`chart_tester.html`**. Đây là một công cụ phát triển hữu ích.

  * **Mục đích:** Tệp này cho phép bạn xem và kiểm thử các biểu đồ SVG một cách độc lập mà **không cần phải chạy toàn bộ ứng dụng Flask**.
  * **Cách sử dụng:**
    1.  Chạy `python build.py` để đảm bảo tệp `app/static/js/chart.js` được cập nhật mới nhất.
    2.  Mở trực tiếp tệp `chart_tester.html` bằng trình duyệt (ví dụ: nhấp đúp vào tệp).
    3.  Trang này sẽ tải `chart.js` và hiển thị tất cả các biểu đồ có sẵn, giúp bạn dễ dàng gỡ lỗi (debug) và tinh chỉnh giao diện hoặc hành vi của chúng một cách nhanh chóng.