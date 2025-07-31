# app/__init__.py

import os
from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from dotenv import load_dotenv

# Import các phần mở rộng và model
from .extensions import db
from .models import Report

# Import các blueprints và services khác
from .utils.cache import cache
from .blueprints.crypto import crypto_bp
from .services.report_generator import create_report_from_content

def create_app():
    """
    Hàm factory để tạo và cấu hình ứng dụng Flask.
    """
    load_dotenv()
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY', 'a_very_secret_key')

    # --- CẤU HÌNH DATABASE ĐỘNG ---
    if postgres_url := os.getenv('POSTGRES_URL'):
        db_url = postgres_url.replace("postgres://", "postgresql://", 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
        print("INFO: Connecting to Vercel Postgres")
    else:
        db_path = os.path.join(app.instance_path, 'local_dev.db')
        os.makedirs(app.instance_path, exist_ok=True)
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        print("INFO: Connecting to local SQLite database")

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # --- CẤU HÌNH CACHING ĐỘNG ---
    if redis_url := os.getenv('REDIS_URL'):
        app.config['CACHE_TYPE'] = 'RedisCache'
        app.config['CACHE_REDIS_URL'] = redis_url
        print("INFO: Connecting to Redis for caching.")
    else:
        app.config['CACHE_TYPE'] = 'SimpleCache'
        print("INFO: Using in-memory SimpleCache. For production, set REDIS_URL.")

    # Khởi tạo các phần mở rộng
    db.init_app(app)
    cache.init_app(app)

    with app.app_context():
        print("INFO: Initializing database tables...")
        db.create_all()
        print("INFO: Database tables initialized.")

    # --- Routes ---
    @app.route('/')
    def index():
        latest_report = Report.query.order_by(Report.created_at.desc()).first()

        if latest_report and app.config['CACHE_TYPE'] == 'SimpleCache':
            try:
                archive_dir = os.path.join(app.instance_path, 'archive')
                os.makedirs(archive_dir, exist_ok=True)
                archive_filename = f"report_{latest_report.id}.html"
                archive_filepath = os.path.join(archive_dir, archive_filename)
                if not os.path.exists(archive_filepath):
                    print(f"INFO: File lưu trữ {archive_filepath} chưa tồn tại. Đang tạo...")
                    archived_html_content = render_template(
                        'index.html', 
                        report=latest_report
                    )
                    with open(archive_filepath, 'w', encoding='utf-8') as f:
                        f.write(archived_html_content)
                    flash(f"Đã tạo thành công file lưu trữ: {archive_filename}", "success")
                    print(f"SUCCESS: Đã tạo file lưu trữ tại {archive_filepath}")
            except Exception as e:
                print(f"ERROR: Không thể tạo file lưu trữ. Lỗi: {e}")
                flash(f"Lưu ý: Không thể tạo file lưu trữ cho báo cáo. Lỗi: {e}", "warning")
        return render_template('index.html', report=latest_report)

    @app.route('/report/<int:report_id>')
    def view_report(report_id):
        report = db.get_or_404(Report, report_id)
        return render_template('index.html', report=report)

    @app.route('/reports')
    def report_list():
        all_reports = Report.query.order_by(Report.created_at.desc()).all()
        return render_template('report_list.html', reports=all_reports)
    
    @app.route('/upload')
    def upload_page():
        return render_template('upload.html')

    @app.route('/upload-report', methods=['POST'])
    def generate_report_from_upload():
        if 'file' not in request.files or not request.form.get('gemini_key'):
            return jsonify({'success': False, 'message': 'Vui lòng cung cấp đủ tệp và API Key.'})

        file = request.files['file']
        api_key = request.form.get('gemini_key')
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Không có tệp nào được chọn.'})

        if file and (file.filename.endswith('.docx') or file.filename.endswith('.odt')):
            try:
                prompt_path = os.path.join(app.root_path, '..', 'create_report', 'prompt_create_report.md')
                # Truyền cả file stream và filename
                code_blocks = create_report_from_content(file.stream, file.filename, api_key, prompt_path)

                if not code_blocks or not code_blocks.get("html"):
                    return jsonify({'success': False, 'message': 'Lỗi: Không thể tạo nội dung báo cáo từ AI.'})

                new_report = Report(
                    html_content=code_blocks.get("html", ""),
                    css_content=code_blocks.get("css", ""),
                    js_content=code_blocks.get("js", "")
                )
                db.session.add(new_report)
                db.session.commit()

                return jsonify({'success': True, 'message': 'Báo cáo đã được tạo và cập nhật thành công!'})

            except Exception as e:
                db.session.rollback()
                return jsonify({'success': False, 'message': f'Đã xảy ra lỗi không mong muốn: {e}'})
        else:
            return jsonify({'success': False, 'message': 'Định dạng tệp không hợp lệ. Vui lòng tải lên tệp .docx hoặc .odt.'})

    app.register_blueprint(crypto_bp, url_prefix='/api/crypto')

    return app