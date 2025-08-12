"""
Workflow construction và main function
"""
import uuid
from datetime import datetime
from langgraph.graph import StateGraph, END

from .workflow_nodes.base import ReportState
from .workflow_nodes.prepare_data import prepare_data_node
from .workflow_nodes.research_deep import research_deep_node
from .workflow_nodes.validate_report import validate_report_node
from .workflow_nodes.create_interface import create_interface_node
from .workflow_nodes.extract_code import extract_code_node
from .workflow_nodes.save_database import save_database_node
from .workflow_nodes.routing import should_retry_or_continue, should_retry_interface_or_continue
from .progress_tracker import progress_tracker


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
    
    # Conditional routing sau extract_code
    workflow.add_conditional_edges(
        "extract_code",
        should_retry_interface_or_continue,
        {
            "retry_interface": "create_interface",
            "continue": "save_database",
            "end": END
        }
    )
    
    workflow.add_edge("save_database", END)
    
    return workflow.compile()


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
        realtime_data=None,
        html_content=None,
        css_content=None,
        js_content=None,
        report_id=None,
        current_attempt=0,
        error_messages=[],
        success=False,
        client=None,
        model="gemini-2.5-flash"
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
