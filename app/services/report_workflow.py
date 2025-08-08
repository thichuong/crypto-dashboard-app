import os
import re
import time
import uuid
import json
import concurrent.futures
from datetime import datetime, timezone
from typing import TypedDict, Optional, List, Literal
from google import genai
from google.genai import types
from langgraph.graph import StateGraph, END
from ..extensions import db
from ..models import Report
from .progress_tracker import progress_tracker


class ReportState(TypedDict):
    """State schema cho report generation workflow"""
    # Session tracking
    session_id: str
    
    # Input parameters
    api_key: str
    max_attempts: int
    
    # File paths
    research_analysis_prompt_path: Optional[str]
    data_validation_prompt_path: Optional[str]
    create_report_prompt_path: Optional[str]
    
    # Processing state
    research_analysis_prompt: Optional[str]
    data_validation_prompt: Optional[str]
    create_report_prompt: Optional[str]
    research_content: Optional[str]
    validation_result: Optional[str]
    interface_content: Optional[str]
    realtime_data: Optional[dict]  # Cache for real-time dashboard data
    
    # Output
    html_content: Optional[str]
    css_content: Optional[str]
    js_content: Optional[str]
    report_id: Optional[int]
    
    # Control flow
    current_attempt: int
    error_messages: List[str]
    success: bool
    
    # Gemini client
    client: Optional[object]
    model: str


def _read_prompt_file(file_path):
    """Đọc nội dung từ tệp prompt."""
    try:
        # Kiểm tra file tồn tại
        if not os.path.exists(file_path):
            print(f"Lỗi: File không tồn tại tại '{file_path}'")
            return None
            
        with open(file_path, 'r', encoding='utf-8') as f:
            template = f.read()
            
            # Kiểm tra nội dung template
            if not template or not isinstance(template, str):
                print(f"Lỗi: Nội dung file trống hoặc không hợp lệ tại '{file_path}'")
                return None
            
            # Đọc toàn bộ nội dung file app/static/colors.css
            current_dir = os.path.dirname(__file__)
            colors = os.path.abspath(os.path.join(current_dir, '..','static', 'css/colors.css'))
            
            # Kiểm tra file colors.css tồn tại
            if not os.path.exists(colors):
                print(f"Cảnh báo: File colors.css không tồn tại tại '{colors}' - sử dụng giá trị mặc định")
                colors_content = ""
            else:
                try:
                    with open(colors, 'r', encoding='utf-8') as f:
                        colors_content = f.read()
                        
                        if colors_content:
                            # Lấy nội dung :root trong file colors.css
                            colors_match = re.search(r':root\s*{([^}]+)}', colors_content, re.DOTALL)
                            if colors_match:
                                colors_content = colors_match.group(1).strip()
                            else:
                                print("Cảnh báo: Không tìm thấy nội dung :root trong file colors.css")
                                colors_content = ""
                        else:
                            colors_content = ""
                except Exception as e:
                    print(f"Lỗi khi đọc file colors.css: {e}")
                    colors_content = ""
                
            # Thay thế biến trong template
            prompt = template.replace("{{ @css_root }}", colors_content)
            return prompt
            
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy tệp prompt tại '{file_path}'")
        return None
    except Exception as e:
        print(f"Lỗi khi đọc file '{file_path}': {e}")
        return None


def _replace_date_placeholders(prompt_text):
    """Thay thế các placeholder về ngày tháng năm trong prompt."""
    now = datetime.now(timezone.utc)
    
    prompt_text = prompt_text.replace("<<@day>>", str(now.day))
    prompt_text = prompt_text.replace("<<@month>>", str(now.month))
    prompt_text = prompt_text.replace("<<@year>>", str(now.year))
    
    return prompt_text


