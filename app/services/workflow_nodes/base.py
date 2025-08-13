"""
Base types và utilities cho workflow
"""
import os
import re
import json
from datetime import datetime, timezone
from typing import TypedDict, Optional, List
from google import genai
from google.genai import types


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
    
    # Component-specific attempt counters (for workflow v2)
    html_attempt: Optional[int]
    js_attempt: Optional[int]
    css_attempt: Optional[int]
    interface_attempt: Optional[int]  # For backward compatibility
    
    # Timestamps
    created_at: Optional[str]
    
    # Gemini client
    client: Optional[object]
    model: str


def read_prompt_file(file_path):
    """Đọc nội dung từ tệp prompt."""
    try:
        # Nếu chỉ là tên file, tìm trong thư mục create_report
        if not os.path.isabs(file_path) and not os.path.dirname(file_path):
            current_dir = os.path.dirname(__file__)
            project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
            file_path = os.path.join(project_root, 'create_report', file_path)
        
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
            colors = os.path.abspath(os.path.join(current_dir, '..', '..','static', 'css/colors.css'))
            
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


def replace_date_placeholders(prompt_text):
    """Thay thế các placeholder về ngày tháng năm trong prompt."""
    now = datetime.now(timezone.utc)
    
    prompt_text = prompt_text.replace("<<@day>>", str(now.day))
    prompt_text = prompt_text.replace("<<@month>>", str(now.month))
    prompt_text = prompt_text.replace("<<@year>>", str(now.year))
    
    return prompt_text


def extract_code_blocks(response_text):
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


def check_report_validation(report_text):
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


def get_realtime_dashboard_data():
    """Lấy dữ liệu thời gian thực từ các services cơ bản"""
    try:
        # Import trực tiếp các service cần thiết (không có RSI)
        from ... import services
        import concurrent.futures
        
        print("Calling essential real-time data services...")
        
        # Định nghĩa các service calls cơ bản
        def call_global_data():
            return services.coingecko.get_global_market_data()
        
        def call_btc_data():
            return services.coingecko.get_btc_price()
        
        def call_fng_data():
            return services.alternative_me.get_fng_index()
        
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
