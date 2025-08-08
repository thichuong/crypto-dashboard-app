import time
from datetime import datetime
from typing import Dict, Any
from threading import Lock

class ProgressTracker:
    """Đơn giản hóa theo dõi tiến độ - chỉ hiển thị step chính với substep queue"""
    
    def __init__(self):
        self.current_progress = {}
        self.substep_queues = {}  # Lưu queue substeps cho mỗi session
        self.lock = Lock()
        
    def start_progress(self, session_id: str):
        """Bắt đầu theo dõi tiến độ cho một session"""
        print(f"[PROGRESS] Starting session: {session_id}")
        with self.lock:
            self.current_progress[session_id] = {
                'step': 0,
                'total_steps': 6,
                'current_step_name': 'Khởi tạo...',
                'percentage': 0,
                'status': 'running',
                'start_time': time.time(),
                'details': '',
                'last_update': time.time()
            }
            # Khởi tạo substep queue cho session
            self.substep_queues[session_id] = []
    
    def update_step(self, session_id: str, step: int, step_name: str, details: str = ''):
        """Cập nhật bước chính"""
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        
        with self.lock:
            if session_id in self.current_progress:
                progress = self.current_progress[session_id]
                progress['step'] = step
                progress['current_step_name'] = f"{timestamp} 🔄 Bước {step}: {step_name}"
                progress['percentage'] = int((step / progress['total_steps']) * 100)
                progress['details'] = f"{timestamp} {details}" if details else ""
                progress['last_update'] = time.time()
                print(f"[PROGRESS] Step {step}: {step_name}")
    
    def update_substep(self, session_id: str, details: str):
        """Cập nhật chi tiết - thêm vào queue và update details hiện tại"""
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        timestamped_details = f"{timestamp} {details}"
        
        with self.lock:
            if session_id in self.current_progress:
                # Update current details
                self.current_progress[session_id]['details'] = timestamped_details
                self.current_progress[session_id]['last_update'] = time.time()
                
                # Add to substep queue
                if session_id not in self.substep_queues:
                    self.substep_queues[session_id] = []
                
                self.substep_queues[session_id].append({
                    'details': timestamped_details,
                    'timestamp': timestamp,
                    'step': self.current_progress[session_id].get('step', 0)
                })
                
                # Giữ tối đa 8 substeps gần nhất
                self.substep_queues[session_id] = self.substep_queues[session_id][-8:]
    
    def complete_progress(self, session_id: str, success: bool = True, report_id: int = None):
        """Hoàn thành tiến độ"""
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        
        with self.lock:
            if session_id in self.current_progress:
                progress = self.current_progress[session_id]
                progress['step'] = progress['total_steps']
                progress['percentage'] = 100
                progress['status'] = 'completed' if success else 'error'
                progress['current_step_name'] = f"{timestamp} ✅ Hoàn thành!" if success else f"{timestamp} ❌ Có lỗi xảy ra"
                progress['report_id'] = report_id
                progress['end_time'] = time.time()
                progress['last_update'] = time.time()
                
                # Clean up substep queue after completion
                if session_id in self.substep_queues:
                    del self.substep_queues[session_id]
    
    def error_progress(self, session_id: str, error_msg: str):
        """Báo lỗi trong quá trình"""
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        
        with self.lock:
            if session_id in self.current_progress:
                progress = self.current_progress[session_id]
                progress['status'] = 'error'
                progress['current_step_name'] = f"{timestamp} ❌ Lỗi"
                progress['details'] = f"{timestamp} {error_msg}"
                progress['end_time'] = time.time()
                progress['last_update'] = time.time()
                
                # Clean up substep queue after error
                if session_id in self.substep_queues:
                    del self.substep_queues[session_id]
    
    def get_progress(self, session_id: str) -> Dict[str, Any]:
        """Lấy tiến độ hiện tại bao gồm substep queue"""
        with self.lock:
            progress = self.current_progress.get(session_id, {})
            if session_id in self.substep_queues:
                progress['substep_queue'] = self.substep_queues[session_id]
            else:
                progress['substep_queue'] = []
            return progress

# Global instance
progress_tracker = ProgressTracker()