def _extract_code_blocks(response_text):
    """Trích xuất các khối mã nguồn (html, css, js) từ phản hồi của Gemini."""
    # Kiểm tra input
    if not response_text or not isinstance(response_text, str):
        print("Cảnh báo: response_text là None hoặc không phải string")
        return {
            "html": "",
            "css": "/* Lỗi: Không có nội dung phản hồi */",
            "js": "// Lỗi: Không có nội dung phản hồi",
            "success": False
        }
    
    html_match = re.search(r"```html(.*?)```", response_text, re.DOTALL)
    css_match = re.search(r"```css(.*?)```", response_text, re.DOTALL)
    js_match = re.search(r"```javascript(.*?)```", response_text, re.DOTALL)

    if not js_match:
        js_match = re.search(r"```js(.*?)```", response_text, re.DOTALL)

    # Kiểm tra xem có ít nhất HTML hoặc có nội dung hữu ích
    html_content = html_match.group(1).strip() if html_match else ""
    css_content = css_match.group(1).strip() if css_match else "/* Lỗi: Không trích xuất được CSS */"
    js_content = js_match.group(1).strip() if js_match else "// Lỗi: Không trích xuất được JS"
    
    # Xác định trạng thái thành công
    # Coi là thành công nếu có HTML hoặc có ít nhất 2 trong 3 thành phần
    has_html = bool(html_content)
    has_css = css_match is not None
    has_js = js_match is not None
    
    # Hoặc kiểm tra xem có HTML tags trong response không (trường hợp không có code blocks)
    has_html_tags = bool(re.search(r'<html|<!doctype|<div|<body|<head', response_text, re.IGNORECASE))
    
    success = has_html or has_html_tags or (has_css and has_js)

    return {
        "html": html_content,
        "css": css_content,
        "js": js_content,
        "success": success
    }


def _get_realtime_dashboard_data():
    """Lấy dữ liệu thời gian thực từ các services cơ bản"""
    try:
        # Import trực tiếp các service cần thiết (không có RSI)
        from ..services import coingecko, alternative_me
        import concurrent.futures
        
        print("Calling essential real-time data services...")
        
        # Định nghĩa các service calls cơ bản
        def call_global_data():
            return coingecko.get_global_market_data()
        
        def call_btc_data():
            return coingecko.get_btc_price()
        
        def call_fng_data():
            return alternative_me.get_fng_index()
        
        # Gọi tất cả API song song với timeout
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_global = executor.submit(call_global_data)
            future_btc = executor.submit(call_btc_data)
            future_fng = executor.submit(call_fng_data)
            
            # Chờ tất cả hoàn thành với timeout 10 giây
            try:
                global_data, global_error, global_status = future_global.result(timeout=10)
                btc_data, btc_error, btc_status = future_btc.result(timeout=10)
                fng_data, fng_error, fng_status = future_fng.result(timeout=10)
            except concurrent.futures.TimeoutError:
                print("Timeout when getting real-time data")
                return None

        # Xử lý lỗi và tạo fallback data
        if fng_error:
            fng_data = {"fng_value": 50, "fng_value_classification": "Neutral"}

        # Kiểm tra dữ liệu quan trọng
        if global_error and btc_error:
            print("Both global and BTC data failed, using fallback")
            return {
                "market_cap": None,
                "volume_24h": None,
                "btc_price_usd": None,
                "btc_change_24h": None,
                "fng_value": 50,
                "fng_classification": "Neutral",
                "data_source": "fallback"
            }

        # Kết hợp tất cả dữ liệu thành một object duy nhất
        combined_data = {
            **(global_data or {}),
            **(btc_data or {}),
            **(fng_data or {}),
            "data_source": "real_time"
        }
        
        print(f"Successfully got real-time data: {list(combined_data.keys())}")
        return combined_data
        
    except Exception as e:
        print(f"Error getting real-time data: {e}")
        import traceback
        print(traceback.format_exc())
        return None


