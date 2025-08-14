"""
Workflow construction và main function - Phiên bản nâng cấp với component-based interface
"""
import uuid
from datetime import datetime
from langgraph.graph import StateGraph, END

from .workflow_nodes.base import ReportState
from .workflow_nodes.prepare_data import prepare_data_node
from .workflow_nodes.research_deep import research_deep_node
from .workflow_nodes.validate_report import validate_report_node
from .workflow_nodes.create_interface_components import create_html_node, create_javascript_node, create_css_node
from .workflow_nodes.generate_report_content import generate_report_content_node
from .workflow_nodes.translate_content import translate_content_node
from .workflow_nodes.save_database import save_database_node
from .workflow_nodes.routing import (
    should_retry_or_continue,
    should_retry_html_or_continue,
    should_retry_js_or_continue,
    should_retry_css_or_continue
)
from .progress_tracker import progress_tracker


def create_report_workflow_v2():
    """Tạo và cấu hình LangGraph workflow phiên bản 2 với component-based interface"""
    
    workflow = StateGraph(ReportState)
    
    # Thêm các nodes
    workflow.add_node("prepare_data", prepare_data_node)
    workflow.add_node("research_deep", research_deep_node)
    workflow.add_node("validate_report", validate_report_node)
    workflow.add_node("generate_report_content", generate_report_content_node)
    workflow.add_node("create_html", create_html_node)
    workflow.add_node("create_javascript", create_javascript_node)
    workflow.add_node("create_css", create_css_node)
    workflow.add_node("translate_content", translate_content_node)
    workflow.add_node("save_database", save_database_node)
    
    # Thiết lập entry point
    workflow.set_entry_point("prepare_data")
    
    # Thiết lập các edges 
    workflow.add_edge("prepare_data", "research_deep")
    workflow.add_edge("research_deep", "validate_report")
    
    # Conditional routing sau validation
    # After validation, generate the report text before HTML
    workflow.add_conditional_edges(
        "validate_report",
        should_retry_or_continue,
        {
            "retry": "research_deep",
            "continue": "generate_report_content",
            "end": END
        }
    )
    # Link from report content to HTML generation
    workflow.add_edge("generate_report_content", "create_html")
    
    # HTML Component với retry logic
    workflow.add_conditional_edges(
        "create_html",
        should_retry_html_or_continue,
        {
            "retry_html": "create_html",
            "continue": "create_javascript",
            "end": END
        }
    )
    
    # JavaScript Component với retry logic
    workflow.add_conditional_edges(
        "create_javascript",
        should_retry_js_or_continue,
        {
            "retry_js": "create_javascript",
            "continue": "create_css",
            "end": END
        }
    )
    
    # CSS Component với retry logic - after CSS, translate HTML content
    workflow.add_conditional_edges(
        "create_css",
        should_retry_css_or_continue,
        {
            "retry_css": "create_css",
            "continue": "translate_content",  # Translate HTML to English after CSS
            "end": END
        }
    )
    
    # After translation, save to database
    workflow.add_edge("translate_content", "save_database")
    
    # Kết thúc workflow
    workflow.add_edge("save_database", END)
    
    return workflow.compile()


def generate_auto_research_report_langgraph_v2(api_key: str, max_attempts: int = 3, session_id: str = None) -> dict:
    """
    Hàm chính để tạo báo cáo sử dụng LangGraph workflow phiên bản 2.
    
    Args:
        api_key (str): API key của Gemini
        max_attempts (int): Số lần thử tối đa để tạo báo cáo PASS
        session_id (str): Session ID để tracking progress (tự tạo nếu None)
        
    Returns:
        dict: {
            'success': bool,
            'session_id': str,
            'html_content': str,
            'css_content': str,
            'js_content': str,
            'research_content': str,
            'error_messages': list,
            'execution_time': float
        }
    """
    import time
    start_time = time.time()
    
    # Tạo session_id nếu chưa có
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Khởi tạo progress tracking
    progress_tracker.start_progress(session_id, total_steps=11)  # Updated for translate_content step
    progress_tracker.update_step(session_id, 0, "Bắt đầu", "Khởi tạo workflow phiên bản 2")
    
    try:
        # Tạo workflow
        workflow = create_report_workflow_v2()
        
        # Initial state
        initial_state = {
            "session_id": session_id,
            "api_key": api_key,
            "max_attempts": max_attempts,
            "current_attempt": 0,
            "success": False,
            "error_messages": [],
            "created_at": datetime.now().isoformat(),
            
            # Workflow specific
            "html_attempt": 0,
            "js_attempt": 0,
            "css_attempt": 0,
        }
        
        # Chạy workflow
        final_state = workflow.invoke(initial_state)
        
        execution_time = time.time() - start_time
        
        # Chuẩn bị kết quả trả về
        result = {
            'success': final_state.get('success', False),
            'session_id': session_id,
            'html_content': final_state.get('html_content', ''),
            'css_content': final_state.get('css_content', ''),
            'js_content': final_state.get('js_content', ''),
            'research_content': final_state.get('research_content', ''),
            'error_messages': final_state.get('error_messages', []),
            'execution_time': execution_time,
            'validation_result': final_state.get('validation_result', 'UNKNOWN'),
            'created_at': final_state.get('created_at', ''),
            
            # Component-specific metadata
            'html_attempt': final_state.get('html_attempt', 0),
            'js_attempt': final_state.get('js_attempt', 0),
            'css_attempt': final_state.get('css_attempt', 0),
        }
        
        # Kiểm tra kết quả
        if final_state["success"] and final_state.get("report_id"):
            return {
                'success': True,
                'session_id': session_id,
                'report_id': final_state["report_id"],
                'errors': []
            }
        else:
            error_msg = f"Workflow thất bại: {', '.join(result['error_messages'])}"
            progress_tracker.error_progress(session_id, error_msg)
        
        return result
        
    except Exception as e:
        execution_time = time.time() - start_time
        error_msg = f"Lỗi trong workflow: {str(e)}"
        progress_tracker.error_progress(session_id, error_msg)
        
        return {
            'success': False,
            'session_id': session_id,
            'html_content': '',
            'css_content': '',
            'js_content': '',
            'research_content': '',
            'error_messages': [error_msg],
            'execution_time': execution_time,
            'validation_result': 'ERROR',
            'created_at': datetime.now().isoformat(),
            'html_attempt': 0,
            'js_attempt': 0,
            'css_attempt': 0,
        }


# Backward compatibility - import workflow cũ nếu cần
def create_report_workflow():
    """Wrapper cho backward compatibility"""
    from .report_workflow import create_report_workflow as create_legacy_workflow
    return create_legacy_workflow()


def generate_auto_research_report_langgraph(api_key: str, max_attempts: int = 3, session_id: str = None) -> dict:
    """Wrapper cho backward compatibility"""
    from .report_workflow import generate_auto_research_report_langgraph as generate_legacy_report
    return generate_legacy_report(api_key, max_attempts, session_id)
