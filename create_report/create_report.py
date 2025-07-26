# create_report/create_report.py

import os
import glob
import google.generativeai as genai
from docx import Document
import re

# --- Cấu hình API Key của bạn ---
# LƯU Ý: Thay 'YOUR_API_KEY' bằng API Key thực tế của bạn.
# Để bảo mật, hãy sử dụng biến môi trường trong dự án thực tế.
try:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("CẢNH BÁO: Không tìm thấy GEMINI_API_KEY trong file .env. Vui lòng đặt thủ công.")
        api_key = "YOUR_API_KEY" # Thay thế ở đây nếu cần
except ImportError:
    print("Thư viện python-dotenv chưa được cài đặt. Đọc API key trực tiếp.")
    api_key = "YOUR_API_KEY" # Thay thế ở đây nếu cần


genai.configure(api_key=api_key)

# --- Các hàm trợ giúp ---

def find_docx_file(directory="."):
    """Tìm tệp .docx đầu tiên trong thư mục được chỉ định."""
    files = glob.glob(os.path.join(directory, "*.docx"))
    if not files:
        raise FileNotFoundError("Không tìm thấy tệp .docx nào trong thư mục.")
    return files[0]

def read_text_from_docx(file_path):
    """Đọc toàn bộ văn bản từ tệp .docx."""
    try:
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        raise IOError(f"Lỗi khi đọc tệp {file_path}: {e}")

def read_prompt_file(file_path="promt_create_report.txt"):
    """Đọc nội dung từ tệp prompt."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Không tìm thấy tệp prompt: {file_path}")

def extract_code_blocks(response_text):
    """Trích xuất các khối mã nguồn (html, css, js) từ phản hồi của Gemini."""
    
    # Regex để tìm các khối mã được đánh dấu ```<ngôn ngữ> ... ```
    html_match = re.search(r"```html(.*?)```", response_text, re.DOTALL)
    css_match = re.search(r"```css(.*?)```", response_text, re.DOTALL)
    js_match = re.search(r"```javascript(.*?)```", response_text, re.DOTALL)

    # Nếu không tìm thấy javascript, thử tìm js
    if not js_match:
        js_match = re.search(r"```js(.*?)```", response_text, re.DOTALL)

    return {
        "html": html_match.group(1).strip() if html_match else None,
        "css": css_match.group(1).strip() if css_match else None,
        "js": js_match.group(1).strip() if js_match else None
    }


def save_files(code_blocks, output_dir="../static"):
    """Lưu nội dung đã trích xuất vào các tệp tương ứng."""
    
    # Đảm bảo thư mục static tồn tại, nếu không thì tạo mới
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Đã tạo thư mục: {output_dir}")

    if code_blocks["html"]:
        with open(os.path.join(output_dir, "report.html"), "w", encoding="utf-8") as f:
            f.write(code_blocks["html"])
        print("Đã tạo thành công file report.html")
    else:
        print("Không tìm thấy nội dung HTML để tạo tệp.")

    if code_blocks["css"]:
        with open(os.path.join(output_dir, "report.css"), "w", encoding="utf-8") as f:
            f.write(code_blocks["css"])
        print("Đã tạo thành công file report.css")
    else:
        print("Không tìm thấy nội dung CSS để tạo tệp.")

    if code_blocks["js"]:
        with open(os.path.join(output_dir, "report.js"), "w", encoding="utf-8") as f:
            f.write(code_blocks["js"])
        print("Đã tạo thành công file report.js")
    else:
        print("Không tìm thấy nội dung JavaScript để tạo tệp.")


# --- Hàm chính để chạy quy trình ---

def main():
    """Hàm chính để thực thi toàn bộ quy trình."""
    print("Bắt đầu quy trình tạo báo cáo tự động...")
    try:
        # 1. Tìm và đọc các tệp đầu vào
        docx_path = find_docx_file()
        print(f"Đang sử dụng tệp báo cáo: {os.path.basename(docx_path)}")
        
        report_content = read_text_from_docx(docx_path)
        system_prompt = read_prompt_file()
        
        # 2. Tạo yêu cầu hoàn chỉnh cho Gemini
        full_request = f"{system_prompt}\n\n---\n\n**NỘI DUNG BÁO CÁO CẦN XỬ LÝ:**\n\n{report_content}"
        
        # 3. Gọi Gemini API
        print("Đang gửi yêu cầu đến Gemini API... Vui lòng đợi.")
        model = genai.GenerativeModel("gemini-2.5-pro")
        response = model.generate_content(full_request)
        
        # 4. Xử lý và lưu kết quả
        print("Đã nhận phản hồi từ Gemini. Đang xử lý để tạo tệp...")
        code_blocks = extract_code_blocks(response.text)
        
        # Đường dẫn thư mục output là ../static (đi ra ngoài create_report và vào static)
        output_directory = os.path.join(os.path.dirname(__file__), '..', 'static')
        
        save_files(code_blocks, output_dir=output_directory)
        
        print("\nQuy trình hoàn tất!")

    except Exception as e:
        print(f"\nĐã xảy ra lỗi: {e}")

if __name__ == "__main__":
    main()