def _check_report_validation(report_text):
    """
    Kiểm tra kết quả validation của báo cáo.
    
    Returns:
        str: 'PASS', 'FAIL', hoặc 'UNKNOWN'
    """
    # Kiểm tra input
    if not report_text or not isinstance(report_text, str):
        print("Cảnh báo: report_text là None hoặc không phải string")
        return 'UNKNOWN'
    
    # Tìm kết quả kiểm tra cuối cùng
    pass_pattern = re.search(r"KẾT QUẢ KIỂM TRA:\s*PASS", report_text, re.IGNORECASE)
    fail_pattern = re.search(r"KẾT QUẢ KIỂM TRA:\s*FAIL", report_text, re.IGNORECASE)
    
    if pass_pattern:
        return 'PASS'
    elif fail_pattern:
        return 'FAIL'
    else:
        return 'UNKNOWN'


# =============================================================================
# WORKFLOW NODES
# =============================================================================

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
        os.path.join(current_dir, '..', '..', 'create_report', 'prompt_combined_research_validation.md')
    )
    state["data_validation_prompt_path"] = os.path.abspath(
        os.path.join(current_dir, '..', '..', 'create_report', 'prompt_data_validation.md')
    )
    state["create_report_prompt_path"] = os.path.abspath(
        os.path.join(current_dir, '..', '..', 'create_report', 'prompt_create_report.md')
    )
    
    # Đọc prompt combined research + validation và thay thế ngày tháng
    research_analysis_prompt = _read_prompt_file(state["research_analysis_prompt_path"])
    if research_analysis_prompt is None:
        error_msg = "Không thể đọc prompt combined research + validation"
        state["error_messages"].append(error_msg)
        state["success"] = False
        progress_tracker.error_progress(session_id, error_msg)
        return state
        
    state["research_analysis_prompt"] = _replace_date_placeholders(research_analysis_prompt)
    
    # Khởi tạo Gemini client
    try:
        client = genai.Client(api_key=state["api_key"])
        state["client"] = client
        state["model"] = "gemini-2.5-pro"
    except Exception as e:
        error_msg = f"Lỗi khi khởi tạo Gemini client: {e}"
        state["error_messages"].append(error_msg)
        state["success"] = False
        progress_tracker.error_progress(session_id, error_msg)
        return state
    
    # Đọc prompt data validation 
    data_validation_prompt = _read_prompt_file(state["data_validation_prompt_path"])
    if data_validation_prompt is None:
        error_msg = "Không thể đọc prompt data validation"
        state["error_messages"].append(error_msg)
        state["success"] = False
        progress_tracker.error_progress(session_id, error_msg)
        return state
    
    state["data_validation_prompt"] = data_validation_prompt
    
    # Đọc prompt tạo giao diện
    create_report_prompt = _read_prompt_file(state["create_report_prompt_path"])
    if create_report_prompt is None:
        error_msg = "Không thể đọc prompt tạo giao diện"
        state["error_messages"].append(error_msg)
        state["success"] = False
        progress_tracker.error_progress(session_id, error_msg)
        return state
    
    state["create_report_prompt"] = create_report_prompt
    state["current_attempt"] = 0
    
    # Lấy dữ liệu real-time một lần duy nhất và cache vào state
    progress_tracker.update_substep(session_id, "Đang lấy dữ liệu thời gian thực...")
    realtime_data = _get_realtime_dashboard_data()
    state["realtime_data"] = realtime_data
    
    if realtime_data:
        progress_tracker.update_substep(session_id, "✓ Đã cache dữ liệu thời gian thực")
    else:
        progress_tracker.update_substep(session_id, "⚠️ Sẽ dùng validation fallback")
    
    state["success"] = True
    return state


