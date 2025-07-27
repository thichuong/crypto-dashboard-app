# create_report/create_report.py

import os
import glob
import google.generativeai as genai
from docx import Document
import re

# --- Cấu hình API Key của bạn ---
# LƯU Ý: Để bảo mật, hãy sử dụng biến môi trường.
try:
    from dotenv import load_dotenv
    # Tải biến môi trường từ file .env ở thư mục gốc của dự án
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(dotenv_path=dotenv_path)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("CẢNH BÁO: Không tìm thấy GEMINI_API_KEY trong file .env. Vui lòng đặt thủ công.")
        api_key = "YOUR_API_KEY"
except ImportError:
    print("Thư viện python-dotenv chưa được cài đặt. Đọc API key trực tiếp.")
    api_key = "YOUR_API_KEY"


genai.configure(api_key=api_key)

# --- Các hàm trợ giúp ---

def find_docx_file(directory="./"):
    """Tìm tệp .docx đầu tiên trong thư mục hiện tại của script."""
    files = glob.glob(os.path.join(directory, "*.docx"))
    if not files:
        raise FileNotFoundError(f"Không tìm thấy tệp .docx nào trong thư mục '{directory}'.")
    return files[0]

def read_text_from_docx(file_path):
    """Đọc toàn bộ văn bản từ tệp .docx."""
    try:
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        raise IOError(f"Lỗi khi đọc tệp {file_path}: {e}")

def read_prompt_file(file_path="./prompt_create_report.md"):
    """Đọc nội dung từ tệp prompt."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Không tìm thấy tệp prompt: {file_path}")

def extract_code_blocks(response_text):
    """Trích xuất các khối mã nguồn (html, css, js) từ phản hồi của Gemini."""
    html_match = re.search(r"```html(.*?)```", response_text, re.DOTALL)
    css_match = re.search(r"```css(.*?)```", response_text, re.DOTALL)
    js_match = re.search(r"```javascript(.*?)```", response_text, re.DOTALL)

    if not js_match:
        js_match = re.search(r"```js(.*?)```", response_text, re.DOTALL)

    return {
        "html": html_match.group(1).strip() if html_match else None,
        "css": css_match.group(1).strip() if css_match else None,
        "js": js_match.group(1).strip() if js_match else None
    }


def save_files(code_blocks, output_dir):
    """Lưu nội dung đã trích xuất vào các tệp tương ứng."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Đã tạo thư mục: {output_dir}")

    files_to_save = {
        "report.html": code_blocks.get("html"),
        "report.css": code_blocks.get("css"),
        "report.js": code_blocks.get("js")
    }

    for filename, content in files_to_save.items():
        if content:
            with open(os.path.join(output_dir, filename), "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Đã tạo thành công file {filename}")
        else:
            print(f"Không tìm thấy nội dung cho file {filename} để tạo tệp.")


# --- Hàm chính để chạy quy trình ---

def main():
    """Hàm chính để thực thi toàn bộ quy trình."""
    print("Bắt đầu quy trình tạo báo cáo tự động...")
    try:
        # 1. Tìm và đọc các tệp đầu vào
        current_dir = os.path.dirname(__file__)
        docx_path = find_docx_file(current_dir)
        print(f"Đang sử dụng tệp báo cáo: {os.path.basename(docx_path)}")
        
        report_content = read_text_from_docx(docx_path)
        system_prompt = read_prompt_file(os.path.join(current_dir, "prompt_create_report.md"))
        
        # 2. Tạo yêu cầu hoàn chỉnh cho Gemini
        full_request = f"{system_prompt}\n\n---\n\n**NỘI DUNG BÁO CÁO CẦN XỬ LÝ:**\n\n{report_content}"
        
        # 3. Gọi Gemini API
        print("Đang gửi yêu cầu đến Gemini API... Vui lòng đợi.")
        model = genai.GenerativeModel("gemini-2.5-pro") # Sử dụng model phù hợp
        response = model.generate_content(full_request)
        
        # 4. Xử lý và lưu kết quả
        print("Đã nhận phản hồi từ Gemini. Đang xử lý để tạo tệp...")
        code_blocks = extract_code_blocks(response.text)
        
        # *** THAY ĐỔI CHÍNH Ở ĐÂY ***
        # Đường dẫn thư mục output là ../app/static 
        # (đi ra ngoài thư mục create_report, vào thư mục app, rồi vào static)
        output_directory = os.path.abspath(os.path.join(current_dir, '..', 'app', 'static'))
        
        save_files(code_blocks, output_dir=output_directory)
        
        print(f"\nQuy trình hoàn tất! Các tệp đã được lưu tại: {output_directory}")

    except Exception as e:
        print(f"\nĐã xảy ra lỗi: {e}")

if __name__ == "__main__":
    main()