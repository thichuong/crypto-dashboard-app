"""
Node validation báo cáo
"""
import re
from .base import ReportState, check_report_validation
from ...services.progress_tracker import progress_tracker


def validate_report_node(state: ReportState) -> ReportState:
    """Node để parse và verify kết quả validation từ combined research response"""
    session_id = state["session_id"]
    progress_tracker.update_step(session_id, 3, "Parse validation result", "Kiểm tra kết quả validation từ combined response")
    
    if not state["research_content"]:
        state["validation_result"] = "UNKNOWN"
        progress_tracker.update_step(session_id, details="Không có research content để parse validation")
        state["success"] = False
        return state
    
    try:
        # Parse validation result từ research_content
        research_content = state["research_content"]
        
        # Kiểm tra xem đã có validation result từ research_deep_node chưa
        current_validation_result = state.get("validation_result", "UNKNOWN")
        
        if current_validation_result == "PASS":
            progress_tracker.update_step(session_id, details="✓ Combined research đã validation PASS")
            state["success"] = True
            return state
        
        elif current_validation_result == "FAIL":
            progress_tracker.update_step(session_id, details="✗ Combined research validation FAIL - cần retry")
            state["success"] = False
            return state
        
        else:
            # UNKNOWN hoặc chưa có validation result, thực hiện parsing bổ sung
            progress_tracker.update_step(session_id, details="? Parsing validation result từ response...")
            
            # Re-check validation result trong toàn bộ response (including research_content)
            full_response = state.get("research_content", "")
            
            # Tìm validation patterns trong response
            validation_result = check_report_validation(full_response)
            state["validation_result"] = validation_result
            
            if validation_result == "PASS":
                progress_tracker.update_step(session_id, details="✓ Parsed validation result: PASS")
                state["success"] = True
                return state
            
            elif validation_result == "FAIL":
                progress_tracker.update_step(session_id, details="✗ Parsed validation result: FAIL")
                state["success"] = False
                return state
            
            else:
                # Vẫn UNKNOWN, thực hiện fallback validation logic
                progress_tracker.update_step(session_id, details="? Validation result vẫn UNKNOWN, sử dụng fallback logic...")
                
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
                        progress_tracker.update_step(session_id, details=f"✓ Fallback validation PASS (quality score: {quality_score}/5)")
                        state["validation_result"] = "PASS"
                        state["success"] = True
                        return state
                    else:
                        progress_tracker.update_step(session_id, details=f"✗ Fallback validation FAIL (quality score: {quality_score}/5)")
                        state["validation_result"] = "FAIL"
                        state["success"] = False
                        return state
                else:
                    progress_tracker.update_step(session_id, details="✗ Combined response quá ngắn")
                    state["validation_result"] = "FAIL"
                    state["success"] = False
                    return state
        
    except Exception as e:
        error_msg = f"Lần thử {state['current_attempt']}: Lỗi khi parse validation result: {e}"
        state["error_messages"].append(error_msg)
        state["validation_result"] = "UNKNOWN"
        state["success"] = False
        progress_tracker.update_step(session_id, details=error_msg)
    
    return state
