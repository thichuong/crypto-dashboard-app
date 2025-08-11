"""
Node tạo giao diện từ báo cáo nghiên cứu
"""
import time
from google.genai import types
from .base import ReportState
from ...services.progress_tracker import progress_tracker


def create_interface_node(state: ReportState) -> ReportState:
    """Node để tạo giao diện từ báo cáo nghiên cứu"""
    session_id = state["session_id"]
    interface_attempt_key = "interface_attempt"
    if interface_attempt_key not in state:
        state[interface_attempt_key] = 0
    state[interface_attempt_key] += 1
    
    progress_tracker.update_step(session_id, 4, f"Tạo giao diện (lần {state[interface_attempt_key]})", "Chuẩn bị tạo HTML, CSS, JS")
    
    # Tạo request đầy đủ
    full_request = f"{state['create_report_prompt']}\n\n---\n\n**NỘI DUNG BÁO CÁO CẦN XỬ LÝ:**\n\n{state['research_content']}"
    
    interface_contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=full_request),
            ],
        ),
    ]
    
    simple_config = types.GenerateContentConfig(
        temperature=0.3,
        candidate_count=1,
    )
    
    # Retry cho interface generation
    for interface_attempt in range(3):
        try:
            progress_tracker.update_step(session_id, details=f"Gọi AI tạo giao diện (lần {interface_attempt + 1}/3)...")
            interface_response = state["client"].models.generate_content(
                model=state["model"],
                contents=interface_contents,
                config=simple_config
            )
            break
        except Exception as interface_error:
            if interface_attempt < 2:
                wait_time = (interface_attempt + 1) * 20
                progress_tracker.update_step(session_id, details=f"Lỗi tạo giao diện, chờ {wait_time}s...")
                time.sleep(wait_time)
            else:
                error_msg = "Không thể tạo interface sau 3 lần thử"
                state["error_messages"].append(error_msg)
                state["success"] = False
                progress_tracker.error_progress(session_id, error_msg)
                return state
    
    # Kiểm tra interface response
    if not interface_response or not hasattr(interface_response, 'text'):
        error_msg = "Interface response không hợp lệ từ AI"
        state["error_messages"].append(error_msg)
        state["success"] = False
        progress_tracker.error_progress(session_id, error_msg)
        return state
        
    if not interface_response.text:
        error_msg = "Không nhận được nội dung interface từ AI"
        state["error_messages"].append(error_msg)
        state["success"] = False
        progress_tracker.error_progress(session_id, error_msg)
        return state
    
    state["interface_content"] = interface_response.text
    state["success"] = True
    progress_tracker.update_step(session_id, details="✓ Tạo giao diện hoàn thành")
    
    return state
