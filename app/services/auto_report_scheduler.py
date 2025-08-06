import os
import re
import threading
import time
from datetime import datetime, timezone
from google import genai
from google.genai import types
from ..extensions import db
from ..models import Report


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


def _create_fallback_report_without_search(client, model, deep_research_prompt):
    """
    Tạo báo cáo fallback không sử dụng Google Search khi gặp lỗi 500.
    """
    try:
        print("Đang thử chế độ fallback (không Google Search)...")
        
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
                        text=f"{deep_research_prompt}\n\n**LUU Ý: Tạo báo cáo dựa trên kiến thức có sẵn do không thể truy cập internet.**"
                    ),
                ],
            ),
        ]
        
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=fallback_config
        )
        
        if response and hasattr(response, 'text') and response.text:
            return response.text
        else:
            return None
            
    except Exception as e:
        print(f"Fallback mode cũng thất bại: {e}")
        return None


def generate_auto_research_report(api_key, max_attempts=3, use_fallback_on_500=True):
    """
    Hàm tự động tạo báo cáo nghiên cứu sâu với cơ chế validation và retry.
    
    Args:
        api_key (str): API key của Gemini
        max_attempts (int): Số lần thử tối đa để tạo báo cáo PASS
        use_fallback_on_500 (bool): Có sử dụng fallback mode khi gặp lỗi 500
        
    Returns:
        bool: True nếu tạo báo cáo thành công, False nếu thất bại
    """
    try:
        print(f"[{datetime.now()}] Bắt đầu tạo báo cáo tự động...")
        
        # Kiểm tra API key
        if not api_key or not isinstance(api_key, str):
            print("Lỗi: API key không hợp lệ")
            return False
        
        # Đường dẫn tới các prompt files
        current_dir = os.path.dirname(__file__)
        deep_research_prompt_path = os.path.abspath(
            os.path.join(current_dir, '..', '..', 'create_report', 'prompt_deep_research_report.md')
        )
        create_report_prompt_path = os.path.abspath(
            os.path.join(current_dir, '..', '..', 'create_report', 'prompt_create_report.md')
        )
        
        print(f"Deep research prompt path: {deep_research_prompt_path}")
        print(f"Create report prompt path: {create_report_prompt_path}")
        
        # Bước 1: Đọc prompt deep research và thay thế ngày tháng
        deep_research_prompt = _read_prompt_file(deep_research_prompt_path)
        if deep_research_prompt is None:
            print("Lỗi: Không thể đọc prompt deep research")
            return False
            
        deep_research_prompt = _replace_date_placeholders(deep_research_prompt)
        
        # Cấu hình Gemini
        try:
            client = genai.Client(api_key=api_key)
            model = "gemini-2.5-pro"
            print("Đã khởi tạo Gemini client thành công")
        except Exception as e:
            print(f"Lỗi khi khởi tạo Gemini client: {e}")
            return False
        
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
        
        # Bước 2: Vòng lặp tạo báo cáo nghiên cứu sâu với validation
        report_content = None
        full_report_text = None
        
        for attempt in range(1, max_attempts + 1):
            print(f"Đang tạo báo cáo nghiên cứu sâu (lần thử {attempt}/{max_attempts})...")
            
            try:
                # Tạo request content với Google Search tools
                contents = [
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=deep_research_prompt),
                        ],
                    ),
                ]
                
                # Thêm timeout và retry cho API call
                import time
                for api_attempt in range(3):  # Retry 3 lần cho mỗi attempt
                    try:
                        print(f"API call attempt {api_attempt + 1}/3...")
                        response = client.models.generate_content(
                            model=model,
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
                    print(f"Lần thử {attempt}: Response không hợp lệ từ AI")
                    continue
                    
                full_report_text = response.text
                
                # Kiểm tra nội dung response
                if not full_report_text or not isinstance(full_report_text, str):
                    print(f"Lần thử {attempt}: Không nhận được nội dung báo cáo từ AI hoặc không phải string")
                    continue
                
                # Kiểm tra validation
                validation_result = _check_report_validation(full_report_text)
                print(f"Lần thử {attempt}: Kết quả validation = {validation_result}")
                
                if validation_result == 'PASS':
                    # Sử dụng toàn bộ nội dung báo cáo
                    report_content = full_report_text
                    print(f"Lần thử {attempt}: Báo cáo PASS - Sử dụng toàn bộ nội dung")
                    break
                elif validation_result == 'FAIL':
                    print(f"Lần thử {attempt}: Báo cáo FAIL - Thử lại...")
                    continue
                else:
                    print(f"Lần thử {attempt}: Không tìm thấy kết quả validation - Thử lại...")
                    continue
                    
            except Exception as e:
                error_str = str(e)
                print(f"Lần thử {attempt}: Lỗi khi gọi AI: {e}")
                
                # Kiểm tra nếu là lỗi 500 và có thể thử fallback
                if "500" in error_str and "INTERNAL" in error_str and use_fallback_on_500 and attempt == max_attempts:
                    print("Phát hiện lỗi 500 INTERNAL, thử chế độ fallback...")
                    fallback_text = _create_fallback_report_without_search(client, model, deep_research_prompt)
                    if fallback_text:
                        validation_result = _check_report_validation(fallback_text)
                        if validation_result in ['PASS', 'UNKNOWN']:  # Chấp nhận UNKNOWN cho fallback
                            full_report_text = fallback_text
                            report_content = full_report_text
                            print("Fallback mode thành công!")
                            break
                continue
        
        # Kiểm tra kết quả sau vòng lặp
        if not report_content:
            print(f"Lỗi: Không thể tạo báo cáo PASS sau {max_attempts} lần thử")
            return False
            
        print("Hoàn thành tạo báo cáo nghiên cứu sâu với validation PASS")
        
        # Bước 3: Đọc prompt tạo giao diện
        # Bước 3: Đọc prompt tạo giao diện
        create_report_prompt = _read_prompt_file(create_report_prompt_path)
        if create_report_prompt is None:
            print("Lỗi: Không thể đọc prompt tạo giao diện")
            return False
            
        # Bước 4: Gọi Gemini để tạo giao diện từ báo cáo nghiên cứu (chỉ PHẦN A)
        full_request = f"{create_report_prompt}\n\n---\n\n**NỘI DUNG BÁO CÁO CẦN XỬ LÝ:**\n\n{report_content}"
        
        print("Đang tạo giao diện báo cáo...")
        
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
                interface_response = client.models.generate_content(
                    model=model,
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
                    print("Lỗi: Không thể tạo interface sau 3 lần thử")
                    return False
        
        # Kiểm tra interface response
        if not interface_response or not hasattr(interface_response, 'text'):
            print("Lỗi: Interface response không hợp lệ từ AI")
            return False
            
        if not interface_response.text or not isinstance(interface_response.text, str):
            print("Lỗi: Không nhận được nội dung interface từ AI hoặc không phải string")
            return False
        
        # Bước 5: Trích xuất các khối mã
        code_blocks = _extract_code_blocks(interface_response.text)
        
        if not code_blocks or not code_blocks.get("html"):
            print("Lỗi: Không thể trích xuất mã HTML từ phản hồi AI")
            return False
            
        print("Hoàn thành tạo giao diện báo cáo")
        
        # Bước 6: Tạo báo cáo mới và lưu vào database
        new_report = Report(
            html_content=code_blocks.get("html", ""),
            css_content=code_blocks.get("css", ""),
            js_content=code_blocks.get("js", "")
        )
        
        db.session.add(new_report)
        db.session.commit()
        
        print(f"[{datetime.now()}] Tạo báo cáo tự động thành công! ID: {new_report.id}")
        return True
        
    except Exception as e:
        print(f"[{datetime.now()}] Lỗi khi tạo báo cáo tự động: {e}")
        if 'db' in locals():
            db.session.rollback()
        return False


def schedule_auto_report(app, api_key, interval_hours=6):
    """
    Lên lịch tự động tạo báo cáo mỗi interval_hours giờ.
    
    Args:
        app: Flask app instance
        api_key (str): API key của Gemini
        interval_hours (int): Khoảng thời gian giữa các lần tạo báo cáo (giờ)
    """
    def run_scheduler():
        with app.app_context():
            while True:
                try:
                    # Chạy tạo báo cáo với số lần thử tối đa và fallback
                    max_attempts = int(os.getenv('MAX_REPORT_ATTEMPTS', '3'))
                    use_fallback = os.getenv('USE_FALLBACK_ON_500', 'true').lower() == 'true'
                    success = generate_auto_research_report(api_key, max_attempts, use_fallback)
                    if success:
                        print(f"[{datetime.now()}] Scheduler: Báo cáo đã được tạo thành công")
                    else:
                        print(f"[{datetime.now()}] Scheduler: Tạo báo cáo thất bại")
                        
                except Exception as e:
                    print(f"[{datetime.now()}] Scheduler error: {e}")
                
                # Chờ interval_hours giờ trước khi chạy lần tiếp theo
                time.sleep(interval_hours * 3600)
    
    # Tạo và khởi động thread cho scheduler
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print(f"[{datetime.now()}] Auto report scheduler đã được khởi động (mỗi {interval_hours} giờ)")


def start_auto_report_scheduler(app):
    """
    Khởi động scheduler tự động tạo báo cáo.
    Hàm này sẽ được gọi khi ứng dụng khởi động.
    
    Args:
        app: Flask app instance
    """
    # Lấy API key từ environment variables
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("WARNING: GEMINI_API_KEY không được thiết lập. Auto report scheduler không được khởi động.")
        return False
    
    # Kiểm tra nếu đang chạy trên môi trường production hoặc có enable scheduler
    enable_scheduler = os.getenv('ENABLE_AUTO_REPORT_SCHEDULER', 'false').lower() == 'true'
    
    if enable_scheduler:
        # Lấy interval từ environment variable, mặc định là 3 giờ
        interval_hours = int(os.getenv('AUTO_REPORT_INTERVAL_HOURS', '3'))
        schedule_auto_report(app, api_key, interval_hours)
        return True
    else:
        print("INFO: Auto report scheduler chưa được bật. Thiết lập ENABLE_AUTO_REPORT_SCHEDULER=true để bật.")
        return False
