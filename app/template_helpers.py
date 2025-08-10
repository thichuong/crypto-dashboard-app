# app/template_helpers.py

import os
from datetime import timedelta


def register_template_helpers(app):
    """
    Đăng ký template globals và helper functions.
    """
    
    def get_chart_modules_content():
        """Đọc và nối tất cả file trong chart_modules theo thứ tự đúng"""
        source_dir = os.path.join(app.static_folder, "js", "chart_modules")
        file_order = ["gauge.js", "bar.js", "line.js", "doughnut.js"]
        
        content = ""
        for fname in file_order:
            fpath = os.path.join(source_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content += f.read() + "\n\n"
            except FileNotFoundError:
                print(f"Warning: Chart module {fname} not found at {fpath}")
        
        return content

    app.jinja_env.globals.update(timedelta=timedelta)
    app.jinja_env.globals['get_chart_modules_content'] = get_chart_modules_content
