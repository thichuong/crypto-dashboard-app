"""
Node chuẩn bị dữ liệu và khởi tạo Gemini client
"""
import os
from google import genai
from .base import ReportState, read_prompt_file, replace_date_placeholders, get_realtime_dashboard_data
from ...services.progress_tracker import progress_tracker


def prepare_data_node(state: ReportState) -> ReportState:
    """Node để chuẩn bị dữ liệu và khởi tạo Gemini client"""
    session_id = state["session_id"]
    progress_tracker.update_step(session_id, 1, "Chuẩn bị dữ liệu", "Kiểm tra API key và đọc prompts")
    
    # Kiểm tra API key
    if not state["api_key"] or not isinstance(state["api_key"], str):
        error_msg = "API key không hợp lệ"
        state["error_messages"].append(error_msg)
        state["success"] = False
        progress_tracker.error_progress(session_id, error_msg)
        return state
    
    # Thiết lập đường dẫn tới các prompt files
    current_dir = os.path.dirname(__file__)
    state["research_analysis_prompt_path"] = os.path.abspath(
        os.path.join(current_dir, '..', '..', '..', 'create_report', 'prompt_combined_research_validation.md')
    )
    state["data_validation_prompt_path"] = os.path.abspath(
        os.path.join(current_dir, '..', '..', '..', 'create_report', 'prompt_data_validation.md')
    )
    state["create_report_prompt_path"] = os.path.abspath(
        os.path.join(current_dir, '..', '..', '..', 'create_report', 'prompt_create_report.md')
    )
    
    # Đọc prompt combined research + validation và thay thế ngày tháng
    research_analysis_prompt = read_prompt_file(state["research_analysis_prompt_path"])
    if research_analysis_prompt is None:
        error_msg = "Không thể đọc prompt combined research + validation"
        state["error_messages"].append(error_msg)
        state["success"] = False
        progress_tracker.error_progress(session_id, error_msg)
        return state
        
    state["research_analysis_prompt"] = replace_date_placeholders(research_analysis_prompt)
    
    # Khởi tạo Gemini client
    try:
        client = genai.Client(api_key=state["api_key"])
        state["client"] = client
        state["model"] = "gemini-2.5-flash"
    except Exception as e:
        error_msg = f"Lỗi khi khởi tạo Gemini client: {e}"
        state["error_messages"].append(error_msg)
        state["success"] = False
        progress_tracker.error_progress(session_id, error_msg)
        return state
    
    # Đọc prompt data validation 
    data_validation_prompt = read_prompt_file(state["data_validation_prompt_path"])
    if data_validation_prompt is None:
        error_msg = "Không thể đọc prompt data validation"
        state["error_messages"].append(error_msg)
        state["success"] = False
        progress_tracker.error_progress(session_id, error_msg)
        return state
    
    state["data_validation_prompt"] = data_validation_prompt
    
    # Đọc prompt tạo giao diện
    create_report_prompt = read_prompt_file(state["create_report_prompt_path"])
    if create_report_prompt is None:
        error_msg = "Không thể đọc prompt tạo giao diện"
        state["error_messages"].append(error_msg)
        state["success"] = False
        progress_tracker.error_progress(session_id, error_msg)
        return state
    
    state["create_report_prompt"] = create_report_prompt
    state["current_attempt"] = 0
    
    # Lấy dữ liệu real-time một lần duy nhất và cache vào state
    progress_tracker.update_step(session_id, details="Đang lấy dữ liệu thời gian thực...")
    realtime_data = get_realtime_dashboard_data()
    state["realtime_data"] = realtime_data
    
    if realtime_data:
        progress_tracker.update_step(session_id, details="✓ Đã cache dữ liệu thời gian thực")
    else:
        progress_tracker.update_step(session_id, details="⚠️ Sẽ dùng validation fallback")
    
    state["success"] = True
    return state
