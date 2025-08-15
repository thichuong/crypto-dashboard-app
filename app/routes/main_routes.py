# app/routes/main_routes.py

import os
from datetime import timezone
from flask import render_template, request, flash, jsonify
from ..extensions import db
from ..models import Report


def register_main_routes(app):
    """
    Đăng ký các route chính của ứng dụng.
    """
    
    @app.route('/health')
    def health_check():
        """Health check endpoint for Railway"""
        return jsonify({'status': 'healthy', 'message': 'Crypto Dashboard is running'}), 200
    
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
        # Ensure created_at is timezone-aware UTC for templates
        if latest_report and latest_report.created_at is not None:
            try:
                if latest_report.created_at.tzinfo is None:
                    latest_report.created_at = latest_report.created_at.replace(tzinfo=timezone.utc)
                else:
                    latest_report.created_at = latest_report.created_at.astimezone(timezone.utc)
            except Exception:
                # if any unexpected type, leave as-is and let template handle it
                pass

        return render_template('index.html', report=latest_report)

    @app.route('/report/<int:report_id>')
    def view_report(report_id):
        report = db.get_or_404(Report, report_id)
        if report and report.created_at is not None:
            try:
                if report.created_at.tzinfo is None:
                    report.created_at = report.created_at.replace(tzinfo=timezone.utc)
                else:
                    report.created_at = report.created_at.astimezone(timezone.utc)
            except Exception:
                pass
        return render_template('index.html', report=report)

    @app.route('/pdf-template/<int:report_id>')
    def pdf_template(report_id):
        report = db.get_or_404(Report, report_id)
        if report and report.created_at is not None:
            try:
                if report.created_at.tzinfo is None:
                    report.created_at = report.created_at.replace(tzinfo=timezone.utc)
                else:
                    report.created_at = report.created_at.astimezone(timezone.utc)
            except Exception:
                pass
        return render_template('pdf_template.html', report=report)

    @app.route('/reports')
    def report_list():
        page = request.args.get('page', 1, type=int)
        per_page = 10  # Number of reports per page
        reports = Report.query.order_by(Report.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        # Normalize created_at for each item in the current page
        try:
            for r in getattr(reports, 'items', []):
                if getattr(r, 'created_at', None) is not None:
                    if r.created_at.tzinfo is None:
                        r.created_at = r.created_at.replace(tzinfo=timezone.utc)
                    else:
                        r.created_at = r.created_at.astimezone(timezone.utc)
        except Exception:
            pass

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