def research_deep_node(state: ReportState) -> ReportState:
    """Node để thực hiện nghiên cứu sâu + validation với Google Search và real-time data trong 1 lần gọi"""
    session_id = state["session_id"]
    state["current_attempt"] += 1
    
    progress_tracker.update_step(session_id, 2, f"Research + Validation (lần {state['current_attempt']})", 
                               "Cấu hình AI tools, Google Search và thực hiện combined research + validation")
    
    try:
        # Chuẩn bị combined prompt với real-time data
        combined_prompt = state["research_analysis_prompt"]
        
        # Thêm real-time data vào prompt
        realtime_data = state.get("realtime_data")
        if realtime_data:
            # Inject real-time data vào combined prompt
            combined_prompt = combined_prompt.replace(
                "{{REAL_TIME_DATA}}", 
                json.dumps(realtime_data, ensure_ascii=False, indent=2)
            )
            progress_tracker.update_substep(session_id, "✓ Đã inject real-time data vào combined prompt")
        else:
            # Thay thế bằng fallback message
            combined_prompt = combined_prompt.replace(
                "{{REAL_TIME_DATA}}", 
                "{\n  \"notice\": \"Real-time data không khả dụng, sử dụng Google Search để lấy dữ liệu mới nhất\"\n}"
            )
            progress_tracker.update_substep(session_id, "⚠️ Không có real-time data, sử dụng Google Search")
        
        # Cấu hình tools với thinking budget cao hơn cho combined task
        tools = [
            types.Tool(googleSearch=types.GoogleSearch()),
        ]
        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                thinking_budget=30000,  # Tăng thinking budget cho combined task
            ),
            tools=tools,
            temperature=0.7,
            candidate_count=1,
        )
        
        # Tạo request content với combined prompt
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=combined_prompt),
                ],
            ),
        ]
        
        # Retry cho combined API call
        for api_attempt in range(3):
            try:
                progress_tracker.update_substep(session_id, f"Gọi Combined AI API (lần {api_attempt + 1}/3)...")
                response = state["client"].models.generate_content(
                    model=state["model"],
                    contents=contents,
                    config=generate_content_config
                )
                break
            except Exception as api_error:
                if api_attempt < 2:
                    wait_time = (api_attempt + 1) * 45  # Longer wait for complex combined calls
                    progress_tracker.update_substep(session_id, f"Lỗi Combined API, chờ {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise api_error
        
        # Kiểm tra response
        if not response or not hasattr(response, 'text'):
            error_msg = f"Lần thử {state['current_attempt']}: Combined response không hợp lệ từ AI"
            state["error_messages"].append(error_msg)
            progress_tracker.update_substep(session_id, error_msg)
            state["success"] = False
            return state
            
        full_response_text = response.text
        
        if not full_response_text:
            error_msg = f"Lần thử {state['current_attempt']}: Không nhận được nội dung từ Combined AI"
            state["error_messages"].append(error_msg)
            progress_tracker.update_substep(session_id, error_msg)
            state["success"] = False
            return state
        
        # Parse combined response để extract research content và validation result
        progress_tracker.update_substep(session_id, "Parsing combined response...")
        
        # Tìm validation result trong response
        validation_result = _check_report_validation(full_response_text)
        state["validation_result"] = validation_result
        
        # Extract research content (everything before validation summary hoặc toàn bộ nếu không có)
        validation_summary_start = full_response_text.find("### 🔍 VALIDATION SUMMARY")
        if validation_summary_start > 0:
            # Có validation summary, lấy phần trước đó làm research content
            research_content = full_response_text[:validation_summary_start].strip()
        else:
            # Không có validation summary riêng, lấy toàn bộ
            research_content = full_response_text
        
        state["research_content"] = research_content
        
        # Set success based on validation result
        if validation_result == "PASS":
            state["success"] = True
            progress_tracker.update_substep(session_id, f"✓ Combined Research + Validation PASS")
        elif validation_result == "FAIL":
            state["success"] = False
            progress_tracker.update_substep(session_id, f"✗ Combined Research + Validation FAIL")
        else:
            # UNKNOWN validation result - treat as success but log warning
            state["success"] = True
            state["validation_result"] = "UNKNOWN"
            progress_tracker.update_substep(session_id, f"? Combined Response với validation UNKNOWN")
        
        # Log response length for debugging
        progress_tracker.update_substep(session_id, 
            f"✓ Combined response: {len(full_response_text)} chars, "
            f"research: {len(research_content)} chars, "
            f"validation: {validation_result}")
        
    except Exception as e:
        error_msg = f"Lần thử {state['current_attempt']}: Lỗi khi gọi Combined AI: {e}"
        state["error_messages"].append(error_msg)
        progress_tracker.update_substep(session_id, error_msg)
        state["success"] = False
    
    return state


def validate_report_node(state: ReportState) -> ReportState:
    """Node để parse và verify kết quả validation từ combined research response"""
    session_id = state["session_id"]
    progress_tracker.update_step(session_id, 3, "Parse validation result", "Kiểm tra kết quả validation từ combined response")
    
    if not state["research_content"]:
        state["validation_result"] = "UNKNOWN"
        progress_tracker.update_substep(session_id, "Không có research content để parse validation")
        state["success"] = False
        return state
    
    try:
        # Parse validation result từ research_content
        research_content = state["research_content"]
        
        # Kiểm tra xem đã có validation result từ research_deep_node chưa
        current_validation_result = state.get("validation_result", "UNKNOWN")
        
        if current_validation_result == "PASS":
            progress_tracker.update_substep(session_id, "✓ Combined research đã validation PASS")
            state["success"] = True
            return state
        
        elif current_validation_result == "FAIL":
            progress_tracker.update_substep(session_id, "✗ Combined research validation FAIL - cần retry")
            state["success"] = False
            return state
        
        else:
            # UNKNOWN hoặc chưa có validation result, thực hiện parsing bổ sung
            progress_tracker.update_substep(session_id, "? Parsing validation result từ response...")
            
            # Re-check validation result trong toàn bộ response (including research_content)
            full_response = state.get("research_content", "")
            
            # Tìm validation patterns trong response
            validation_result = _check_report_validation(full_response)
            state["validation_result"] = validation_result
            
            if validation_result == "PASS":
                progress_tracker.update_substep(session_id, "✓ Parsed validation result: PASS")
                state["success"] = True
                return state
            
            elif validation_result == "FAIL":
                progress_tracker.update_substep(session_id, "✗ Parsed validation result: FAIL")
                state["success"] = False
                return state
            
            else:
                # Vẫn UNKNOWN, thực hiện fallback validation logic
                progress_tracker.update_substep(session_id, "? Validation result vẫn UNKNOWN, sử dụng fallback logic...")
                
                # Fallback validation - kiểm tra content quality
                if len(research_content) > 2000:  # Combined response sẽ dài hơn
                    content_lower = research_content.lower()
                    
                    # Kiểm tra các elements cơ bản
                    has_btc = any(keyword in content_lower for keyword in ['bitcoin', 'btc'])
                    has_analysis = any(keyword in content_lower for keyword in ['phân tích', 'analysis', 'thị trường', 'market'])
                    has_numbers = re.search(r'\d+\.?\d*\s*%|\$\d+', research_content)
                    has_fng = any(keyword in content_lower for keyword in ['fear', 'greed', 'sợ hãi', 'tham lam'])
                    
                    # Kiểm tra có validation table không
                    has_validation_table = any(keyword in research_content for keyword in [
                        'Bảng Đối chiếu', 'Validation Summary', '| Dữ liệu', '| BTC Price'
                    ])
                    
                    # Combined response cần có nhiều elements hơn
                    quality_score = sum([has_btc, has_analysis, has_numbers, has_fng, has_validation_table])
                    
                    if quality_score >= 4:  # Cần ít nhất 4/5 elements
                        progress_tracker.update_substep(session_id, f"✓ Fallback validation PASS (quality score: {quality_score}/5)")
                        state["validation_result"] = "PASS"
                        state["success"] = True
                        return state
                    else:
                        progress_tracker.update_substep(session_id, f"✗ Fallback validation FAIL (quality score: {quality_score}/5)")
                        state["validation_result"] = "FAIL"
                        state["success"] = False
                        return state
                else:
                    progress_tracker.update_substep(session_id, "✗ Combined response quá ngắn")
                    state["validation_result"] = "FAIL"
                    state["success"] = False
                    return state
        
    except Exception as e:
        error_msg = f"Lần thử {state['current_attempt']}: Lỗi khi parse validation result: {e}"
        state["error_messages"].append(error_msg)
        state["validation_result"] = "UNKNOWN"
        state["success"] = False
        progress_tracker.update_substep(session_id, error_msg)
    
    return state


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
        temperature=0.7,
        candidate_count=1,
    )
    
    # Retry cho interface generation
    for interface_attempt in range(3):
        try:
            progress_tracker.update_substep(session_id, f"Gọi AI tạo giao diện (lần {interface_attempt + 1}/3)...")
            interface_response = state["client"].models.generate_content(
                model=state["model"],
                contents=interface_contents,
                config=simple_config
            )
            break
        except Exception as interface_error:
            if interface_attempt < 2:
                wait_time = (interface_attempt + 1) * 20
                progress_tracker.update_substep(session_id, f"Lỗi tạo giao diện, chờ {wait_time}s...")
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
    progress_tracker.update_substep(session_id, "✓ Tạo giao diện hoàn thành")
    
    return state


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
    code_blocks = _extract_code_blocks(state["interface_content"])
    
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
    
    progress_tracker.update_substep(session_id, f"✓ Trích xuất thành công - HTML: {len(html_content)} chars, CSS: {len(css_content)} chars, JS: {len(js_content)} chars")
    
    return state


