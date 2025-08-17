# app/routes/report_routes.py

import os
import uuid
import threading
from flask import request, jsonify
from ..extensions import db
from ..models import CryptoReport as Report
from ..services.report_generator import create_report_from_content
from ..services.progress_tracker import progress_tracker


def register_report_routes(app):
    """
    Đăng ký các route liên quan đến báo cáo.
    """
    
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
            
            # Import và chạy workflow V2 trong background thread
            from ..services.report_workflow_v2 import generate_auto_research_report_langgraph_v2
            
            def run_workflow_background():
                """Chạy workflow V2 trong background thread với application context"""
                # Đảm bảo có application context
                with app.app_context():
                    try:
                        result = generate_auto_research_report_langgraph_v2(api_key, session_id=session_id)
                        print(f"Workflow V2 completed: {result}")
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

    @app.route('/report-fragment/<int:report_id>', methods=['GET'])
    def report_fragment(report_id):
        """
        Trả về HTML fragment của báo cáo theo report_id và language query param (lang=vi|en).
        Nếu lang=en và report.html_content_en tồn tại thì trả về nội dung tiếng Anh.
        """
        lang = request.args.get('lang', 'vi')
        try:
            report = Report.query.get(report_id)
            if not report:
                return jsonify({'success': False, 'message': 'Report not found'}), 404

            if lang == 'en' and getattr(report, 'html_content_en', None):
                return jsonify({'success': True, 'html': report.html_content_en})
            else:
                return jsonify({'success': True, 'html': report.html_content})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
