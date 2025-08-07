import json
import time
import os
from typing import Dict, Any, Optional
from threading import Lock

class ProgressTracker:
    """Theo dõi và lưu trữ tiến độ tạo báo cáo"""
    
    def __init__(self):
        self.current_progress = {}
        self.lock = Lock()
        
    def start_progress(self, session_id: str):
        """Bắt đầu theo dõi tiến độ cho một session"""
        print(f"[PROGRESS_TRACKER] Starting progress for session: {session_id}")
        with self.lock:
            self.current_progress[session_id] = {
                'step': 0,
                'total_steps': 7,
                'current_step_name': 'Khởi tạo...',
                'percentage': 0,
                'status': 'running',
                'start_time': time.time(),
                'details': ''
            }
    
    def update_step(self, session_id: str, step: int, step_name: str, details: str = ''):
        """Cập nhật bước hiện tại"""
        print(f"[PROGRESS_TRACKER] Update step for {session_id}: Step {step} - {step_name}")
        with self.lock:
            if session_id in self.current_progress:
                progress = self.current_progress[session_id]
                progress['step'] = step
                progress['current_step_name'] = step_name
                progress['percentage'] = int((step / progress['total_steps']) * 100)
                progress['details'] = details
                print(f"[PROGRESS_TRACKER] Progress updated: {progress['percentage']}%")
    
    def update_substep(self, session_id: str, details: str):
        """Cập nhật chi tiết bước con"""
        print(f"[PROGRESS_TRACKER] Update substep for {session_id}: {details}")
        with self.lock:
            if session_id in self.current_progress:
                self.current_progress[session_id]['details'] = details
    
    def complete_progress(self, session_id: str, success: bool = True, report_id: int = None):
        """Hoàn thành tiến độ"""
        with self.lock:
            if session_id in self.current_progress:
                progress = self.current_progress[session_id]
                progress['step'] = progress['total_steps']
                progress['percentage'] = 100
                progress['status'] = 'completed' if success else 'error'
                progress['current_step_name'] = 'Hoàn thành!' if success else 'Có lỗi xảy ra'
                progress['report_id'] = report_id
                progress['end_time'] = time.time()
    
    def error_progress(self, session_id: str, error_msg: str):
        """Báo lỗi trong quá trình"""
        with self.lock:
            if session_id in self.current_progress:
                progress = self.current_progress[session_id]
                progress['status'] = 'error'
                progress['current_step_name'] = 'Lỗi'
                progress['details'] = error_msg
                progress['end_time'] = time.time()
    
    def get_progress(self, session_id: str) -> Dict[str, Any]:
        """Lấy tiến độ hiện tại"""
        with self.lock:
            return self.current_progress.get(session_id, {})

# Global instance
progress_tracker = ProgressTracker()
