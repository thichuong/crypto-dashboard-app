"""
Node lưu báo cáo vào database
"""
from .base import ReportState
from ...services.progress_tracker import progress_tracker
from ...extensions import db
from ...models import Report


"""
Node lưu báo cáo vào database với retry logic cho SSL errors
"""
import time
import psycopg2
from sqlalchemy.exc import OperationalError
from .base import ReportState
from ...services.progress_tracker import progress_tracker
from ...extensions import db
from ...models import Report


def _save_to_database_with_retry(state: ReportState, session_id: str, max_retries: int = 3) -> ReportState:
    """Helper function để lưu database với retry logic cho SSL errors"""
    
    for attempt in range(max_retries):
        try:
            # Tạo báo cáo mới và lưu vào database
            if attempt > 0:
                progress_tracker.update_step(session_id, details=f"Thử lại lưu database (lần {attempt + 1}/{max_retries})...")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                progress_tracker.update_step(session_id, details="Tạo record báo cáo mới...")
            
            new_report = Report(
                html_content=state["html_content"],
                css_content=state["css_content"],
                js_content=state["js_content"]
            )
            
            progress_tracker.update_step(session_id, details="Đang commit vào database...")
            
            # Thử commit với timeout protection
            db.session.add(new_report)
            db.session.commit()
            
            state["report_id"] = new_report.id
            state["success"] = True
            
            progress_tracker.complete_progress(session_id, True, new_report.id)
            print(f"✅ Lưu database thành công sau {attempt + 1} lần thử - Report ID: {new_report.id}")
            return state
            
        except (OperationalError, psycopg2.OperationalError) as e:
            # Rollback session trước khi retry
            try:
                db.session.rollback()
            except:
                pass
            
            error_detail = str(e)
            is_ssl_error = any(keyword in error_detail.lower() for keyword in [
                'ssl', 'decryption failed', 'bad record mac', 'connection reset'
            ])
            
            if is_ssl_error and attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"⚠️ SSL error detected, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                progress_tracker.update_step(session_id, details=f"SSL error - thử lại sau {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                # Hết số lần thử hoặc không phải SSL error
                error_msg = f"Lỗi khi lưu database sau {max_retries} lần thử: {error_detail}"
                state["error_messages"].append(error_msg)
                state["success"] = False
                progress_tracker.error_progress(session_id, error_msg)
                print(f"❌ {error_msg}")
                return state
                
        except Exception as e:
            # Các lỗi khác không retry
            try:
                db.session.rollback()
            except:
                pass
            
            error_msg = f"Lỗi không thể retry khi lưu database: {e}"
            state["error_messages"].append(error_msg)
            state["success"] = False
            progress_tracker.error_progress(session_id, error_msg)
            print(f"❌ {error_msg}")
            return state
    
    # Không bao giờ đến đây, nhưng để đảm bảo
    error_msg = "Đã hết số lần thử lưu database"
    state["error_messages"].append(error_msg)
    state["success"] = False
    progress_tracker.error_progress(session_id, error_msg)
    return state


def _save_to_database_with_context(state: ReportState, session_id: str) -> ReportState:
    """Helper function để lưu database với proper context"""
    # Kiểm tra kích thước dữ liệu trước khi lưu
    total_size = len(state["html_content"]) + len(state["css_content"]) + len(state["js_content"])
    progress_tracker.update_step(session_id, details=f"Chuẩn bị lưu dữ liệu (~{total_size:,} ký tự)...")
    
    if total_size > 50000:  # > 50KB
        print(f"⚠️ Large data detected: {total_size:,} characters - using retry logic")
        max_retries = 5  # Tăng số lần retry cho dữ liệu lớn
    else:
        max_retries = 3
    
    return _save_to_database_with_retry(state, session_id, max_retries)


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
