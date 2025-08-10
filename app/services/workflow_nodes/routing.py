"""
Conditional routing functions cho workflow
"""
from typing import Literal
from .base import ReportState


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
