import os
import re
import time
import uuid
import json
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
            "js": "// Lỗi: Không có nội dung phản hồi"
        }
    
    html_match = re.search(r"```html(.*?)```", response_text, re.DOTALL)
    css_match = re.search(r"```css(.*?)```", response_text, re.DOTALL)
    js_match = re.search(r"```javascript(.*?)```", response_text, re.DOTALL)

    if not js_match:
        js_match = re.search(r"```js(.*?)```", response_text, re.DOTALL)

    return {
        "html": html_match.group(1).strip() if html_match else "",
        "css": css_match.group(1).strip() if css_match else "/* Lỗi: Không trích xuất được CSS */",
        "js": js_match.group(1).strip() if js_match else "// Lỗi: Không trích xuất được JS"
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
    print(f"[PROGRESS] Starting prepare_data_node for session {session_id}")
    progress_tracker.update_step(session_id, 1, "Chuẩn bị dữ liệu và khởi tạo AI...", "Đang kiểm tra API key và đọc prompts")
    
    print(f"[{datetime.now()}] Bắt đầu tạo báo cáo tự động...")
    
    # Kiểm tra API key
    if not state["api_key"] or not isinstance(state["api_key"], str):
        error_msg = "API key không hợp lệ"
        state["error_messages"].append(error_msg)
        state["success"] = False
        progress_tracker.error_progress(session_id, error_msg)
        print(f"[PROGRESS] Error in prepare_data_node: {error_msg}")
        return state
    
    # Thiết lập đường dẫn tới các prompt files
    progress_tracker.update_substep(session_id, "Đang thiết lập đường dẫn prompts...")
    current_dir = os.path.dirname(__file__)
    state["research_analysis_prompt_path"] = os.path.abspath(
        os.path.join(current_dir, '..', '..', 'create_report', 'prompt_research_analysis.md')
    )
    state["data_validation_prompt_path"] = os.path.abspath(
        os.path.join(current_dir, '..', '..', 'create_report', 'prompt_data_validation.md')
    )
    state["create_report_prompt_path"] = os.path.abspath(
        os.path.join(current_dir, '..', '..', 'create_report', 'prompt_create_report.md')
    )
    
    print(f"Research analysis prompt path: {state['research_analysis_prompt_path']}")
    print(f"Data validation prompt path: {state['data_validation_prompt_path']}")
    print(f"Create report prompt path: {state['create_report_prompt_path']}")
    
    # Đọc prompt research analysis và thay thế ngày tháng
    progress_tracker.update_substep(session_id, "Đang đọc prompt nghiên cứu...")
    research_analysis_prompt = _read_prompt_file(state["research_analysis_prompt_path"])
    if research_analysis_prompt is None:
        error_msg = "Không thể đọc prompt research analysis"
        state["error_messages"].append(error_msg)
        state["success"] = False
        progress_tracker.error_progress(session_id, error_msg)
        print(f"[PROGRESS] Error in prepare_data_node: {error_msg}")
        return state
        
    state["research_analysis_prompt"] = _replace_date_placeholders(research_analysis_prompt)
    
    # Khởi tạo Gemini client
    progress_tracker.update_substep(session_id, "Đang khởi tạo Gemini AI...")
    try:
        client = genai.Client(api_key=state["api_key"])
        state["client"] = client
        state["model"] = "gemini-2.5-pro"
        print("Đã khởi tạo Gemini client thành công")
    except Exception as e:
        error_msg = f"Lỗi khi khởi tạo Gemini client: {e}"
        state["error_messages"].append(error_msg)
        state["success"] = False
        progress_tracker.error_progress(session_id, error_msg)
        print(f"[PROGRESS] Error in prepare_data_node: {error_msg}")
        return state
    
    # Đọc prompt data validation 
    progress_tracker.update_substep(session_id, "Đang đọc prompt xác thực dữ liệu...")
    data_validation_prompt = _read_prompt_file(state["data_validation_prompt_path"])
    if data_validation_prompt is None:
        error_msg = "Không thể đọc prompt data validation"
        state["error_messages"].append(error_msg)
        state["success"] = False
        progress_tracker.error_progress(session_id, error_msg)
        print(f"[PROGRESS] Error in prepare_data_node: {error_msg}")
        return state
    
    state["data_validation_prompt"] = data_validation_prompt
    
    # Đọc prompt tạo giao diện
    progress_tracker.update_substep(session_id, "Đang đọc prompt tạo giao diện...")
    create_report_prompt = _read_prompt_file(state["create_report_prompt_path"])
    if create_report_prompt is None:
        error_msg = "Không thể đọc prompt tạo giao diện"
        state["error_messages"].append(error_msg)
        state["success"] = False
        progress_tracker.error_progress(session_id, error_msg)
        print(f"[PROGRESS] Error in prepare_data_node: {error_msg}")
        return state
    
    state["create_report_prompt"] = create_report_prompt
    state["current_attempt"] = 0
    state["success"] = True
    
    print(f"[PROGRESS] Completed prepare_data_node for session {session_id}")
    return state


def research_deep_node(state: ReportState) -> ReportState:
    """Node để thực hiện nghiên cứu sâu với Google Search"""
    session_id = state["session_id"]
    state["current_attempt"] += 1
    
    progress_tracker.update_step(session_id, 2, f"Thu thập dữ liệu từ internet (lần {state['current_attempt']})...", 
                               "Đang cấu hình Google Search và AI tools")
    
    print(f"Đang tạo báo cáo nghiên cứu sâu (lần thử {state['current_attempt']}/{state['max_attempts']})...")
    
    try:
        # Cấu hình tools và thinking mode với giới hạn budget
        progress_tracker.update_substep(session_id, "Đang cấu hình AI tools và Google Search...")
        tools = [
            types.Tool(googleSearch=types.GoogleSearch()),
        ]
        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                thinking_budget=32768,  # Giá trị tối đa cho phép (128-32768)
            ),
            tools=tools,
            temperature=0.7,  # Thêm temperature để ổn định
            candidate_count=1,  # Chỉ tạo 1 candidate
        )
        
        # Tạo request content với Google Search tools
        progress_tracker.update_substep(session_id, "Đang chuẩn bị request content...")
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=state["research_analysis_prompt"]),
                ],
            ),
        ]
        
        # Thêm timeout và retry cho API call
        for api_attempt in range(3):  # Retry 3 lần cho mỗi attempt
            try:
                progress_tracker.update_substep(session_id, f"Đang gọi AI API (lần {api_attempt + 1}/3)...")
                print(f"API call attempt {api_attempt + 1}/3...")
                response = state["client"].models.generate_content(
                    model=state["model"],
                    contents=contents,
                    config=generate_content_config
                )
                break  # Thành công, thoát khỏi retry loop
            except Exception as api_error:
                print(f"API attempt {api_attempt + 1} failed: {api_error}")
                if api_attempt < 2:  # Không phải lần cuối
                    wait_time = (api_attempt + 1) * 30  # Exponential backoff: 30s, 60s
                    progress_tracker.update_substep(session_id, f"Lỗi API, đang chờ {wait_time}s trước khi thử lại...")
                    print(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    raise api_error  # Ném lỗi sau khi hết retry
        
        # Kiểm tra response
        progress_tracker.update_substep(session_id, "Đang xử lý phản hồi từ AI...")
        if not response or not hasattr(response, 'text'):
            error_msg = f"Lần thử {state['current_attempt']}: Response không hợp lệ từ AI"
            state["error_messages"].append(error_msg)
            progress_tracker.update_substep(session_id, error_msg)
            return state
            
        full_report_text = response.text
        
        # Kiểm tra nội dung response
        if not full_report_text:
            error_msg = f"Lần thử {state['current_attempt']}: Không nhận được nội dung báo cáo từ AI hoặc không phải string"
            state["error_messages"].append(error_msg)
            progress_tracker.update_substep(session_id, error_msg)
            return state
        
        state["research_content"] = full_report_text
        state["success"] = True
        progress_tracker.update_substep(session_id, "Hoàn thành thu thập dữ liệu!")
        
    except Exception as e:
        error_str = str(e)
        error_msg = f"Lần thử {state['current_attempt']}: Lỗi khi gọi AI: {e}"
        print(error_msg)
        state["error_messages"].append(error_msg)
        progress_tracker.update_substep(session_id, error_msg)
        
        # báo cáo cần thông tin real-time
        state["success"] = False
    
    return state


def validate_report_node(state: ReportState) -> ReportState:
    """Node để validate báo cáo nghiên cứu bằng dữ liệu thời gian thực"""
    session_id = state["session_id"]
    progress_tracker.update_step(session_id, 3, "Xác thực dữ liệu với hệ thống thời gian thực...", "Đang lấy dữ liệu dashboard và kiểm tra độ chính xác")
    
    if not state["research_content"]:
        state["validation_result"] = "UNKNOWN"
        progress_tracker.update_substep(session_id, "Không có nội dung để kiểm tra")
        state["success"] = False
        return state
    
    try:
        # Lấy dữ liệu thời gian thực từ dashboard
        progress_tracker.update_substep(session_id, "Đang lấy dữ liệu thời gian thực từ hệ thống...")
        realtime_data = _get_realtime_dashboard_data()
        
        if not realtime_data:
            # Fallback: Nếu không lấy được dữ liệu thời gian thực, sử dụng validation đơn giản
            print(f"[WARNING] Không thể lấy dữ liệu thời gian thực, chuyển sang validation cơ bản")
            progress_tracker.update_substep(session_id, "⚠️ Không có dữ liệu real-time, sử dụng validation cơ bản...")
            
            # Fallback validation: kiểm tra xem báo cáo có nội dung hợp lệ không
            if len(state["research_content"]) > 1000:  # Báo cáo đủ dài
                # Kiểm tra có chứa các thông tin cơ bản không
                content_lower = state["research_content"].lower()
                has_btc = any(keyword in content_lower for keyword in ['bitcoin', 'btc'])
                has_analysis = any(keyword in content_lower for keyword in ['phân tích', 'analysis', 'thị trường', 'market'])
                has_numbers = re.search(r'\d+\.?\d*\s*%|\$\d+', state["research_content"])
                
                if has_btc and has_analysis and has_numbers:
                    print(f"Lần thử {state['current_attempt']}: Fallback validation PASS - Báo cáo có nội dung hợp lệ")
                    progress_tracker.update_substep(session_id, "✓ Báo cáo có nội dung đầy đủ, chấp nhận!")
                    state["validation_result"] = "PASS"
                    state["success"] = True
                    return state
                else:
                    print(f"Lần thử {state['current_attempt']}: Fallback validation FAIL - Thiếu nội dung cơ bản")
                    progress_tracker.update_substep(session_id, "✗ Báo cáo thiếu nội dung cơ bản...")
                    state["validation_result"] = "FAIL"
                    state["success"] = False
                    return state
            else:
                print(f"Lần thử {state['current_attempt']}: Fallback validation FAIL - Báo cáo quá ngắn")
                progress_tracker.update_substep(session_id, "✗ Báo cáo quá ngắn...")
                state["validation_result"] = "FAIL"
                state["success"] = False
                return state
        
        # Chuẩn bị prompt validation với dữ liệu thời gian thực
        progress_tracker.update_substep(session_id, "Đang chuẩn bị prompt xác thực...")
        validation_prompt = state["data_validation_prompt"]
        validation_prompt = validation_prompt.replace("{{REAL_TIME_DATA}}", json.dumps(realtime_data, ensure_ascii=False, indent=2))
        validation_prompt = validation_prompt.replace("{{REPORT_CONTENT}}", state["research_content"])
        
        # Tạo request cho validation (không cần Google Search)
        progress_tracker.update_substep(session_id, "Đang gọi AI để xác thực dữ liệu...")
        validation_contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=validation_prompt),
                ],
            ),
        ]
        
        # Cấu hình đơn giản cho validation
        simple_config = types.GenerateContentConfig(
            temperature=0.1,  # Thấp hơn để đảm bảo tính nhất quán
            candidate_count=1,
        )
        
        # Retry cho validation
        for validation_attempt in range(3):
            try:
                print(f"Validation attempt {validation_attempt + 1}/3...")
                validation_response = state["client"].models.generate_content(
                    model=state["model"],
                    contents=validation_contents,
                    config=simple_config
                )
                break
            except Exception as validation_error:
                print(f"Validation attempt {validation_attempt + 1} failed: {validation_error}")
                if validation_attempt < 2:
                    wait_time = (validation_attempt + 1) * 15  # 15s, 30s
                    progress_tracker.update_substep(session_id, f"Lỗi xác thực, chờ {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    error_msg = "Không thể xác thực dữ liệu sau 3 lần thử"
                    state["error_messages"].append(error_msg)
                    state["validation_result"] = "UNKNOWN"
                    state["success"] = False
                    progress_tracker.error_progress(session_id, error_msg)
                    return state
        
        # Kiểm tra validation response
        progress_tracker.update_substep(session_id, "Đang xử lý kết quả xác thực...")
        if not validation_response or not hasattr(validation_response, 'text'):
            error_msg = f"Lần thử {state['current_attempt']}: Validation response không hợp lệ từ AI"
            state["error_messages"].append(error_msg)
            state["validation_result"] = "UNKNOWN"
            state["success"] = False
            progress_tracker.update_substep(session_id, error_msg)
            return state
            
        validation_text = validation_response.text
        
        if not validation_text:
            error_msg = f"Lần thử {state['current_attempt']}: Không nhận được kết quả validation từ AI"
            state["error_messages"].append(error_msg)
            state["validation_result"] = "UNKNOWN"
            state["success"] = False
            progress_tracker.update_substep(session_id, error_msg)
            return state
        
        # Phân tích kết quả validation
        validation_result = _check_report_validation(validation_text)
        state["validation_result"] = validation_result
        
        print(f"Lần thử {state['current_attempt']}: Kết quả validation = {validation_result}")
        
        if validation_result == 'PASS':
            print(f"Lần thử {state['current_attempt']}: Báo cáo PASS - Dữ liệu chính xác")
            progress_tracker.update_substep(session_id, "✓ Dữ liệu báo cáo chính xác, đạt yêu cầu!")
            state["success"] = True
        elif validation_result == 'FAIL':
            print(f"Lần thử {state['current_attempt']}: Báo cáo FAIL - Dữ liệu không chính xác")
            progress_tracker.update_substep(session_id, "✗ Dữ liệu không chính xác, cần tạo lại báo cáo...")
            state["success"] = False
        else:
            # UNKNOWN case
            print(f"Lần thử {state['current_attempt']}: Không xác định được kết quả validation")
            progress_tracker.update_substep(session_id, "? Không xác định được kết quả, thử lại...")
            state["success"] = False
        
        # Lưu kết quả validation để debug
        print(f"[DEBUG] Validation response: {validation_text[:500]}...")
        
    except Exception as e:
        error_msg = f"Lần thử {state['current_attempt']}: Lỗi khi xác thực dữ liệu: {e}"
        print(error_msg)
        state["error_messages"].append(error_msg)
        state["validation_result"] = "UNKNOWN"
        state["success"] = False
        progress_tracker.update_substep(session_id, error_msg)
    
    return state


def create_interface_node(state: ReportState) -> ReportState:
    """Node để tạo giao diện từ báo cáo nghiên cứu"""
    session_id = state["session_id"]
    progress_tracker.update_step(session_id, 4, "Tạo giao diện báo cáo...", "Đang chuẩn bị tạo HTML, CSS, JS")
    
    print("Đang tạo giao diện báo cáo...")
    
    # Tạo request đầy đủ
    progress_tracker.update_substep(session_id, "Đang chuẩn bị request cho AI...")
    full_request = f"{state['create_report_prompt']}\n\n---\n\n**NỘI DUNG BÁO CÁO CẦN XỬ LÝ:**\n\n{state['research_content']}"
    
    # Tạo request content cho giao diện (không cần Google Search cho phần này)
    interface_contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=full_request),
            ],
        ),
    ]
    
    # Cấu hình đơn giản hơn cho interface generation (không có tools)
    simple_config = types.GenerateContentConfig(
        temperature=0.7,
        candidate_count=1,
    )
    
    # Retry cho interface generation
    for interface_attempt in range(3):
        try:
            progress_tracker.update_substep(session_id, f"Đang gọi AI để tạo giao diện (lần {interface_attempt + 1}/3)...")
            print(f"Interface generation attempt {interface_attempt + 1}/3...")
            interface_response = state["client"].models.generate_content(
                model=state["model"],
                contents=interface_contents,
                config=simple_config
            )
            break  # Thành công, thoát khỏi retry loop
        except Exception as interface_error:
            print(f"Interface attempt {interface_attempt + 1} failed: {interface_error}")
            if interface_attempt < 2:  # Không phải lần cuối
                wait_time = (interface_attempt + 1) * 20  # 20s, 40s
                progress_tracker.update_substep(session_id, f"Lỗi tạo giao diện, chờ {wait_time}s...")
                print(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                error_msg = "Không thể tạo interface sau 3 lần thử"
                state["error_messages"].append(error_msg)
                state["success"] = False
                progress_tracker.error_progress(session_id, error_msg)
                return state
    
    # Kiểm tra interface response
    progress_tracker.update_substep(session_id, "Đang kiểm tra phản hồi từ AI...")
    if not interface_response or not hasattr(interface_response, 'text'):
        error_msg = "Interface response không hợp lệ từ AI"
        state["error_messages"].append(error_msg)
        state["success"] = False
        progress_tracker.error_progress(session_id, error_msg)
        return state
        
    if not interface_response.text:
        error_msg = "Không nhận được nội dung interface từ AI hoặc không phải string"
        state["error_messages"].append(error_msg)
        state["success"] = False
        progress_tracker.error_progress(session_id, error_msg)
        return state
    
    state["interface_content"] = interface_response.text
    state["success"] = True
    progress_tracker.update_substep(session_id, "Hoàn thành tạo giao diện!")
    
    return state


def extract_code_node(state: ReportState) -> ReportState:
    """Node để trích xuất các khối mã từ phản hồi interface"""
    session_id = state["session_id"]
    progress_tracker.update_step(session_id, 5, "Trích xuất mã nguồn...", "Đang tách HTML, CSS, JavaScript")
    
    print("Đang trích xuất các khối mã...")
    
    # Kiểm tra interface_content trước khi trích xuất
    if not state.get("interface_content"):
        error_msg = "Không có nội dung interface để trích xuất"
        state["error_messages"].append(error_msg)
        state["success"] = False
        progress_tracker.error_progress(session_id, error_msg)
        return state
    
    # Trích xuất các khối mã
    progress_tracker.update_substep(session_id, "Đang phân tích và trích xuất các khối mã...")
    code_blocks = _extract_code_blocks(state["interface_content"])
    
    # Kiểm tra kết quả trích xuất với nhiều điều kiện
    html_content = code_blocks.get("html", "").strip()
    css_content = code_blocks.get("css", "").strip()
    js_content = code_blocks.get("js", "").strip()
    
    # Validation HTML content
    if not html_content:
        # Thử trích xuất trực tiếp từ interface_content nếu có HTML tags
        interface_text = state["interface_content"]
        if '<html' in interface_text.lower() or '<!doctype' in interface_text.lower() or '<div' in interface_text.lower():
            # Có vẻ như có HTML trong response nhưng không trong code blocks
            print("[DEBUG] Detected HTML content outside code blocks, using raw content")
            html_content = interface_text
        else:
            error_msg = "Không thể trích xuất mã HTML từ phản hồi AI - Không tìm thấy HTML content"
            print(f"[DEBUG] Interface content sample: {interface_text[:200]}...")
            state["error_messages"].append(error_msg)
            state["success"] = False
            progress_tracker.error_progress(session_id, error_msg)
            return state
    
    # Kiểm tra HTML content có hợp lệ không
    if len(html_content) < 50:  # HTML quá ngắn có thể không hợp lệ
        print(f"[WARNING] HTML content seems too short ({len(html_content)} chars): {html_content[:100]}")
        # Không fail ngay, vẫn tiếp tục với nội dung này
    
    # Set default values nếu CSS/JS trống
    if not css_content:
        css_content = "/* CSS được tạo tự động */\nbody { font-family: Arial, sans-serif; margin: 20px; }"
    
    if not js_content or js_content.startswith("//"):
        js_content = "// JavaScript được tạo tự động\nconsole.log('Report loaded successfully');"
    
    state["html_content"] = html_content
    state["css_content"] = css_content
    state["js_content"] = js_content
    state["success"] = True
    
    progress_tracker.update_substep(session_id, f"Trích xuất thành công! HTML: {len(html_content)} chars, CSS: {len(css_content)} chars, JS: {len(js_content)} chars")
    print(f"Hoàn thành trích xuất - HTML: {len(html_content)}, CSS: {len(css_content)}, JS: {len(js_content)} characters")
    
    return state


def _save_to_database_with_context(state: ReportState, session_id: str) -> ReportState:
    """Helper function để lưu database với proper context"""
    try:
        # Tạo báo cáo mới và lưu vào database
        progress_tracker.update_substep(session_id, "Đang tạo record báo cáo mới...")
        new_report = Report(
            html_content=state["html_content"],
            css_content=state["css_content"],
            js_content=state["js_content"]
        )
        
        progress_tracker.update_substep(session_id, "Đang lưu vào database...")
        db.session.add(new_report)
        db.session.commit()
        
        state["report_id"] = new_report.id
        state["success"] = True
        
        progress_tracker.update_step(session_id, 7, "Hoàn thành!", f"Báo cáo #{new_report.id} đã được tạo thành công")
        progress_tracker.complete_progress(session_id, True, new_report.id)
        
        print(f"[{datetime.now()}] Tạo báo cáo tự động thành công! ID: {new_report.id}")
        
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
    progress_tracker.update_step(session_id, 6, "Lưu báo cáo vào database...", "Đang lưu HTML, CSS, JS vào cơ sở dữ liệu")
    
    print("Đang lưu báo cáo vào database...")
    
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
    workflow.add_edge("extract_code", "save_database")
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
