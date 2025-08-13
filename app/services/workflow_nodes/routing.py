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


def should_retry_html_or_continue(state: ReportState) -> Literal["retry_html", "continue", "end"]:
    """Quyết định hướng đi tiếp theo sau create_html"""
    
    # Nếu tạo HTML thành công, tiếp tục
    if state["success"] and state.get("html_content"):
        return "continue"
    
    # Kiểm tra số lần thử HTML riêng (tối đa 3 lần)
    html_attempt = state.get("html_attempt", 0)
    if html_attempt >= 3:
        return "end"
    
    # Còn lần thử HTML, retry
    return "retry_html"


def should_retry_js_or_continue(state: ReportState) -> Literal["retry_js", "continue", "end"]:
    """Quyết định hướng đi tiếp theo sau create_javascript"""
    
    # Nếu tạo JS thành công, tiếp tục
    if state["success"] and state.get("js_content"):
        return "continue"
    
    # Kiểm tra số lần thử JS riêng (tối đa 3 lần)
    js_attempt = state.get("js_attempt", 0)
    if js_attempt >= 3:
        return "end"
    
    # Còn lần thử JS, retry
    return "retry_js"


def should_retry_css_or_continue(state: ReportState) -> Literal["retry_css", "continue", "end"]:
    """Quyết định hướng đi tiếp theo sau create_css"""
    
    # Nếu tạo CSS thành công, tiếp tục
    if state["success"] and state.get("css_content"):
        return "continue"
    
    # Kiểm tra số lần thử CSS riêng (tối đa 3 lần)
    css_attempt = state.get("css_attempt", 0)
    if css_attempt >= 3:
        return "end"
    
    # Còn lần thử CSS, retry
    return "retry_css"
