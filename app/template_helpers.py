# app/template_helpers.py

import os
from datetime import timedelta


def register_template_helpers(app):
    """
    Đăng ký template globals và helper functions.
    """
    
    def get_chart_modules_content():
        """Đọc và nối tất cả file .js trong chart_modules với thứ tự tối ưu"""
        from flask import current_app
        
        source_dir = os.path.join(app.static_folder, "js", "chart_modules")
        
        # Định nghĩa thứ tự ưu tiên (dependency order)
        priority_order = ["gauge.js", "bar.js", "line.js", "doughnut.js"]
        
        # Check cache trong development mode
        cache_key = 'chart_modules_content'
        if not current_app.debug:
            cached_content = getattr(app, '_chart_modules_cache', None)
            if cached_content:
                return cached_content
        
        try:
            # Lấy tất cả file .js trong thư mục
            all_js_files = [f for f in os.listdir(source_dir) if f.endswith('.js')]
            
            # Sắp xếp theo thứ tự ưu tiên + alphabet cho file mới
            ordered_files = []
            
            # Thêm file theo thứ tự ưu tiên trước
            for priority_file in priority_order:
                if priority_file in all_js_files:
                    ordered_files.append(priority_file)
                    all_js_files.remove(priority_file)
            
            # Thêm các file còn lại theo alphabet
            ordered_files.extend(sorted(all_js_files))
            
            # Đọc và nối nội dung
            content_parts = []
            for filename in ordered_files:
                filepath = os.path.join(source_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        file_content = f.read()
                        
                        # Add file metadata và error handling
                        wrapped_content = f"""// ==================== {filename} ====================
try {{
{file_content}
}} catch (error) {{
    console.error('Error loading chart module {filename}:', error);
}}
// ==================== End {filename} ===================="""
                        content_parts.append(wrapped_content)
                        
                except FileNotFoundError:
                    print(f"Warning: Chart module {filename} not found")
                    content_parts.append(f"// Warning: {filename} not found")
            
            final_content = "\n\n".join(content_parts)
            
            # Cache in production
            if not current_app.debug:
                app._chart_modules_cache = final_content
            
            return final_content
            
        except FileNotFoundError:
            print(f"Warning: Chart modules directory not found at {source_dir}")
            return "// No chart modules found"

    app.jinja_env.globals.update(timedelta=timedelta)
    app.jinja_env.globals['get_chart_modules_content'] = get_chart_modules_content
