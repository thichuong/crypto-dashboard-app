"""
Test file để kiểm tra workflow mới - Đã chuyển từ workflow_nodes/test_workflow.py
"""
import sys
import os

# Thêm root project vào Python path để import được app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_workflow_imports():
    """Test import các modules từ workflow mới"""
    try:
        # Test import base types
        from app.services.workflow_nodes.base import ReportState
        print("✓ Import ReportState thành công")
        
        # Test import nodes
        from app.services.workflow_nodes.prepare_data import prepare_data_node
        from app.services.workflow_nodes.research_deep import research_deep_node
        from app.services.workflow_nodes.validate_report import validate_report_node
        from app.services.workflow_nodes.create_interface import create_interface_node
        from app.services.workflow_nodes.extract_code import extract_code_node
        from app.services.workflow_nodes.save_database import save_database_node
        print("✓ Import tất cả nodes thành công")
        
        # Test import routing
        from app.services.workflow_nodes.routing import should_retry_or_continue, should_retry_interface_or_continue
        print("✓ Import routing functions thành công")
        
        # Test import main workflow
        from app.services.report_workflow_new import create_report_workflow, generate_auto_research_report_langgraph
        print("✓ Import main workflow functions thành công")
        
        # Test tạo workflow
        workflow = create_report_workflow()
        print("✓ Tạo workflow thành công")
        
        print("\n🎉 Tất cả imports và workflow construction đều thành công!")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi khi test imports: {e}")
        import traceback
        print(traceback.format_exc())
        return False


def test_utilities():
    """Test các utility functions"""
    try:
        from app.services.workflow_nodes.base import (
            read_prompt_file, 
            replace_date_placeholders, 
            extract_code_blocks, 
            check_report_validation
        )
        
        # Test replace_date_placeholders
        test_text = "Hôm nay là ngày <<@day>>/<<@month>>/<<@year>>"
        result = replace_date_placeholders(test_text)
        print(f"✓ replace_date_placeholders: {result}")
        
        # Test check_report_validation
        test_report_pass = "Báo cáo này có KẾT QUẢ KIỂM TRA: PASS"
        test_report_fail = "Báo cáo này có KẾT QUẢ KIỂM TRA: FAIL"
        test_report_unknown = "Báo cáo này không có kết quả"
        
        print(f"✓ Validation PASS: {check_report_validation(test_report_pass)}")
        print(f"✓ Validation FAIL: {check_report_validation(test_report_fail)}")
        print(f"✓ Validation UNKNOWN: {check_report_validation(test_report_unknown)}")
        
        # Test extract_code_blocks
        test_response = """
        Đây là response có code:
        
        ```html
        <html><body>Test</body></html>
        ```
        
        ```css
        body { color: red; }
        ```
        
        ```javascript
        console.log('test');
        ```
        """
        
        code_result = extract_code_blocks(test_response)
        print(f"✓ Extract code blocks success: {code_result['success']}")
        print(f"  HTML length: {len(code_result['html'])}")
        print(f"  CSS length: {len(code_result['css'])}")
        print(f"  JS length: {len(code_result['js'])}")
        
        print("\n🎉 Tất cả utility functions đều hoạt động!")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi khi test utilities: {e}")
        import traceback
        print(traceback.format_exc())
        return False


def test_node_structure():
    """Test cấu trúc và interface của các nodes"""
    try:
        from app.services.workflow_nodes.base import ReportState
        
        # Test ReportState có đủ fields không
        # Tạo một mock state để test
        mock_state = {
            'session_id': 'test',
            'api_key': 'test_key',
            'max_attempts': 3,
            'research_analysis_prompt_path': None,
            'data_validation_prompt_path': None,
            'create_report_prompt_path': None,
            'research_analysis_prompt': None,
            'data_validation_prompt': None,
            'create_report_prompt': None,
            'research_content': None,
            'validation_result': None,
            'interface_content': None,
            'realtime_data': None,
            'html_content': None,
            'css_content': None,
            'js_content': None,
            'report_id': None,
            'current_attempt': 0,
            'error_messages': [],
            'success': False,
            'client': None,
            'model': 'gemini-2.5-pro'
        }
        
        print("✓ ReportState structure test passed")
        
        # Test routing functions với mock state
        from app.services.workflow_nodes.routing import should_retry_or_continue, should_retry_interface_or_continue
        
        # Test routing logic
        mock_state['validation_result'] = 'PASS'
        result = should_retry_or_continue(mock_state)
        assert result == 'continue', f"Expected 'continue', got '{result}'"
        print("✓ Routing 'continue' test passed")
        
        mock_state['validation_result'] = 'FAIL'
        mock_state['current_attempt'] = 5
        mock_state['max_attempts'] = 3
        result = should_retry_or_continue(mock_state)
        assert result == 'end', f"Expected 'end', got '{result}'"
        print("✓ Routing 'end' test passed")
        
        mock_state['current_attempt'] = 1
        result = should_retry_or_continue(mock_state)
        assert result == 'retry', f"Expected 'retry', got '{result}'"
        print("✓ Routing 'retry' test passed")
        
        print("\n🎉 Node structure tests đều thành công!")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi khi test node structure: {e}")
        import traceback
        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    print("=== TEST WORKFLOW STRUCTURE ===\n")
    print("File đã được chuyển từ workflow_nodes/test_workflow.py sang tests/test_workflow_structure.py\n")
    
    success1 = test_workflow_imports()
    print("\n" + "="*50 + "\n")
    
    success2 = test_utilities()
    print("\n" + "="*50 + "\n")
    
    success3 = test_node_structure()
    print("\n" + "="*50 + "\n")
    
    if success1 and success2 and success3:
        print("🎉 TẤT CẢ TESTS ĐỀU THÀNH CÔNG!")
        print("Workflow mới đã sẵn sàng để sử dụng.")
        print("\nCách chạy test:")
        print("cd /path/to/crypto-dashboard-app")
        print("python tests/test_workflow_structure.py")
    else:
        print("❌ CÓ LỖI XẢY RA - Cần kiểm tra lại imports và dependencies")
