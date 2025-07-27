import os
from flask import Flask, render_template, request, flash, redirect, url_for
from dotenv import load_dotenv
from markupsafe import Markup
from .utils.cache import cache
from .blueprints.crypto import crypto_bp

# Import hàm logic xử lý báo cáo
from .services.report_generator import create_report_from_content

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

    # --- Routes ---

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
        """
        Nhận file, gọi service để tạo báo cáo và hiển thị kết quả.
        """
        if 'file' not in request.files:
            flash('Không có tệp nào được chọn.')
            return redirect(url_for('upload_page'))

        file = request.files['file']
        api_key = request.form.get('gemini_key')

        if file.filename == '' or not api_key or not file.filename.endswith('.docx'):
            flash('Dữ liệu đầu vào không hợp lệ. Vui lòng kiểm tra lại API Key và tệp .docx.')
            return redirect(url_for('upload_page'))
        
        try:
            prompt_path = os.path.join(app.root_path, '..', 'create_report', 'promt_create_report.txt')
            
            # Gọi hàm xử lý logic từ service
            code_blocks = create_report_from_content(file.stream, api_key, prompt_path)

            if code_blocks is None:
                flash('Lỗi máy chủ: Không thể tạo nội dung báo cáo. Vui lòng kiểm tra log để biết chi tiết.')
                return redirect(url_for('upload_page'))

            # Render template mới với dữ liệu đã được xử lý
            # Chúng ta không cần dùng view_report.html nữa mà dùng template mới
            return render_template(
                'generated_report.html', 
                html_content=code_blocks['html'], 
                css_code=code_blocks['css'], 
                js_code=code_blocks['js']
            )

        except Exception as e:
            flash(f"Đã xảy ra lỗi không xác định: {e}")
            return redirect(url_for('upload_page'))

    # Đăng ký blueprint cho các API crypto
    app.register_blueprint(crypto_bp, url_prefix='/api/crypto')

    return app