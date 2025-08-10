# app/routes/api_routes.py

import os
import threading
import time
from flask import jsonify
from ..models import Report
from ..services.progress_tracker import progress_tracker


def register_api_routes(app):
    """
    Đăng ký các API routes.
    """
    
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