def _save_to_database_with_context(state: ReportState, session_id: str) -> ReportState:
    """Helper function để lưu database với proper context"""
    try:
        # Tạo báo cáo mới và lưu vào database
        progress_tracker.update_substep(session_id, "Tạo record báo cáo mới...")
        new_report = Report(
            html_content=state["html_content"],
            css_content=state["css_content"],
            js_content=state["js_content"]
        )
        
        progress_tracker.update_substep(session_id, "Đang commit vào database...")
        db.session.add(new_report)
        db.session.commit()
        
        state["report_id"] = new_report.id
        state["success"] = True
        
        progress_tracker.complete_progress(session_id, True, new_report.id)
        
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


def save_database_node(state: ReportState) -> ReportState:
    """Node để lưu báo cáo vào database"""
    session_id = state["session_id"]
    progress_tracker.update_step(session_id, 6, "Lưu báo cáo", "Đang lưu HTML, CSS, JS vào cơ sở dữ liệu")
    
    try:
        # Import Flask app để có application context
        from .. import create_app
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


# =============================================================================
# CONDITIONAL ROUTING
# =============================================================================

def should_retry_or_continue(state: ReportState) -> Literal["retry", "continue", "end"]:
    """Quyết định hướng đi tiếp theo sau validation"""
    
    # Nếu validation PASS, tiếp tục
    if state["validation_result"] == "PASS":
        return "continue"
    
    # Nếu đã hết số lần thử, kết thúc
    if state["current_attempt"] >= state["max_attempts"]:
        return "end"
    
    # Còn lần thử, retry
    return "retry"


