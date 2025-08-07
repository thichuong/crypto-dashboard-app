import json
import time
from typing import Dict, Any, Optional
from flask_socketio import SocketIO, emit
from threading import Lock

class ProgressTracker:
    """Theo dõi và phát broadcast tiến độ tạo báo cáo"""
    
    def __init__(self, socketio: Optional[SocketIO] = None):
        self.socketio = socketio
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
        self._emit_progress(session_id)
    
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
        self._emit_progress(session_id)
    
    def update_substep(self, session_id: str, details: str):
        """Cập nhật chi tiết bước con"""
        print(f"[PROGRESS_TRACKER] Update substep for {session_id}: {details}")
        with self.lock:
            if session_id in self.current_progress:
                self.current_progress[session_id]['details'] = details
        self._emit_progress(session_id)
    
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
        self._emit_progress(session_id)
        
        # Xóa session sau 30 giây
        if self.socketio:
            self.socketio.start_background_task(self._cleanup_session, session_id, 30)
    
    def error_progress(self, session_id: str, error_msg: str):
        """Báo lỗi trong quá trình"""
        with self.lock:
            if session_id in self.current_progress:
                progress = self.current_progress[session_id]
                progress['status'] = 'error'
                progress['current_step_name'] = 'Lỗi'
                progress['details'] = error_msg
                progress['end_time'] = time.time()
        self._emit_progress(session_id)
    
    def get_progress(self, session_id: str) -> Dict[str, Any]:
        """Lấy tiến độ hiện tại"""
        with self.lock:
            return self.current_progress.get(session_id, {})
    
    def _emit_progress(self, session_id: str):
        """Phát broadcast tiến độ qua SocketIO (thống nhất cho cả Vercel và local)"""
        if session_id not in self.current_progress:
            return
            
        progress_data = self.current_progress[session_id].copy()
        print(f"[PROGRESS_TRACKER] Emitting progress for {session_id}: {progress_data}")
        
        if self.socketio:
            # Sử dụng SocketIO với polling transport (tương thích cả Vercel và local)
            self.socketio.emit('progress_update', {
                'session_id': session_id,
                'progress': progress_data
            }, room=session_id)
        else:
            print(f"[PROGRESS_TRACKER] Cannot emit progress - no SocketIO available")
    
    def _cleanup_session(self, session_id: str, delay: int):
        """Dọn dẹp session sau delay giây"""
        time.sleep(delay)
        with self.lock:
            if session_id in self.current_progress:
                del self.current_progress[session_id]

# Global instance
progress_tracker = ProgressTracker()

def init_progress_tracker(socketio: SocketIO):
    """Khởi tạo progress tracker với SocketIO"""
    global progress_tracker
    progress_tracker.socketio = socketio
