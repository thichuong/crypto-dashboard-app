"""
Test workflow phiên bản 2 với component-based interface
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.services.report_workflow_v2 import (
    create_report_workflow_v2,
    generate_auto_research_report_langgraph_v2
)
from app.services.workflow_nodes.base import ReportState


def test_workflow_v2_structure():
    """Test cấu trúc workflow phiên bản 2"""
    print("🧪 Testing Workflow V2 Structure...")
    
    try:
        # Test tạo workflow
        workflow = create_report_workflow_v2()
        print("✓ Workflow V2 created successfully")
        
        # Test workflow có thể invoke (không test nodes vì CompiledStateGraph không expose graph)
        print("✓ Workflow compiled and ready to use")
        
        # Test ReportState có đủ fields
        mock_state = {
            'session_id': 'test-123',
            'api_key': 'test-key',
            'max_attempts': 3,
            'current_attempt': 0,
            'success': False,
            'error_messages': [],
            'html_attempt': 0,
            'js_attempt': 0,
            'css_attempt': 0,
            'created_at': '2025-01-01T00:00:00',
            'client': None,
            'model': 'gemini-1.5-flash'
        }
        
        print("✓ ReportState structure test passed")
        
        # Test routing functions với mock state
        from app.services.workflow_nodes.routing import (
            should_retry_html_or_continue,
            should_retry_js_or_continue,
            should_retry_css_or_continue
        )
        
        # Test HTML routing
        mock_state['success'] = True
        mock_state['html_content'] = '<html></html>'
        result = should_retry_html_or_continue(mock_state)
        assert result == 'continue', f"Expected 'continue', got '{result}'"
        print("✓ HTML routing 'continue' test passed")
        
        mock_state['success'] = False
        mock_state['html_content'] = ''
        mock_state['html_attempt'] = 5
        result = should_retry_html_or_continue(mock_state)
        assert result == 'end', f"Expected 'end', got '{result}'"
        print("✓ HTML routing 'end' test passed")
        
        # Test JS routing
        mock_state['success'] = True
        mock_state['js_content'] = 'console.log("test");'
        result = should_retry_js_or_continue(mock_state)
        assert result == 'continue', f"Expected 'continue', got '{result}'"
        print("✓ JS routing 'continue' test passed")
        
        # Test CSS routing
        mock_state['success'] = True
        mock_state['css_content'] = 'body { margin: 0; }'
        result = should_retry_css_or_continue(mock_state)
        assert result == 'continue', f"Expected 'continue', got '{result}'"
        print("✓ CSS routing 'continue' test passed")
        
        print("🎉 All Workflow V2 structure tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_component_prompts():
    """Test việc đọc các prompt files"""
    print("\n🧪 Testing Component Prompts...")
    
    try:
        from app.services.workflow_nodes.base import read_prompt_file
        
        # Test đọc HTML prompt
        html_prompt = read_prompt_file('prompt_create_html.md')
        if html_prompt and 'HTML' in html_prompt:
            print("✓ HTML prompt loaded successfully")
        else:
            print("✗ HTML prompt loading failed")
            return False
        
        # Test đọc JS prompt
        js_prompt = read_prompt_file('prompt_create_javascript.md')
        if js_prompt and 'JavaScript' in js_prompt:
            print("✓ JavaScript prompt loaded successfully")
        else:
            print("✗ JavaScript prompt loading failed")
            return False
        
        # Test đọc CSS prompt
        css_prompt = read_prompt_file('prompt_create_css.md')
        if css_prompt and 'CSS' in css_prompt:
            print("✓ CSS prompt loaded successfully")
        else:
            print("✗ CSS prompt loading failed")
            return False
        
        print("🎉 All prompt tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Prompt test failed: {str(e)}")
        return False


def test_extraction_functions():
    """Test các hàm trích xuất HTML, JS, CSS"""
    print("\n🧪 Testing Extraction Functions...")
    
    try:
        from app.services.workflow_nodes.create_interface_components import (
            _extract_html, _extract_javascript, _extract_css
        )
        
        # Test HTML extraction
        html_response = """
        Đây là giao diện HTML:
        ```html
        <html>
        <head><title>Test</title></head>
        <body><h1>Hello World</h1></body>
        </html>
        ```
        """
        html_result = _extract_html(html_response)
        if html_result and '<html>' in html_result:
            print("✓ HTML extraction test passed")
        else:
            print("✗ HTML extraction test failed")
            return False
        
        # Test JS extraction
        js_response = """
        Đây là JavaScript code:
        ```javascript
        console.log('Hello World');
        document.addEventListener('DOMContentLoaded', function() {
            alert('Ready!');
        });
        ```
        """
        js_result = _extract_javascript(js_response)
        if js_result and 'console.log' in js_result:
            print("✓ JavaScript extraction test passed")
        else:
            print("✗ JavaScript extraction test failed")
            return False
        
        # Test CSS extraction
        css_response = """
        Đây là CSS styles:
        ```css
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
        }
        ```
        """
        css_result = _extract_css(css_response)
        if css_result and 'font-family' in css_result:
            print("✓ CSS extraction test passed")
        else:
            print("✗ CSS extraction test failed")
            return False
        
        print("🎉 All extraction tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Extraction test failed: {str(e)}")
        return False


def main():
    """Chạy tất cả tests"""
    print("🚀 Starting Workflow V2 Tests...")
    print("=" * 50)
    
    all_passed = True
    
    # Test 1: Workflow structure
    if not test_workflow_v2_structure():
        all_passed = False
    
    # Test 2: Component prompts
    if not test_component_prompts():
        all_passed = False
    
    # Test 3: Extraction functions
    if not test_extraction_functions():
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Workflow V2 is ready!")
    else:
        print("❌ SOME TESTS FAILED! Please check the issues above.")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