def should_retry_interface_or_continue(state: ReportState) -> Literal["retry_interface", "continue", "end"]:
    """Quyết định hướng đi tiếp theo sau extract_code"""
    
    # Nếu extract thành công, tiếp tục
    if state["success"]:
        return "continue"
    
    # Kiểm tra số lần thử interface riêng (tối đa 3 lần)
    interface_attempt = state.get("interface_attempt", 0)
    if interface_attempt >= 3:
        return "end"
    
    # Còn lần thử interface, retry
    return "retry_interface"


# =============================================================================
# WORKFLOW CONSTRUCTION
# =============================================================================

def create_report_workflow():
    """Tạo và cấu hình LangGraph workflow"""
    
    workflow = StateGraph(ReportState)
    
    # Thêm các nodes
    workflow.add_node("prepare_data", prepare_data_node)
    workflow.add_node("research_deep", research_deep_node)
    workflow.add_node("validate_report", validate_report_node)
    workflow.add_node("create_interface", create_interface_node)
    workflow.add_node("extract_code", extract_code_node)
    workflow.add_node("save_database", save_database_node)
    
    # Thiết lập entry point
    workflow.set_entry_point("prepare_data")
    
    # Thiết lập các edges 
    workflow.add_edge("prepare_data", "research_deep")
    workflow.add_edge("research_deep", "validate_report")
    
    # Conditional routing sau validation
    workflow.add_conditional_edges(
        "validate_report",
        should_retry_or_continue,
        {
            "retry": "research_deep",
            "continue": "create_interface",
            "end": END
        }
    )
    
    workflow.add_edge("create_interface", "extract_code")
    
    # Conditional routing sau extract_code
    workflow.add_conditional_edges(
        "extract_code",
        should_retry_interface_or_continue,
        {
            "retry_interface": "create_interface",
            "continue": "save_database",
            "end": END
        }
    )
    
    workflow.add_edge("save_database", END)
    
    return workflow.compile()


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def generate_auto_research_report_langgraph(api_key: str, max_attempts: int = 3, session_id: str = None) -> dict:
    """
    Hàm chính để tạo báo cáo sử dụng LangGraph workflow.
    
    Args:
        api_key (str): API key của Gemini
        max_attempts (int): Số lần thử tối đa để tạo báo cáo PASS
        session_id (str): Session ID để tracking progress (tự tạo nếu None)
        
    Returns:
        dict: {
            'success': bool,
            'session_id': str,
            'report_id': int | None,
            'errors': list
        }
    """
    
    # Tạo session_id nếu chưa có
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Khởi tạo progress tracking
    progress_tracker.start_progress(session_id)
    
    # Khởi tạo state 
    initial_state = ReportState(
        session_id=session_id,
        api_key=api_key,
        max_attempts=max_attempts,
        research_analysis_prompt_path=None,
        data_validation_prompt_path=None,
        create_report_prompt_path=None,
        research_analysis_prompt=None,
        data_validation_prompt=None,
        create_report_prompt=None,
        research_content=None,
        validation_result=None,
        interface_content=None,
        realtime_data=None,
        html_content=None,
        css_content=None,
        js_content=None,
        report_id=None,
        current_attempt=0,
        error_messages=[],
        success=False,
        client=None,
        model="gemini-2.5-pro"
    )
    
    try:
        # Import Flask app để đảm bảo application context
        from .. import create_app
        from flask import current_app
        
        # Kiểm tra và tạo application context nếu cần
        try:
            # Test xem có app context không
            _ = current_app.name
            # Nếu có rồi, chạy trực tiếp
            workflow = create_report_workflow()
            final_state = workflow.invoke(initial_state)
        except RuntimeError:
            # Chưa có app context, tạo mới
            app = create_app()
            with app.app_context():
                workflow = create_report_workflow()
                final_state = workflow.invoke(initial_state)
        
        # Kiểm tra kết quả
        if final_state["success"] and final_state.get("report_id"):
            return {
                'success': True,
                'session_id': session_id,
                'report_id': final_state["report_id"],
                'errors': []
            }
        else:
            progress_tracker.error_progress(session_id, "Workflow hoàn thành nhưng không thành công")
            print(f"[{datetime.now()}] Lỗi khi tạo báo cáo tự động:")
            for error in final_state["error_messages"]:
                print(f"  - {error}")
            return {
                'success': False,
                'session_id': session_id,
                'report_id': None,
                'errors': final_state["error_messages"]
            }
            
    except Exception as e:
        error_msg = f"Lỗi workflow: {e}"
        progress_tracker.error_progress(session_id, error_msg)
        print(f"[{datetime.now()}] {error_msg}")
        return {
            'success': False,
            'session_id': session_id,
            'report_id': None,
            'errors': [error_msg]
        }
