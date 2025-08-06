import os
import re
import time
from datetime import datetime, timezone
from typing import TypedDict, Optional, List, Literal
from google import genai
from google.genai import types
from langgraph.graph import StateGraph, END
from ..extensions import db
from ..models import Report


class ReportState(TypedDict):
    """State schema cho report generation workflow"""
    # Input parameters
    api_key: str
    max_attempts: int
    use_fallback_on_500: bool
    
    # File paths
    deep_research_prompt_path: Optional[str]
    create_report_prompt_path: Optional[str]
    
    # Processing state
    deep_research_prompt: Optional[str]
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
    fallback_used: bool
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
    print(f"[{datetime.now()}] Bắt đầu tạo báo cáo tự động...")
    
    # Kiểm tra API key
    if not state["api_key"] or not isinstance(state["api_key"], str):
        state["error_messages"].append("API key không hợp lệ")
        state["success"] = False
        return state
    
    # Thiết lập đường dẫn tới các prompt files
    current_dir = os.path.dirname(__file__)
    state["deep_research_prompt_path"] = os.path.abspath(
        os.path.join(current_dir, '..', '..', 'create_report', 'prompt_deep_research_report.md')
    )
    state["create_report_prompt_path"] = os.path.abspath(
        os.path.join(current_dir, '..', '..', 'create_report', 'prompt_create_report.md')
    )
    
    print(f"Deep research prompt path: {state['deep_research_prompt_path']}")
    print(f"Create report prompt path: {state['create_report_prompt_path']}")
    
    # Đọc prompt deep research và thay thế ngày tháng
    deep_research_prompt = _read_prompt_file(state["deep_research_prompt_path"])
    if deep_research_prompt is None:
        state["error_messages"].append("Không thể đọc prompt deep research")
        state["success"] = False
        return state
        
    state["deep_research_prompt"] = _replace_date_placeholders(deep_research_prompt)
    
    # Khởi tạo Gemini client
    try:
        client = genai.Client(api_key=state["api_key"])
        state["client"] = client
        state["model"] = "gemini-2.5-pro"
        print("Đã khởi tạo Gemini client thành công")
    except Exception as e:
        state["error_messages"].append(f"Lỗi khi khởi tạo Gemini client: {e}")
        state["success"] = False
        return state
    
    # Đọc prompt tạo giao diện
    create_report_prompt = _read_prompt_file(state["create_report_prompt_path"])
    if create_report_prompt is None:
        state["error_messages"].append("Không thể đọc prompt tạo giao diện")
        state["success"] = False
        return state
    
    state["create_report_prompt"] = create_report_prompt
    state["current_attempt"] = 0
    state["success"] = True
    
    return state


def research_deep_node(state: ReportState) -> ReportState:
    """Node để thực hiện nghiên cứu sâu với Google Search"""
    state["current_attempt"] += 1
    print(f"Đang tạo báo cáo nghiên cứu sâu (lần thử {state['current_attempt']}/{state['max_attempts']})...")
    
    try:
        # Cấu hình tools và thinking mode với giới hạn budget
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
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=state["deep_research_prompt"]),
                ],
            ),
        ]
        
        # Thêm timeout và retry cho API call
        for api_attempt in range(3):  # Retry 3 lần cho mỗi attempt
            try:
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
                    print(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    raise api_error  # Ném lỗi sau khi hết retry
        
        # Kiểm tra response
        if not response or not hasattr(response, 'text'):
            state["error_messages"].append(f"Lần thử {state['current_attempt']}: Response không hợp lệ từ AI")
            return state
            
        full_report_text = response.text
        
        # Kiểm tra nội dung response
        if not full_report_text or not isinstance(full_report_text, str):
            state["error_messages"].append(f"Lần thử {state['current_attempt']}: Không nhận được nội dung báo cáo từ AI hoặc không phải string")
            return state
        
        state["research_content"] = full_report_text
        state["success"] = True
        
    except Exception as e:
        error_str = str(e)
        error_msg = f"Lần thử {state['current_attempt']}: Lỗi khi gọi AI: {e}"
        print(error_msg)
        state["error_messages"].append(error_msg)
        
        # Kiểm tra nếu là lỗi 500 và có thể thử fallback
        if ("500" in error_str and "INTERNAL" in error_str and 
            state["use_fallback_on_500"] and 
            state["current_attempt"] == state["max_attempts"]):
            state["should_fallback"] = True
        
        state["success"] = False
    
    return state


def fallback_research_node(state: ReportState) -> ReportState:
    """Node fallback cho nghiên cứu không sử dụng Google Search"""
    print("Đang thử chế độ fallback (không Google Search)...")
    
    try:
        # Cấu hình đơn giản không có tools
        fallback_config = types.GenerateContentConfig(
            temperature=0.8,
            candidate_count=1,
        )
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(
                        text=f"{state['deep_research_prompt']}\n\n**LUU Ý: Tạo báo cáo dựa trên kiến thức có sẵn do không thể truy cập internet.**"
                    ),
                ],
            ),
        ]
        
        response = state["client"].models.generate_content(
            model=state["model"],
            contents=contents,
            config=fallback_config
        )
        
        if response and hasattr(response, 'text') and response.text:
            state["research_content"] = response.text
            state["fallback_used"] = True
            state["success"] = True
            print("Fallback mode thành công!")
        else:
            state["error_messages"].append("Fallback mode cũng thất bại: Không nhận được response")
            state["success"] = False
            
    except Exception as e:
        state["error_messages"].append(f"Fallback mode cũng thất bại: {e}")
        state["success"] = False
    
    return state


