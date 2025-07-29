# build.py
import os
# cat chart_modules/utils.js chart_modules/gauge.js chart_modules/bar.js chart_modules/line.js chart_modules/doughnut.js > chart.js
# --- CẤU HÌNH ---
# Đường dẫn đến thư mục chứa các module JavaScript
SOURCE_DIR = "app/static/js/chart_modules"

# Đường dẫn đến tệp đích
TARGET_FILE = "app/static/js/chart.js"

# Liệt kê các tệp theo đúng thứ tự bạn muốn nối
# utils.js phải luôn ở đầu tiên!
FILE_ORDER = [
    "utils.js",
    "gauge.js",
    "bar.js",
    "line.js",
    "doughnut.js",
]

def build_js():
    """
    Đọc nội dung từ các tệp nguồn và ghi vào tệp đích.
    """
    print("Bắt đầu quá trình build chart.js...")

    # Mở tệp đích ở chế độ ghi ('w')
    with open(TARGET_FILE, "w", encoding="utf-8") as outfile:
        for fname in FILE_ORDER:
            fpath = os.path.join(SOURCE_DIR, fname)
            try:
                # Mở từng tệp nguồn ở chế độ đọc ('r')
                with open(fpath, "r", encoding="utf-8") as infile:
                    print(f"  -> Đang xử lý tệp: {fname}")
                    # Đọc nội dung và ghi vào tệp đích
                    outfile.write(infile.read())
                    # Thêm một dòng mới để ngăn các tệp bị dính liền
                    outfile.write("\n\n")
            except FileNotFoundError:
                print(f"(!) CẢNH BÁO: Không tìm thấy tệp {fpath}. Bỏ qua...")

    print(f"\n✅ Build thành công! Tệp {TARGET_FILE} đã được cập nhật.")

# Chạy hàm build khi kịch bản được thực thi trực tiếp
if __name__ == "__main__":
    build_js()