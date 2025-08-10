# app/__init__.py

import os
from datetime import timedelta
import uuid
from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from dotenv import load_dotenv

# Import các phần mở rộng và model
from .extensions import db
from .models import Report

# Import các blueprints và services khác
from .utils.cache import cache
from .blueprints.crypto import crypto_bp
from .services.report_generator import create_report_from_content
from .services.auto_report_scheduler import start_auto_report_scheduler, generate_auto_research_report
from .services.progress_tracker import progress_tracker

def create_app():
    """
    Hàm factory để tạo và cấu hình ứng dụng Flask.
    """
    load_dotenv()
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY', 'a_very_secret_key')
    
    # --- DETECT ENVIRONMENT ---
    is_production = os.getenv('FLASK_ENV') == 'production'
    
    if is_production:
        print("INFO: Running in production mode")
    else:
        print("INFO: Running in development mode")

    # --- CẤU HÌNH DATABASE ĐỘNG ---
    if postgres_url := os.getenv('POSTGRES_URL'):
        db_url = postgres_url.replace("postgres://", "postgresql://", 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
        print("INFO: Connecting to Postgres database")
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

    # Khởi động auto report scheduler
    start_auto_report_scheduler(app)

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

    @app.route('/pdf-template/<int:report_id>')
    def pdf_template(report_id):
        report = db.get_or_404(Report, report_id)
        return render_template('pdf_template.html', report=report)

    @app.route('/reports')
    def report_list():
        page = request.args.get('page', 1, type=int)
        per_page = 10  # Number of reports per page
        reports = Report.query.order_by(Report.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        return render_template('report_list.html', reports=reports)
    
    @app.route('/upload')
    def upload_page():
        return render_template('upload.html')

    @app.route('/auto-update-system-<secret_key>')
    def auto_update_page(secret_key):
        """Trang auto update - chỉ có thể truy cập bằng URL với secret key đúng"""
        required_secret = os.getenv('AUTO_UPDATE_SECRET_KEY')
        
        # Kiểm tra nếu secret key chưa được cấu hình
        if not required_secret:
            return jsonify({
                'error': 'Auto update system chưa được cấu hình', 
                'message': 'Vui lòng thiết lập AUTO_UPDATE_SECRET_KEY trong file .env'
            }), 503
        
        # Kiểm tra secret key có khớp không
        if secret_key != required_secret:
            # Log attempt để security monitoring
            app.logger.warning(f'Unauthorized access attempt to auto-update-system with key: {secret_key}')
            return jsonify({
                'error': 'Access denied', 
                'message': 'Invalid secret key'
            }), 403
        
        # Log successful access
        app.logger.info('Authorized access to auto-update-system')
        return render_template('auto_update.html')

    @app.route('/upload-report', methods=['POST'])
    def generate_report_from_upload():
        if 'file' not in request.files or not request.form.get('gemini_key'):
            return jsonify({'success': False, 'message': 'Vui lòng cung cấp đủ tệp và API Key.'})

        file = request.files['file']
        api_key = request.form.get('gemini_key')
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Không có tệp nào được chọn.'})

        if file and (file.filename.endswith('.docx') or file.filename.endswith('.odt') or file.filename.endswith('.pdf')):
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
            return jsonify({'success': False, 'message': 'Định dạng tệp không hợp lệ. Vui lòng tải lên tệp .docx, .odt hoặc .pdf.'})

    @app.route('/generate-auto-report', methods=['POST'])
    def manual_generate_auto_report():
        """Route để tạo báo cáo tự động thủ công với progress tracking"""
        try:
            api_key = os.getenv('GEMINI_API_KEY')
            
            if not api_key:
                return jsonify({'success': False, 'message': 'Vui lòng cung cấp API Key hoặc thiết lập GEMINI_API_KEY.'})
            
            # Tạo session_id mới cho tracking
            session_id = str(uuid.uuid4())
            
            # Import và chạy workflow trong background thread
            from .services.report_workflow import generate_auto_research_report_langgraph
            import threading
            
            def run_workflow_background():
                """Chạy workflow trong background thread với application context"""
                # Đảm bảo có application context
                with app.app_context():
                    try:
                        result = generate_auto_research_report_langgraph(api_key, session_id=session_id)
                        print(f"Workflow completed: {result}")
                    except Exception as e:
                        print(f"Workflow error: {e}")
                        progress_tracker.error_progress(session_id, f"Lỗi workflow: {e}")
            
            # Khởi tạo progress tracking
            progress_tracker.start_progress(session_id)
            
            # Chạy workflow trong background thread
            thread = threading.Thread(target=run_workflow_background)
            thread.daemon = True
            thread.start()
            
            return jsonify({
                'success': True, 
                'message': 'Đã bắt đầu tạo báo cáo, theo dõi tiến độ qua API',
                'session_id': session_id
            })
                
        except Exception as e:
            return jsonify({'success': False, 'message': f'Đã xảy ra lỗi không mong muốn: {e}'})

    @app.route('/scheduler-status')
    def scheduler_status():
        """API endpoint để kiểm tra trạng thái scheduler"""
        is_enabled = os.getenv('ENABLE_AUTO_REPORT_SCHEDULER', 'false').lower() == 'true'
        has_api_key = bool(os.getenv('GEMINI_API_KEY'))
        interval_hours = int(os.getenv('AUTO_REPORT_INTERVAL_HOURS', '3'))
        
        # Get latest report info
        latest_report = Report.query.order_by(Report.created_at.desc()).first()
        latest_report_time = latest_report.created_at.isoformat() if latest_report else None
        total_reports = Report.query.count()
        
        return jsonify({
            'scheduler_enabled': is_enabled,
            'has_api_key': has_api_key,
            'interval_hours': interval_hours,
            'status': 'active' if (is_enabled and has_api_key) else 'inactive',
            'latest_report_time': latest_report_time,
            'total_reports': total_reports
        })

    @app.route('/api/progress/<session_id>')
    def get_progress_api(session_id):
        """API endpoint để lấy progress (thay thế SocketIO trên Vercel)"""
        try:
            progress_data = progress_tracker.get_progress(session_id)
            if not progress_data:
                return jsonify({'error': 'Session not found'}), 404
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'progress': progress_data
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/test-progress/<session_id>')
    def test_progress(session_id):
        """Test endpoint để kiểm tra progress tracking"""
        import threading
        import time
        
        def test_workflow():
            # Đảm bảo có application context
            with app.app_context():
                progress_tracker.start_progress(session_id)
                time.sleep(2)
                
                for i in range(1, 8):
                    progress_tracker.update_step(session_id, i, f"Test step {i}", f"Testing step {i} details")
                    time.sleep(2)
                
                progress_tracker.complete_progress(session_id, True, 999)
        
        thread = threading.Thread(target=test_workflow)
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'session_id': session_id, 'message': 'Test progress started'})

    app.register_blueprint(crypto_bp, url_prefix='/api/crypto')

    # --- TEMPLATE GLOBALS ---
    def get_chart_modules_content():
        """Đọc và nối tất cả file trong chart_modules theo thứ tự đúng"""
        source_dir = os.path.join(app.static_folder, "js", "chart_modules")
        file_order = ["gauge.js", "bar.js", "line.js", "doughnut.js"]
        
        content = ""
        for fname in file_order:
            fpath = os.path.join(source_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content += f.read() + "\n\n"
            except FileNotFoundError:
                print(f"Warning: Chart module {fname} not found at {fpath}")
        
        return content

    app.jinja_env.globals.update(timedelta=timedelta)
    app.jinja_env.globals['get_chart_modules_content'] = get_chart_modules_content

    # --- ERROR HANDLERS ---
    @app.errorhandler(404)
    def handle_404(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'API endpoint not found', 'status': 404}), 404
        return render_template('index.html'), 404

    @app.errorhandler(500)
    def handle_500(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error', 'status': 500}), 500
        return render_template('index.html'), 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        # Chỉ log lỗi, không expose chi tiết cho client
        app.logger.error(f'Unhandled exception: {e}', exc_info=True)
        if request.path.startswith('/api/'):
            return jsonify({'error': 'An unexpected error occurred', 'status': 500}), 500
        return render_template('index.html'), 500

    return app