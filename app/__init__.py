import os
from flask import Flask, render_template, request, flash, redirect, url_for
from dotenv import load_dotenv
from .utils.cache import cache
from .blueprints.crypto import crypto_bp
from markupsafe import Markup
# Thư viện cần thiết
import google.generativeai as genai
from docx import Document
import re
from io import BytesIO

def create_app():
    """
    Hàm factory để tạo và cấu hình ứng dụng Flask.
    """
    load_dotenv()

    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY', 'a_very_secret_key_that_should_be_changed')

    config = {
        "CACHE_TYPE": "SimpleCache",
        "CACHE_DEFAULT_TIMEOUT": 3600
    }
    app.config.from_mapping(config)
    cache.init_app(app)

    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    except Exception as e:
        print(f"Lỗi cấu hình Gemini API: {e}")

    # --- Các hàm trợ giúp ---

    def read_text_from_docx_stream(stream):
        """Đọc văn bản từ một stream .docx (trong bộ nhớ)."""
        doc = Document(BytesIO(stream.read()))
        return "\n".join([para.text for para in doc.paragraphs])

    def read_prompt_file(file_path):
        """Đọc nội dung từ tệp prompt."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Lỗi: Không tìm thấy tệp prompt tại '{file_path}'")
            return None

    def extract_single_html_block(response_text):
        """Trích xuất khối mã HTML duy nhất từ phản hồi của AI."""
        # Tìm kiếm khối mã bắt đầu bằng ```html và kết thúc bằng ```
        match = re.search(r"```html(.*?)```", response_text, re.DOTALL)
        if match:
            # Trả về nội dung bên trong khối mã
            return match.group(1).strip()
        # Nếu không tìm thấy, có thể AI đã trả về HTML thuần mà không có dấu ```
        # Kiểm tra xem văn bản có giống HTML không
        if response_text.strip().startswith("<!DOCTYPE html"):
             return response_text.strip()
        return None


    # --- Các Route của ứng dụng ---

    @app.route('/')
    def index():
        """Phục vụ trang dashboard chính."""
        return render_template('index.html')

    @app.route('/upload')
    def upload_page():
        """Hiển thị trang tải lên file báo cáo."""
        return render_template('upload.html')

    @app.route('/upload-report', methods=['POST'])
    def generate_report_from_upload():
        """Xử lý việc tải lên file docx và tạo một báo cáo HTML duy nhất."""
        if 'file' not in request.files:
            flash('Không có tệp nào được chọn.')
            return redirect(url_for('upload_page'))

        file = request.files['file']
        api_key = request.form.get('gemini_key')

        # --- 1. Xác thực đầu vào ---
        if file.filename == '':
            flash('Chưa chọn tệp nào. Vui lòng tải lên một tệp .txt.', 'error')
            return redirect(url_for('upload_page'))

        if not api_key:
            flash('Thiếu Gemini API Key. Vui lòng cung cấp khóa của bạn.', 'error')
            return redirect(url_for('upload_page'))

        if not file.filename.endswith('.docx'):
            flash('Định dạng tệp không hợp lệ. Chỉ chấp nhận tệp .txt.', 'error')
            return redirect(url_for('upload_page'))

        if file and file.filename.endswith('.docx'):
            try:
                report_content = read_text_from_docx_stream(file.stream)
                
                # Sử dụng prompt mới
                prompt_path = os.path.join(app.root_path, '..', 'create_report', 'promt_create_report_1_file.txt')
                system_prompt = read_prompt_file(prompt_path)
                
                if not system_prompt:
                    flash('Lỗi máy chủ: Không thể đọc được tệp prompt hệ thống.')
                    return redirect(url_for('upload_page'))

                full_request = f"{system_prompt}\n\n---\n\n**NỘI DUNG BÁO CÁO CẦN XỬ LÝ:**\n\n{report_content}"
                
                # **Quan trọng: Sử dụng model gemini-2.5-pro theo yêu cầu**
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-2.5-pro")
                response = model.generate_content(full_request)
                
                # Trích xuất toàn bộ khối HTML
                generated_html_content = extract_single_html_block(response.text)

                if not generated_html_content:
                    flash('Không thể trích xuất mã HTML từ phản hồi của AI. Vui lòng thử lại.')
                    # In ra phản hồi để gỡ lỗi nếu cần
                    print("AI Response:", response.text) 
                    return redirect(url_for('upload_page'))
                
                # Truyền toàn bộ nội dung HTML vào template mới
                # Sử dụng Markup để Flask biết rằng chuỗi này là an toàn để render
                return render_template('view_report.html', report_content=Markup(generated_html_content))

            except Exception as e:
                flash(f"Đã xảy ra lỗi trong quá trình tạo báo cáo: {e}")
                return redirect(url_for('upload_page'))
        else:
            flash('Định dạng tệp không hợp lệ. Vui lòng chỉ tải lên tệp .docx.')
            return redirect(url_for('upload_page'))


    # Đăng ký blueprint cho các API crypto
    app.register_blueprint(crypto_bp, url_prefix='/api/crypto')

    return app