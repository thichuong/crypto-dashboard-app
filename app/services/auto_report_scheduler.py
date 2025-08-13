import os
import re
import threading
import time
from datetime import datetime, timezone
from google import genai
from google.genai import types
from ..extensions import db
from ..models import Report
from .report_workflow_v2 import generate_auto_research_report_langgraph_v2





def generate_auto_research_report(api_key, max_attempts=3, use_fallback_on_500=True):
    """
    Wrapper function cho LangGraph workflow V2 để giữ tương thích với code cũ.
    
    Args:
        api_key (str): API key của Gemini
        max_attempts (int): Số lần thử tối đa để tạo báo cáo PASS
        use_fallback_on_500 (bool): Có sử dụng fallback mode khi gặp lỗi 500 (legacy parameter, ignored in V2)
        
    Returns:
        bool: True nếu tạo báo cáo thành công, False nếu thất bại
    """
    # Sử dụng workflow V2, parameter use_fallback_on_500 được ignore vì V2 có error handling tốt hơn
    result = generate_auto_research_report_langgraph_v2(api_key, max_attempts)
    
    # Convert dict result to boolean for backward compatibility
    if isinstance(result, dict):
        return result.get('success', False)
    return result


def schedule_auto_report(app, api_key, interval_hours=6):
    """
    Lên lịch tự động tạo báo cáo mỗi interval_hours giờ với improved error handling.
    
    Args:
        app: Flask app instance
        api_key (str): API key của Gemini
        interval_hours (int): Khoảng thời gian giữa các lần tạo báo cáo (giờ)
    """
    def run_scheduler():
        consecutive_failures = 0
        max_consecutive_failures = 3
        
        with app.app_context():
            while True:
                try:
                    start_time = datetime.now()
                    print(f"[{start_time}] 🚀 Scheduler: Bắt đầu tạo báo cáo tự động...")
                    
                    # Chạy tạo báo cáo với số lần thử tối đa và fallback
                    max_attempts = int(os.getenv('MAX_REPORT_ATTEMPTS', '3'))
                    use_fallback = os.getenv('USE_FALLBACK_ON_500', 'true').lower() == 'true'
                    
                    result = generate_auto_research_report(api_key, max_attempts, use_fallback)
                    
                    if isinstance(result, dict) and result.get('success'):
                        consecutive_failures = 0  # Reset failure counter
                        end_time = datetime.now()
                        duration = (end_time - start_time).total_seconds()
                        report_id = result.get('report_id')
                        print(f"[{end_time}] ✅ Scheduler: Báo cáo #{report_id} tạo thành công trong {duration:.1f}s")
                    elif isinstance(result, bool) and result:
                        consecutive_failures = 0  # Reset failure counter  
                        end_time = datetime.now()
                        duration = (end_time - start_time).total_seconds()
                        print(f"[{end_time}] ✅ Scheduler: Báo cáo tạo thành công trong {duration:.1f}s")
                    else:
                        consecutive_failures += 1
                        error_info = ""
                        if isinstance(result, dict) and result.get('errors'):
                            error_info = f" - Errors: {result['errors'][:2]}"  # Show first 2 errors
                        
                        print(f"[{datetime.now()}] ❌ Scheduler: Tạo báo cáo thất bại ({consecutive_failures}/{max_consecutive_failures}){error_info}")
                        
                        # Nếu thất bại liên tiếp quá nhiều, tăng interval
                        if consecutive_failures >= max_consecutive_failures:
                            extended_interval = interval_hours * 2
                            print(f"[{datetime.now()}] ⚠️ Scheduler: Too many failures, extending interval to {extended_interval}h")
                            time.sleep(extended_interval * 3600)
                            consecutive_failures = 0  # Reset counter
                            continue
                        
                except Exception as e:
                    consecutive_failures += 1
                    print(f"[{datetime.now()}] ❌ Scheduler error ({consecutive_failures}/{max_consecutive_failures}): {e}")
                    
                    # Nếu lỗi liên tiếp quá nhiều, restart scheduler
                    if consecutive_failures >= max_consecutive_failures:
                        print(f"[{datetime.now()}] 🔄 Scheduler: Restarting due to consecutive failures...")
                        time.sleep(300)  # Wait 5 minutes before restart
                        consecutive_failures = 0
                        continue
                
                # Chờ interval_hours giờ trước khi chạy lần tiếp theo
                next_run = datetime.now().replace(microsecond=0) + timedelta(hours=interval_hours)
                print(f"[{datetime.now()}] ⏰ Scheduler: Next run scheduled at {next_run}")
                time.sleep(interval_hours * 3600)
    
    # Import timedelta ở đầu function
    from datetime import timedelta
    
    # Tạo và khởi động thread cho scheduler
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print(f"[{datetime.now()}] 🎯 Auto report scheduler started (interval: {interval_hours}h, max failures: 3)")


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
