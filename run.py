# run.py
from app import create_app
import os
from build import build_js

# Gọi hàm create_app để tạo một instance của ứng dụng Flask
app = create_app()

# Vercel configuration for maxDuration
config = {"maxDuration": 30}

# Đoạn mã này đảm bảo việc build chỉ xảy ra một lần khi bạn
# khởi động ứng dụng ở chế độ debug (ví dụ: flask run --debug)
# và sẽ không chạy trên môi trường production.
if app.debug and not os.getenv('VERCEL'):
    build_js()

# Vercel expects an app variable to be exported
# This is the WSGI callable that Vercel will use
if __name__ == '__main__':
    # Lấy host và port từ biến môi trường hoặc dùng giá trị mặc định
    host = os.environ.get('FLASK_RUN_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_RUN_PORT', 8080))
    
    # Chỉ enable debug mode khi không phải trên Vercel
    debug_mode = not os.getenv('VERCEL', False)
    
    # Chạy ứng dụng
    app.run(host=host, port=port, debug=debug_mode)