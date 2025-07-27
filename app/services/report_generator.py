import os
import re
from io import BytesIO
from docx import Document
import google.generativeai as genai

def _read_text_from_docx_stream(stream):
    """Đọc văn bản từ một stream .docx (trong bộ nhớ)."""
    try:
        doc = Document(BytesIO(stream.read()))
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"Lỗi khi đọc file docx: {e}")
        return None

def _read_prompt_file(file_path):
    """Đọc nội dung từ tệp prompt."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy tệp prompt tại '{file_path}'")
        return None

def _extract_code_blocks(response_text):
    """Trích xuất các khối mã nguồn (html, css, js) từ phản hồi của Gemini."""
    html_match = re.search(r"```html(.*?)```", response_text, re.DOTALL)
    css_match = re.search(r"```css(.*?)```", response_text, re.DOTALL)
    js_match = re.search(r"```javascript(.*?)```", response_text, re.DOTALL)

    # Dự phòng trường hợp AI trả về ```js thay vì ```javascript
    if not js_match:
        js_match = re.search(r"```js(.*?)```", response_text, re.DOTALL)

    return {
        "html": html_match.group(1).strip() if html_match else "",
        "css": css_match.group(1).strip() if css_match else "/* Lỗi: Không trích xuất được CSS */",
        "js": js_match.group(1).strip() if js_match else "// Lỗi: Không trích xuất được JS"
    }

def create_report_from_content(file_stream, api_key, prompt_path):
    """
    Hàm chính để tạo báo cáo: đọc file, gọi AI và trích xuất mã.
    Trả về một dictionary chứa các khối mã html, css, js.
    """
    try:
        # 1. Đọc nội dung từ file .docx
        report_content = _read_text_from_docx_stream(file_stream)
        if report_content is None:
            return None

        # 2. Đọc file prompt
        system_prompt = _read_prompt_file(prompt_path)
        if system_prompt is None:
            return None

        full_request = f"{system_prompt}\n\n---\n\n**NỘI DUNG BÁO CÁO CẦN XỬ LÝ:**\n\n{report_content}"

        # 3. Gọi Gemini API
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-pro")
        response = model.generate_content(full_request)
        
        # 4. Trích xuất và trả về kết quả
        return _extract_code_blocks(response.text)

    except Exception as e:
        print(f"Đã xảy ra lỗi trong quá trình tạo báo cáo logic: {e}")
        # In ra phản hồi của AI nếu có lỗi để debug
        if 'response' in locals() and hasattr(response, 'text'):
            print(f"AI Response (on error): {response.text}")
        return None