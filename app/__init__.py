# app/__init__.py

import os
from flask import Flask, render_template, request, flash, redirect, url_for
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
    # Nếu có biến môi trường POSTGRES_URL (từ Vercel), dùng nó.
    # Nếu không, dùng file sqlite tên là 'local_dev.db' trong thư mục gốc.
    if postgres_url := os.getenv('POSTGRES_URL'):
        # Vercel cung cấp URL bắt đầu bằng 'postgres://', SQLAlchemy cần 'postgresql://'
        db_url = postgres_url.replace("postgres://", "postgresql://", 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
        print("INFO: Connecting to Vercel Postgres")
    else:
        # Sử dụng SQLite cho môi trường local
        db_path = os.path.join(app.instance_path, 'local_dev.db')
        os.makedirs(app.instance_path, exist_ok=True) # Đảm bảo thư mục instance tồn tại
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        print("INFO: Connecting to local SQLite database")

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # --- CẤU HÌNH CACHING ĐỘNG ---
    # Nếu có biến môi trường REDIS_URL (từ Vercel hoặc .env), dùng Redis.
    # Nếu không, dùng 'SimpleCache' (in-memory) cho môi trường local.
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

    # Tạo bảng database trong context của ứng dụng
    with app.app_context():
        print("INFO: Initializing database tables...")
        db.create_all()
        print("INFO: Database tables initialized.")

    # --- Routes ---
    @app.route('/')
    def index():
        """
        Hiển thị báo cáo mới nhất và tạo bản sao lưu trữ tĩnh nếu chưa có.
        """
        # 1. Lấy báo cáo mới nhất từ database
        latest_report = Report.query.order_by(Report.created_at.desc()).first()

        # 2. Nếu có báo cáo, tiến hành logic tạo file lưu trữ
        if latest_report:
            try:
                # Đường dẫn tới thư mục lưu trữ trong thư mục 'instance'
                # Thư mục 'instance' lý tưởng cho các file được tạo ra khi ứng dụng chạy
                archive_dir = os.path.join(app.instance_path, 'archive')
                os.makedirs(archive_dir, exist_ok=True) # Tạo thư mục nếu chưa có

                # Tên file sẽ là 'report_ID.html'
                archive_filename = f"report_{latest_report.id}.html"
                archive_filepath = os.path.join(archive_dir, archive_filename)

                # 3. KIỂM TRA file đã tồn tại chưa
                if not os.path.exists(archive_filepath):
                    print(f"INFO: File lưu trữ {archive_filepath} chưa tồn tại. Đang tạo...")
                    
                    # Dùng một template riêng để render ra nội dung HTML hoàn chỉnh
                    archived_html_content = render_template(
                        'index.html', 
                        report=latest_report
                    )

                    # 4. GHI nội dung vào file mới
                    with open(archive_filepath, 'w', encoding='utf-8') as f:
                        f.write(archived_html_content)
                    
                    flash(f"Đã tạo thành công file lưu trữ: {archive_filename}", "success")
                    print(f"SUCCESS: Đã tạo file lưu trữ tại {archive_filepath}")

            except Exception as e:
                # In lỗi ra console và hiển thị thông báo nhưng không làm dừng ứng dụng
                print(f"ERROR: Không thể tạo file lưu trữ. Lỗi: {e}")
                flash(f"Lưu ý: Không thể tạo file lưu trữ cho báo cáo. Lỗi: {e}", "warning")

        # 5. Render trang index chính như bình thường với dữ liệu báo cáo mới nhất
        return render_template('index.html', report=latest_report)

    @app.route('/report/<int:report_id>')
    def view_report(report_id):
        """Hiển thị một báo cáo cụ thể bằng ID."""
        report = db.get_or_404(Report, report_id)
        return render_template('index.html', report=report)

    @app.route('/reports')
    def report_list():
        """Hiển thị danh sách tất cả các báo cáo đã lưu."""
        all_reports = Report.query.order_by(Report.created_at.desc()).all()
        return render_template('report_list.html', reports=all_reports)
    
    @app.route('/upload')
    def upload_page():
        """Hiển thị trang tải lên file báo cáo."""
        return render_template('upload.html')

    @app.route('/upload-report', methods=['POST'])
    def generate_report_from_upload():
        """
        Nhận file, tạo báo cáo và LƯU vào database.
        """
        # ... (Phần kiểm tra file và API key giữ nguyên) ...
        if 'file' not in request.files or not request.form.get('gemini_key'):
            flash('Vui lòng cung cấp đủ tệp .docx và API Key.')
            return redirect(url_for('upload_page'))

        file = request.files['file']
        api_key = request.form.get('gemini_key')
        
        try:
            prompt_path = os.path.join(app.root_path, '..', 'create_report', 'prompt_create_report.md')
            code_blocks = create_report_from_content(file.stream, api_key, prompt_path)

            if not code_blocks or not code_blocks.get("html"):
                flash('Lỗi: Không thể tạo nội dung báo cáo từ AI.')
                return redirect(url_for('upload_page'))

            # Tạo một bản ghi báo cáo mới
            new_report = Report(
                html_content=code_blocks.get("html", ""),
                css_content=code_blocks.get("css", ""),
                js_content=code_blocks.get("js", "")
            )

            # Lưu vào database
            db.session.add(new_report)
            db.session.commit()

            flash('Báo cáo đã được tạo và cập nhật thành công!')
            return redirect(url_for('index'))

        except Exception as e:
            db.session.rollback() # Hoàn tác nếu có lỗi
            flash(f"Đã xảy ra lỗi không mong muốn: {e}")
            return redirect(url_for('upload_page'))

    # Đăng ký blueprint
    app.register_blueprint(crypto_bp, url_prefix='/api/crypto')

    return app