"""
Node trích xuất các khối mã từ phản hồi interface
"""
from .base import ReportState, extract_code_blocks
from ...services.progress_tracker import progress_tracker


def extract_code_node(state: ReportState) -> ReportState:
    """Node để trích xuất các khối mã từ phản hồi interface"""
    session_id = state["session_id"]
    progress_tracker.update_step(session_id, 5, "Trích xuất mã nguồn", "Tách HTML, CSS, JavaScript")
    
    # Kiểm tra interface_content trước khi trích xuất
    if not state.get("interface_content"):
        error_msg = "Không có nội dung interface để trích xuất"
        state["error_messages"].append(error_msg)
        state["success"] = False
        progress_tracker.error_progress(session_id, error_msg)
        return state
    
    # Trích xuất các khối mã
    code_blocks = extract_code_blocks(state["interface_content"])
    
    # Kiểm tra kết quả trích xuất
    if not code_blocks.get("success", False):
        error_msg = "Không thể trích xuất mã nguồn từ phản hồi AI"
        state["error_messages"].append(error_msg)
        state["success"] = False
        progress_tracker.error_progress(session_id, error_msg)
        return state
    
    html_content = code_blocks.get("html", "").strip()
    css_content = code_blocks.get("css", "").strip()
    js_content = code_blocks.get("js", "").strip()
    
    # Set default values nếu CSS/JS trống
    if not css_content:
        css_content = "/* CSS được tạo tự động */\nbody { font-family: Arial, sans-serif; margin: 20px; }"
    
    if not js_content:
        js_content = "// JavaScript được tạo tự động\nconsole.log('Report loaded successfully');"
    
    state["html_content"] = html_content
    state["css_content"] = css_content
    state["js_content"] = js_content
    state["success"] = True
    
    progress_tracker.update_step(session_id, details=f"✓ Trích xuất thành công - HTML: {len(html_content)} chars, CSS: {len(css_content)} chars, JS: {len(js_content)} chars")
    
    return state
