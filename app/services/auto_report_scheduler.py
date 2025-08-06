import os
import re
import threading
import time
from datetime import datetime, timezone
from google import genai
from google.genai import types
from ..extensions import db
from ..models import Report
from .report_workflow import generate_auto_research_report_langgraph





def generate_auto_research_report(api_key, max_attempts=3, use_fallback_on_500=True):
    """
    Wrapper function cho LangGraph workflow để giữ tương thích với code cũ.
    
    Args:
        api_key (str): API key của Gemini
        max_attempts (int): Số lần thử tối đa để tạo báo cáo PASS
        use_fallback_on_500 (bool): Có sử dụng fallback mode khi gặp lỗi 500
        
    Returns:
        bool: True nếu tạo báo cáo thành công, False nếu thất bại
    """
    return generate_auto_research_report_langgraph(api_key, max_attempts, use_fallback_on_500)


def schedule_auto_report(app, api_key, interval_hours=6):
    """
    Lên lịch tự động tạo báo cáo mỗi interval_hours giờ.
    
    Args:
        app: Flask app instance
        api_key (str): API key của Gemini
        interval_hours (int): Khoảng thời gian giữa các lần tạo báo cáo (giờ)
    """
    def run_scheduler():
        with app.app_context():
            while True:
                try:
                    # Chạy tạo báo cáo với số lần thử tối đa và fallback
                    max_attempts = int(os.getenv('MAX_REPORT_ATTEMPTS', '3'))
                    use_fallback = os.getenv('USE_FALLBACK_ON_500', 'true').lower() == 'true'
                    success = generate_auto_research_report(api_key, max_attempts, use_fallback)
                    if success:
                        print(f"[{datetime.now()}] Scheduler: Báo cáo đã được tạo thành công")
                    else:
                        print(f"[{datetime.now()}] Scheduler: Tạo báo cáo thất bại")
                        
                except Exception as e:
                    print(f"[{datetime.now()}] Scheduler error: {e}")
                
                # Chờ interval_hours giờ trước khi chạy lần tiếp theo
                time.sleep(interval_hours * 3600)
    
    # Tạo và khởi động thread cho scheduler
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print(f"[{datetime.now()}] Auto report scheduler đã được khởi động (mỗi {interval_hours} giờ)")


def start_auto_report_scheduler(app):
    """
    Khởi động scheduler tự động tạo báo cáo.
    Hàm này sẽ được gọi khi ứng dụng khởi động.
    
    Args:
        app: Flask app instance
    """
    # Lấy API key từ environment variables
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("WARNING: GEMINI_API_KEY không được thiết lập. Auto report scheduler không được khởi động.")
        return False
    
    # Kiểm tra nếu đang chạy trên môi trường production hoặc có enable scheduler
    enable_scheduler = os.getenv('ENABLE_AUTO_REPORT_SCHEDULER', 'false').lower() == 'true'
    
    if enable_scheduler:
        # Lấy interval từ environment variable, mặc định là 3 giờ
        interval_hours = int(os.getenv('AUTO_REPORT_INTERVAL_HOURS', '3'))
        schedule_auto_report(app, api_key, interval_hours)
        return True
    else:
        print("INFO: Auto report scheduler chưa được bật. Thiết lập ENABLE_AUTO_REPORT_SCHEDULER=true để bật.")
        return False
