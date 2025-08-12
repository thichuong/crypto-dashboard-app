"""
Node thực hiện nghiên cứu sâu + validation
"""
import time
import json
from google.genai import types
from .base import ReportState, check_report_validation
from ...services.progress_tracker import progress_tracker


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
            progress_tracker.update_step(session_id, details="✓ Đã inject real-time data vào combined prompt")
        else:
            # Thay thế bằng fallback message
            combined_prompt = combined_prompt.replace(
                "{{REAL_TIME_DATA}}", 
                "{\n  \"notice\": \"Real-time data không khả dụng, sử dụng Google Search để lấy dữ liệu mới nhất\"\n}"
            )
            progress_tracker.update_step(session_id, details="⚠️ Không có real-time data, sử dụng Google Search")
        
        # Cấu hình tools với thinking budget cao hơn cho combined task
        tools = [
            types.Tool(googleSearch=types.GoogleSearch()),
        ]
        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                thinking_budget=24576,  # Tăng thinking budget cho combined task
            ),
            tools=tools,
            temperature=0.5,
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
                progress_tracker.update_step(session_id, details=f"Gọi Combined AI API (lần {api_attempt + 1}/3)...")
                response = state["client"].models.generate_content(
                    model=state["model"],
                    contents=contents,
                    config=generate_content_config
                )
                break
            except Exception as api_error:
                if api_attempt < 2:
                    wait_time = (api_attempt + 1) * 45  # Longer wait for complex combined calls
                    # Log error và chờ retry
                    progress_tracker.update_step(session_id, details=f"Lỗi Combined API, chờ {wait_time}s... ({api_error})")
                    time.sleep(wait_time)
                else:
                    raise api_error
        
        # Kiểm tra response
        if not response or not hasattr(response, 'text'):
            error_msg = f"Lần thử {state['current_attempt']}: Combined response không hợp lệ từ AI"
            state["error_messages"].append(error_msg)
            progress_tracker.update_step(session_id, details=error_msg)
            state["success"] = False
            return state
            
        full_response_text = response.text
        
        if not full_response_text:
            error_msg = f"Lần thử {state['current_attempt']}: Không nhận được nội dung từ Combined AI"
            state["error_messages"].append(error_msg)
            progress_tracker.update_step(session_id, details=error_msg)
            state["success"] = False
            return state
        
        # Parse combined response để extract research content và validation result
        progress_tracker.update_step(session_id, details="Parsing combined response...")
        
        # Tìm validation result trong response
        validation_result = check_report_validation(full_response_text)
        state["validation_result"] = validation_result
        
        state["research_content"] = full_response_text
        
        # Set success based on validation result
        if validation_result == "PASS":
            state["success"] = True
            progress_tracker.update_step(session_id, details=f"✓ Combined Research + Validation PASS")
        elif validation_result == "FAIL":
            state["success"] = False
            progress_tracker.update_step(session_id, details=f"✗ Combined Research + Validation FAIL")
        else:
            # UNKNOWN validation result - treat as success but log warning
            state["success"] = True
            state["validation_result"] = "UNKNOWN"
            progress_tracker.update_step(session_id, details=f"? Combined Response với validation UNKNOWN")
        
        # Log response length for debugging
        progress_tracker.update_step(session_id, details=
            f"✓ Combined response: {len(full_response_text)} chars, "
            f"validation: {validation_result}")
        
    except Exception as e:
        error_msg = f"Lần thử {state['current_attempt']}: Lỗi khi gọi Combined AI: {e}"
        state["error_messages"].append(error_msg)
        progress_tracker.update_step(session_id, details=error_msg)
        state["success"] = False
    
    return state
