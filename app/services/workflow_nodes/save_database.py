"""
Node lưu báo cáo vào database
"""
from .base import ReportState
from ...services.progress_tracker import progress_tracker
from ...extensions import db
from ...models import Report


def _save_to_database_with_context(state: ReportState, session_id: str) -> ReportState:
    """Helper function để lưu database với proper context"""
    try:
        # Tạo báo cáo mới và lưu vào database
        progress_tracker.update_step(session_id, details="Tạo record báo cáo mới...")
        new_report = Report(
            html_content=state["html_content"],
            css_content=state["css_content"],
            js_content=state["js_content"]
        )
        
        progress_tracker.update_step(session_id, details="Đang commit vào database...")
        db.session.add(new_report)
        db.session.commit()
        
        state["report_id"] = new_report.id
        state["success"] = True
        
        progress_tracker.complete_progress(session_id, True, new_report.id)
        
    except Exception as e:
        error_msg = f"Lỗi khi lưu database: {e}"
        state["error_messages"].append(error_msg)
        state["success"] = False
        progress_tracker.error_progress(session_id, error_msg)
        try:
            db.session.rollback()
        except:
            pass
    
    return state


def save_database_node(state: ReportState) -> ReportState:
    """Node để lưu báo cáo vào database"""
    session_id = state["session_id"]
    progress_tracker.update_step(session_id, 6, "Lưu báo cáo", "Đang lưu HTML, CSS, JS vào cơ sở dữ liệu")
    
    try:
        # Import Flask app để có application context
        from ... import create_app
        from flask import current_app
        
        # Kiểm tra xem đã có application context chưa
        try:
            # Test xem có app context không
            _ = current_app.name
            # Nếu có rồi, gọi trực tiếp
            return _save_to_database_with_context(state, session_id)
        except RuntimeError:
            # Chưa có app context, tạo mới
            app = create_app()
            with app.app_context():
                return _save_to_database_with_context(state, session_id)
            
    except Exception as e:
        error_msg = f"Lỗi khi lưu database: {e}"
        state["error_messages"].append(error_msg)
        state["success"] = False
        progress_tracker.error_progress(session_id, error_msg)
        try:
            db.session.rollback()
        except:
            pass
    
    return state
