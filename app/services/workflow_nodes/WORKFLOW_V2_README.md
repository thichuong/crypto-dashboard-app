# Workflow V2 - Component-Based Interface Generation

## Tổng quan

Workflow phiên bản 2 đã được nâng cấp để tách việc tạo giao diện thành 3 components riêng biệt:
- **HTML Component**: Tạo cấu trúc semantic
- **JavaScript Component**: Tạo tương tác và functionality  
- **CSS Component**: Tạo styling và responsive design

## Cải tiến so với Workflow V1

### Workflow V1 (Legacy):
```
prepare_data → research_deep → validate_report → create_interface → extract_code → save_database
```

### Workflow V2 (New):
```
prepare_data → research_deep → validate_report → create_html → create_javascript → create_css → save_database
```

## Lợi ích của Workflow V2

### 1. **Separation of Concerns**
- **HTML**: Tập trung vào structure và semantic
- **JavaScript**: Tập trung vào functionality và interactions
- **CSS**: Tập trung vào styling và responsive design

### 2. **Better Error Handling**
- Mỗi component có retry logic riêng (tối đa 3 lần)
- Lỗi ở component này không ảnh hưởng các component khác
- Easier debugging và troubleshooting

### 3. **Improved Quality**
- Specialized prompts cho từng component
- AI focus vào 1 responsibility tại 1 thời điểm
- Better code quality và maintainability

### 4. **Scalability**
- Dễ dàng extend với components mới
- Có thể parallel processing trong tương lai
- Component reusability

## Cấu trúc Files

```
app/services/
├── report_workflow.py                    # Legacy workflow (V1)
├── report_workflow_v2.py                 # New workflow (V2) 
└── workflow_nodes/
    ├── create_interface_components.py    # New component nodes
    └── routing.py                        # Updated routing functions

create_report/
├── prompt_create_html.md                 # HTML generation prompt
├── prompt_create_javascript.md           # JavaScript generation prompt  
└── prompt_create_css.md                 # CSS generation prompt
```

## Component Nodes

### 1. `create_html_node`
```python
def create_html_node(state: ReportState) -> ReportState:
    """Tạo HTML semantic structure từ báo cáo nghiên cứu"""
```

**Responsibilities:**
- Tạo HTML5 semantic structure
- Accessibility features (ARIA labels, alt text)
- SEO-ready structure  
- Responsive-ready markup

### 2. `create_javascript_node`
```python
def create_javascript_node(state: ReportState) -> ReportState:
    """Tạo JavaScript functionality từ báo cáo nghiên cứu"""
```

**Responsibilities:**
- Interactive elements (charts, modals, tabs)
- Data processing utilities
- Mobile responsive behaviors
- Performance optimizations

### 3. `create_css_node`
```python
def create_css_node(state: ReportState) -> ReportState:
    """Tạo CSS styling từ báo cáo nghiên cứu"""
```

**Responsibilities:**
- Professional crypto dashboard styling
- Responsive design system
- Dark/Light theme support
- Performance-optimized CSS

## Routing Logic

### Component-Specific Retry Logic
```python
def should_retry_html_or_continue(state) -> Literal["retry_html", "continue", "end"]:
def should_retry_js_or_continue(state) -> Literal["retry_js", "continue", "end"]:  
def should_retry_css_or_continue(state) -> Literal["retry_css", "continue", "end"]:
```

**Flow:**
1. Nếu component thành công → `continue`
2. Nếu thất bại và còn lần thử → `retry_[component]`
3. Nếu thất bại và hết lần thử → `end`

## State Management

### New State Fields
```python
class ReportState(TypedDict):
    # Component-specific counters
    html_attempt: Optional[int]
    js_attempt: Optional[int] 
    css_attempt: Optional[int]
    
    # Timestamps
    created_at: Optional[str]
```

## Usage

### Basic Usage
```python
from app.services.report_workflow_v2 import generate_auto_research_report_langgraph_v2

result = generate_auto_research_report_langgraph_v2(
    api_key="your-gemini-api-key",
    max_attempts=3,
    session_id="optional-session-id"
)

if result['success']:
    html = result['html_content']
    css = result['css_content'] 
    js = result['js_content']
```

### Backward Compatibility
```python
# V1 workflow vẫn hoạt động
from app.services.report_workflow import generate_auto_research_report_langgraph

# V2 workflow mới
from app.services.report_workflow_v2 import generate_auto_research_report_langgraph_v2
```

## Migration Guide

### 1. **Immediate**: Use V2 for new implementations
```python
# New projects - use V2
from app.services.report_workflow_v2 import generate_auto_research_report_langgraph_v2
```

### 2. **Gradual**: Update existing endpoints
```python
# Update route handlers one by one
@app.route('/generate-report-v2')  
def generate_report_v2():
    return generate_auto_research_report_langgraph_v2(...)
```

### 3. **Future**: Full replacement
- Test V2 thoroughly in production
- Update all imports to V2
- Remove V1 workflow when stable

## Performance Improvements

### 1. **Specialized Prompts**
- Each component gets optimized prompt
- Reduced token usage per generation
- Better quality output

### 2. **Failure Isolation**
- Component failures don't cascade
- Easier recovery and retry
- Better resource utilization

### 3. **Debugging**
- Component-level error tracking
- Granular progress reporting
- Better observability

## Testing

```bash
# Run V2 tests
python -m tests.test_workflow_v2

# All tests should pass:
# ✓ Workflow V2 structure tests
# ✓ Component prompts tests  
# ✓ Extraction functions tests
```

## Monitoring

### Progress Tracking
```python
# V2 uses 7 steps instead of 6
progress_tracker.init_progress(session_id, total_steps=7)

# Steps:
# 0: Initialize
# 1: Prepare data  
# 2: Research deep
# 3: Validate report
# 4: Create HTML
# 5: Create JavaScript
# 6: Create CSS
# 7: Save database
```

### Error Tracking
```python
result = {
    'html_attempt': 2,    # Number of HTML attempts
    'js_attempt': 1,      # Number of JS attempts  
    'css_attempt': 1,     # Number of CSS attempts
    'error_messages': [...] # Component-specific errors
}
```

## Future Enhancements

### 1. **Parallel Processing**
- HTML → (JS + CSS in parallel)
- Reduce total execution time

### 2. **Component Caching**
- Cache successful components
- Reuse across similar reports

### 3. **Advanced Routing**
- Smart retry strategies
- Component dependency handling
- Conditional component execution

---

**Recommendation**: Migrate to Workflow V2 for all new report generation tasks. The improved separation of concerns, better error handling, and component-specific optimizations provide significant benefits over the legacy workflow.