def validate_report_node(state: ReportState) -> ReportState:
    """Node để validate báo cáo nghiên cứu"""
    if not state["research_content"]:
        state["validation_result"] = "UNKNOWN"
        return state
    
    # Kiểm tra validation
    validation_result = _check_report_validation(state["research_content"])
    state["validation_result"] = validation_result
    
    print(f"Lần thử {state['current_attempt']}: Kết quả validation = {validation_result}")
    
    if validation_result == 'PASS':
        print(f"Lần thử {state['current_attempt']}: Báo cáo PASS - Sử dụng toàn bộ nội dung")
        state["success"] = True
    elif validation_result == 'FAIL':
        print(f"Lần thử {state['current_attempt']}: Báo cáo FAIL - Thử lại...")
        state["success"] = False
    else:
        # UNKNOWN case
        if state["fallback_used"]:
            # Chấp nhận UNKNOWN cho fallback
            print(f"Lần thử {state['current_attempt']}: Validation UNKNOWN nhưng chấp nhận do dùng fallback")
            state["success"] = True
        else:
            print(f"Lần thử {state['current_attempt']}: Không tìm thấy kết quả validation - Thử lại...")
            state["success"] = False
    
    return state


def create_interface_node(state: ReportState) -> ReportState:
    """Node để tạo giao diện từ báo cáo nghiên cứu"""
    print("Đang tạo giao diện báo cáo...")
    
    # Tạo request đầy đủ
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
                print(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                state["error_messages"].append("Không thể tạo interface sau 3 lần thử")
                state["success"] = False
                return state
    
    # Kiểm tra interface response
    if not interface_response or not hasattr(interface_response, 'text'):
        state["error_messages"].append("Interface response không hợp lệ từ AI")
        state["success"] = False
        return state
        
    if not interface_response.text or not isinstance(interface_response.text, str):
        state["error_messages"].append("Không nhận được nội dung interface từ AI hoặc không phải string")
        state["success"] = False
        return state
    
    state["interface_content"] = interface_response.text
    state["success"] = True
    
    return state


def extract_code_node(state: ReportState) -> ReportState:
    """Node để trích xuất các khối mã từ phản hồi interface"""
    print("Đang trích xuất các khối mã...")
    
    # Trích xuất các khối mã
    code_blocks = _extract_code_blocks(state["interface_content"])
    
    if not code_blocks or not code_blocks.get("html"):
        state["error_messages"].append("Không thể trích xuất mã HTML từ phản hồi AI")
        state["success"] = False
        return state
    
    state["html_content"] = code_blocks.get("html", "")
    state["css_content"] = code_blocks.get("css", "")
    state["js_content"] = code_blocks.get("js", "")
    state["success"] = True
    
    print("Hoàn thành tạo giao diện báo cáo")
    
    return state


def save_database_node(state: ReportState) -> ReportState:
    """Node để lưu báo cáo vào database"""
    print("Đang lưu báo cáo vào database...")
    
    try:
        # Tạo báo cáo mới và lưu vào database
        new_report = Report(
            html_content=state["html_content"],
            css_content=state["css_content"],
            js_content=state["js_content"]
        )
        
        db.session.add(new_report)
        db.session.commit()
        
        state["report_id"] = new_report.id
        state["success"] = True
        
        print(f"[{datetime.now()}] Tạo báo cáo tự động thành công! ID: {new_report.id}")
        
    except Exception as e:
        state["error_messages"].append(f"Lỗi khi lưu database: {e}")
        state["success"] = False
        try:
            db.session.rollback()
        except:
            pass
    
    return state


# =============================================================================
# CONDITIONAL ROUTING
# =============================================================================

def should_retry_or_continue(state: ReportState) -> Literal["retry", "continue", "fallback", "end"]:
    """Quyết định hướng đi tiếp theo sau validation"""
    
    # Nếu validation PASS, tiếp tục
    if state["validation_result"] == "PASS":
        return "continue"
    
    # Nếu đã hết số lần thử
    if state["current_attempt"] >= state["max_attempts"]:
        # Kiểm tra xem có nên thử fallback không
        if (hasattr(state, "should_fallback") and state["should_fallback"] and 
            state["use_fallback_on_500"] and not state["fallback_used"]):
            return "fallback"
        
        # Nếu đã dùng fallback và có kết quả UNKNOWN, chấp nhận
        if state["fallback_used"] and state["validation_result"] == "UNKNOWN":
            return "continue"
        
        # Hết lựa chọn, kết thúc
        return "end"
    
    # Còn lần thử, retry
    return "retry"


def should_continue_after_fallback(state: ReportState) -> Literal["continue", "end"]:
    """Quyết định có tiếp tục sau fallback không"""
    if state["success"]:
        return "continue"
    return "end"


# =============================================================================
# WORKFLOW CONSTRUCTION
# =============================================================================

def create_report_workflow():
    """Tạo và cấu hình LangGraph workflow"""
    
    workflow = StateGraph(ReportState)
    
    # Thêm các nodes
    workflow.add_node("prepare_data", prepare_data_node)
    workflow.add_node("research_deep", research_deep_node)
    workflow.add_node("fallback_research", fallback_research_node)
    workflow.add_node("validate_report", validate_report_node)
    workflow.add_node("create_interface", create_interface_node)
    workflow.add_node("extract_code", extract_code_node)
    workflow.add_node("save_database", save_database_node)
    
    # Thiết lập entry point
    workflow.set_entry_point("prepare_data")
    
    # Thiết lập các edges
    workflow.add_edge("prepare_data", "research_deep")
    workflow.add_edge("research_deep", "validate_report")
    workflow.add_edge("fallback_research", "validate_report")
    
    # Conditional routing sau validation
    workflow.add_conditional_edges(
        "validate_report",
        should_retry_or_continue,
        {
            "retry": "research_deep",
            "continue": "create_interface",
            "fallback": "fallback_research",
            "end": END
        }
    )
    
    # Conditional routing sau fallback
    workflow.add_conditional_edges(
        "fallback_research", 
        should_continue_after_fallback,
        {
            "continue": "validate_report",
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

def generate_auto_research_report_langgraph(api_key: str, max_attempts: int = 3, use_fallback_on_500: bool = True) -> bool:
    """
    Hàm chính để tạo báo cáo sử dụng LangGraph workflow.
    
    Args:
        api_key (str): API key của Gemini
        max_attempts (int): Số lần thử tối đa để tạo báo cáo PASS
        use_fallback_on_500 (bool): Có sử dụng fallback mode khi gặp lỗi 500
        
    Returns:
        bool: True nếu tạo báo cáo thành công, False nếu thất bại
    """
    
    # Khởi tạo state
    initial_state = ReportState(
        api_key=api_key,
        max_attempts=max_attempts,
        use_fallback_on_500=use_fallback_on_500,
        deep_research_prompt_path=None,
        create_report_prompt_path=None,
        deep_research_prompt=None,
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
        fallback_used=False,
        success=False,
        client=None,
        model="gemini-2.5-pro"
    )
    
    try:
        # Tạo và chạy workflow
        workflow = create_report_workflow()
        final_state = workflow.invoke(initial_state)
        
        # Kiểm tra kết quả
        if final_state["success"] and final_state.get("report_id"):
            return True
        else:
            print(f"[{datetime.now()}] Lỗi khi tạo báo cáo tự động:")
            for error in final_state["error_messages"]:
                print(f"  - {error}")
            return False
            
    except Exception as e:
        print(f"[{datetime.now()}] Lỗi workflow: {e}")
        return False
