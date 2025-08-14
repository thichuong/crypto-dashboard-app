# app/services/workflow_nodes/translate_content.py

import time
from typing import Dict, Any
from google.genai import types
from .base import ReportState, read_prompt_file
from ...services.progress_tracker import progress_tracker


def translate_content_node(state: ReportState) -> Dict[str, Any]:
    """
    Node để dịch nội dung HTML từ tiếng Việt sang tiếng Anh bằng AI.
    Note: JavaScript translation removed - JS now supports multi-language natively.
    
    Args:
        state: Trạng thái hiện tại của workflow
        
    Returns:
        Dict chứa nội dung đã dịch
    """
    session_id = state["session_id"]
    progress_tracker.update_step(session_id, 8, "Dịch nội dung", "Dịch HTML từ tiếng Việt sang tiếng Anh")
    
    try:
        print("\n=== BƯỚC DỊCH NỘI DUNG ===")
        print("Bắt đầu dịch HTML content từ tiếng Việt sang tiếng Anh...")
        
        translated_html = None
        translated_js = None
        
        # Dịch HTML content
        if state.get("html_content"):
            print("Đang dịch HTML content...")
            progress_tracker.update_step(session_id, details="Đang dịch HTML content...")
            translated_html = _translate_with_ai(
                state["client"], 
                state["model"], 
                state["html_content"], 
                "html",
                session_id
            )
            if translated_html:
                print("✓ HTML content đã được dịch thành công")
                progress_tracker.update_step(session_id, details=f"✓ HTML đã dịch - {len(translated_html)} chars")
            else:
                print("✗ Dịch HTML content thất bại")
        
        # JavaScript translation removed - JS now supports multi-language natively
        translated_js = None
        
        # Cập nhật state với nội dung đã dịch và trả về state để tiếp tục workflow
        if translated_html:
            state["html_content_en"] = translated_html
        else:
            # đảm bảo key tồn tại
            state.setdefault("html_content_en", None)

        if translated_js:
            state["js_content_en"] = translated_js
        else:
            state.setdefault("js_content_en", None)

        translated_count = 0
        if translated_html:
            translated_count += 1
        if translated_js:
            translated_count += 1

        print(f"Translation node hoàn thành. Đã dịch {translated_count} nội dung.")
        progress_tracker.update_step(session_id, details=f"Hoàn thành dịch {translated_count} nội dung")
        return state
        
    except Exception as e:
        error_msg = f"Translation node thất bại: {e}"
        print(f"ERROR: {error_msg}")
        progress_tracker.update_step(session_id, details=f"⚠️ Lỗi dịch: {e}")
    # Tiếp tục workflow ngay cả khi dịch thất bại - đảm bảo các khóa tồn tại trên state
    state.setdefault("html_content_en", None)
    state.setdefault("js_content_en", None)
    return state


def _translate_with_ai(client, model, content: str, content_type: str, session_id: str) -> str:
    """
    Dịch nội dung bằng AI.
    Note: JavaScript translation has been removed - JS now supports multi-language natively.
    
    Args:
        client: Google GenAI client
        model: Model name
        content: Nội dung cần dịch
        content_type: Loại nội dung ("html" only - javascript no longer supported)
        session_id: Session ID cho progress tracking
        
    Returns:
        Nội dung đã dịch hoặc None nếu thất bại
    """
    if not content or len(content.strip()) == 0:
        return None
    
    # Tạo prompt dịch cho HTML content: đọc từ file prompt để dễ bảo trì
    if content_type == "html":
        prompt_template = read_prompt_file('prompt_translate_html.md')
        prompt = prompt_template.replace('{content}', content)
    else:  # JavaScript translation no longer supported
        print(f"WARNING: JavaScript translation is no longer supported. Content type: {content_type}")
        return None
    
    # Tạo request cho AI
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
            ],
        ),
    ]
    
    config = types.GenerateContentConfig(
        temperature=0.1,  # Low temperature để dịch chính xác
        candidate_count=1,
    )
    
    # Retry logic giống như các node khác
    for attempt in range(3):
        try:
            progress_tracker.update_step(session_id, details=f"Gọi AI dịch {content_type} (lần {attempt + 1}/3)...")
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )
            
            if response and hasattr(response, 'text') and response.text:
                # Làm sạch response text
                translated_content = response.text.strip()
                
                # Loại bỏ markdown code blocks nếu có
                if translated_content.startswith('```'):
                    lines = translated_content.split('\n')
                    if len(lines) > 2:
                        # Bỏ dòng đầu và cuối (markdown markers)
                        translated_content = '\n'.join(lines[1:-1])
                
                return translated_content
            else:
                print(f"WARNING: AI không trả về nội dung cho {content_type}")
                return None
                
        except Exception as e:
            if attempt < 2:
                wait_time = (attempt + 1) * 10
                progress_tracker.update_step(session_id, details=f"Lỗi dịch {content_type}, chờ {wait_time}s...")
                print(f"WARNING: Lỗi dịch {content_type} (lần {attempt + 1}), thử lại sau {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                print(f"ERROR: Không thể dịch {content_type} sau 3 lần thử: {e}")
                return None
    
    return None
