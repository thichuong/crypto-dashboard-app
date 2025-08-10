# Workflow Structure Documentation

## Cấu trúc mới của Workflow

Workflow đã được tách thành nhiều file riêng biệt để dễ quản lý và bảo trì:

### Cấu trúc thư mục:
```
app/services/
├── report_workflow.py              # File gốc (sẽ deprecated)
├── report_workflow_new.py          # Main workflow file mới
└── workflow_nodes/                 # Thư mục chứa các nodes
    ├── __init__.py                 # Export các nodes
    ├── base.py                     # Types và utilities chung
    ├── prepare_data.py             # Node chuẩn bị dữ liệu
    ├── research_deep.py            # Node nghiên cứu sâu
    ├── validate_report.py          # Node validation báo cáo
    ├── create_interface.py         # Node tạo giao diện
    ├── extract_code.py             # Node trích xuất code
    ├── save_database.py            # Node lưu database
    └── routing.py                  # Conditional routing functions
```

### Chi tiết từng file:

#### `base.py`
- Chứa `ReportState` TypedDict
- Các utility functions: `read_prompt_file`, `replace_date_placeholders`, `extract_code_blocks`, `check_report_validation`, `get_realtime_dashboard_data`

#### `prepare_data.py`
- Node `prepare_data_node`
- Chuẩn bị dữ liệu, khởi tạo Gemini client
- Đọc prompt files, cache real-time data

#### `research_deep.py`
- Node `research_deep_node`
- Thực hiện nghiên cứu sâu + validation trong 1 lần gọi
- Sử dụng Google Search và real-time data

#### `validate_report.py`
- Node `validate_report_node`
- Parse và verify kết quả validation
- Fallback validation logic

#### `create_interface.py`
- Node `create_interface_node`
- Tạo giao diện HTML/CSS/JS từ báo cáo nghiên cứu

#### `extract_code.py`
- Node `extract_code_node`
- Trích xuất các khối mã từ phản hồi AI

#### `save_database.py`
- Node `save_database_node`
- Lưu báo cáo vào database với proper Flask context

#### `routing.py`
- `should_retry_or_continue`
- `should_retry_interface_or_continue`
- Conditional routing logic

#### `report_workflow_new.py`
- `create_report_workflow()` - Cấu hình LangGraph workflow
- `generate_auto_research_report_langgraph()` - Main function

### Cách sử dụng:

```python
# Import từ file mới
from app.services.report_workflow_new import generate_auto_research_report_langgraph

# Hoặc import từ file gốc (tương thích ngược)
from app.services.report_workflow import generate_auto_research_report_langgraph

# Sử dụng bình thường
result = generate_auto_research_report_langgraph(api_key="...", max_attempts=3)
```

### Lợi ích của cấu trúc mới:

1. **Modularity**: Mỗi node là một file riêng, dễ test và debug
2. **Maintainability**: Dễ bảo trì và cập nhật từng phần
3. **Reusability**: Có thể tái sử dụng các nodes trong workflows khác
4. **Separation of Concerns**: Mỗi file có trách nhiệm riêng biệt
5. **Testability**: Dễ dàng viết unit tests cho từng node

### Migration Guide:

1. Giữ nguyên file `report_workflow.py` để tương thích ngược
2. Sử dụng `report_workflow_new.py` cho các tính năng mới
3. Dần dần migrate các imports sang file mới
4. Sau khi test đầy đủ, có thể thay thế hoàn toàn file cũ
