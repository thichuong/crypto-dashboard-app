"""
Node tạo giao diện theo từng thành phần riêng biệt (HTML, JS, CSS)
"""
import time
import re
from google.genai import types
from .base import ReportState, read_prompt_file
from ...services.progress_tracker import progress_tracker


def create_html_node(state: ReportState) -> ReportState:
    """Node để tạo HTML từ báo cáo nghiên cứu"""
    session_id = state["session_id"]
    html_attempt_key = "html_attempt"
    if html_attempt_key not in state:
        state[html_attempt_key] = 0
    state[html_attempt_key] += 1
    
    # Bước tạo HTML sau khi đã có nội dung báo cáo markdown
    progress_tracker.update_step(session_id, 5, f"Tạo HTML (lần {state[html_attempt_key]})", "Tạo cấu trúc HTML từ nội dung báo cáo")
    
    # Đọc prompt tạo HTML
    html_prompt = read_prompt_file('prompt_create_html.md')
    if not html_prompt:
        error_msg = "Không thể đọc prompt tạo HTML"
        state["error_messages"].append(error_msg)
        state["success"] = False
        progress_tracker.error_progress(session_id, error_msg)
        return state
    
    # Tạo request tạo HTML
    # Chuyển nội dung báo cáo markdown thành HTML semantic
    report_md = state.get('report_content') or state.get('research_content', '')
    full_request = f"{html_prompt}\n\n---\n\n**NỘI DUNG BÁO CÁO:**\n\n{report_md}"
    
    html_contents = [
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
    
    # Retry cho HTML generation
    for html_attempt in range(3):
        try:
            progress_tracker.update_step(session_id, details=f"Gọi AI tạo HTML (lần {html_attempt + 1}/3)...")
            html_response = state["client"].models.generate_content(
                model=state["model"],
                contents=html_contents,
                config=simple_config
            )
            break
        except Exception as html_error:
            if html_attempt < 2:
                wait_time = (html_attempt + 1) * 20
                progress_tracker.update_step(session_id, details=f"Lỗi tạo HTML, chờ {wait_time}s...")
                time.sleep(wait_time)
            else:
                error_msg = f"Không thể tạo HTML sau 3 lần thử: {str(html_error)}"
                state["error_messages"].append(error_msg)
                state["success"] = False
                progress_tracker.error_progress(session_id, error_msg)
                return state
    
    # Kiểm tra HTML response
    if not html_response or not hasattr(html_response, 'text') or not html_response.text:
        error_msg = "Không nhận được nội dung HTML từ AI"
        state["error_messages"].append(error_msg)
        state["success"] = False
        progress_tracker.error_progress(session_id, error_msg)
        return state
    
    # Trích xuất HTML content
    html_content = _extract_html(html_response.text)
    if not html_content:
        error_msg = "Không thể trích xuất HTML từ phản hồi AI"
        state["error_messages"].append(error_msg)
        state["success"] = False
        progress_tracker.error_progress(session_id, error_msg)
        return state
    
    state["html_content"] = html_content
    state["success"] = True
    progress_tracker.update_step(session_id, details=f"✓ Tạo HTML hoàn thành - {len(html_content)} chars")
    
    return state


def create_javascript_node(state: ReportState) -> ReportState:
    """Node để tạo JavaScript từ báo cáo nghiên cứu"""
    session_id = state["session_id"]
    js_attempt_key = "js_attempt"
    if js_attempt_key not in state:
        state[js_attempt_key] = 0
    state[js_attempt_key] += 1
    
    # Bước tạo JavaScript
    progress_tracker.update_step(session_id, 6, f"Tạo JavaScript (lần {state[js_attempt_key]})", "Tạo tương tác JS từ nội dung HTML")
    
    # Đọc prompt tạo JavaScript
    js_prompt = read_prompt_file('prompt_create_javascript.md')
    if not js_prompt:
        error_msg = "Không thể đọc prompt tạo JavaScript"
        state["error_messages"].append(error_msg)
        state["success"] = False
        progress_tracker.error_progress(session_id, error_msg)
        return state
    
    # Tạo request tạo JS (bao gồm HTML đã tạo để tương thích)
    html_context = state.get("html_content", "")
    full_request = f"{js_prompt}\n\n---\n\n**HTML ĐÃ TẠO:**\n\n{html_context}"
    
    js_contents = [
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
    
    # Retry cho JS generation
    for js_attempt in range(3):
        try:
            progress_tracker.update_step(session_id, details=f"Gọi AI tạo JavaScript (lần {js_attempt + 1}/3)...")
            js_response = state["client"].models.generate_content(
                model=state["model"],
                contents=js_contents,
                config=simple_config
            )
            break
        except Exception as js_error:
            if js_attempt < 2:
                wait_time = (js_attempt + 1) * 20
                progress_tracker.update_step(session_id, details=f"Lỗi tạo JavaScript, chờ {wait_time}s...")
                time.sleep(wait_time)
            else:
                error_msg = f"Không thể tạo JavaScript sau 3 lần thử: {str(js_error)}"
                state["error_messages"].append(error_msg)
                state["success"] = False
                progress_tracker.error_progress(session_id, error_msg)
                return state
    
    # Kiểm tra JS response
    if not js_response or not hasattr(js_response, 'text') or not js_response.text:
        error_msg = "Không nhận được nội dung JavaScript từ AI"
        state["error_messages"].append(error_msg)
        state["success"] = False
        progress_tracker.error_progress(session_id, error_msg)
        return state
    
    # Trích xuất JS content
    js_content = _extract_javascript(js_response.text)
    if not js_content:
        js_content = "// JavaScript được tạo tự động\nconsole.log('Report loaded successfully');"
    
    state["js_content"] = js_content
    state["success"] = True
    progress_tracker.update_step(session_id, details=f"✓ Tạo JavaScript hoàn thành - {len(js_content)} chars")
    
    return state


def create_css_node(state: ReportState) -> ReportState:
    """Node để tạo CSS từ báo cáo nghiên cứu"""
    session_id = state["session_id"]
    css_attempt_key = "css_attempt"
    if css_attempt_key not in state:
        state[css_attempt_key] = 0
    state[css_attempt_key] += 1
    
    # Bước tạo CSS
    progress_tracker.update_step(session_id, 7, f"Tạo CSS (lần {state[css_attempt_key]})", "Tạo styling CSS từ nội dung HTML")
    
    # Đọc prompt tạo CSS
    css_prompt = read_prompt_file('prompt_create_css.md')
    if not css_prompt:
        error_msg = "Không thể đọc prompt tạo CSS"
        state["error_messages"].append(error_msg)
        state["success"] = False
        progress_tracker.error_progress(session_id, error_msg)
        return state
    
    # Tạo request tạo CSS (bao gồm HTML đã tạo để tương thích)
    html_context = state.get("html_content", "")
    full_request = f"{css_prompt}\n\n---\n\n**HTML ĐÃ TẠO:**\n\n{html_context}"
    
    css_contents = [
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
    
    # Retry cho CSS generation
    for css_attempt in range(3):
        try:
            progress_tracker.update_step(session_id, details=f"Gọi AI tạo CSS (lần {css_attempt + 1}/3)...")
            css_response = state["client"].models.generate_content(
                model=state["model"],
                contents=css_contents,
                config=simple_config
            )
            break
        except Exception as css_error:
            if css_attempt < 2:
                wait_time = (css_attempt + 1) * 20
                progress_tracker.update_step(session_id, details=f"Lỗi tạo CSS, chờ {wait_time}s...")
                time.sleep(wait_time)
            else:
                error_msg = f"Không thể tạo CSS sau 3 lần thử: {str(css_error)}"
                state["error_messages"].append(error_msg)
                state["success"] = False
                progress_tracker.error_progress(session_id, error_msg)
                return state
    
    # Kiểm tra CSS response
    if not css_response or not hasattr(css_response, 'text') or not css_response.text:
        error_msg = "Không nhận được nội dung CSS từ AI"
        state["error_messages"].append(error_msg)
        state["success"] = False
        progress_tracker.error_progress(session_id, error_msg)
        return state
    
    # Trích xuất CSS content
    css_content = _extract_css(css_response.text)
    if not css_content:
        css_content = "/* CSS được tạo tự động */\nbody { font-family: Arial, sans-serif; margin: 20px; }"
    
    state["css_content"] = css_content
    state["success"] = True
    progress_tracker.update_step(session_id, details=f"✓ Tạo CSS hoàn thành - {len(css_content)} chars")
    
    return state


def _extract_html(response_text):
    """Trích xuất nội dung HTML từ phản hồi"""
    if not response_text:
        return ""
    
    # Tìm khối HTML
    html_match = re.search(r"```html(.*?)```", response_text, re.DOTALL)
    if html_match:
        return html_match.group(1).strip()
    
    # Nếu không có khối mã, kiểm tra xem có HTML tags không
    if re.search(r'<html|<!doctype|<div|<body|<head', response_text, re.IGNORECASE):
        return response_text.strip()
    
    return ""


def _extract_javascript(response_text):
    """Trích xuất nội dung JavaScript từ phản hồi"""
    if not response_text:
        return ""
    
    # Tìm khối JavaScript
    js_match = re.search(r"```javascript(.*?)```", response_text, re.DOTALL)
    if not js_match:
        js_match = re.search(r"```js(.*?)```", response_text, re.DOTALL)
    
    if js_match:
        return js_match.group(1).strip()
    
    return ""


def _extract_css(response_text):
    """Trích xuất nội dung CSS từ phản hồi"""
    if not response_text:
        return ""
    
    # Tìm khối CSS
    css_match = re.search(r"```css(.*?)```", response_text, re.DOTALL)
    if css_match:
        return css_match.group(1).strip()
    
    return ""
