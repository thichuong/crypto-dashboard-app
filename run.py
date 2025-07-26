# run.py
from app import create_app
import os

# Gọi hàm create_app để tạo một instance của ứng dụng Flask
app = create_app()

if __name__ == '__main__':
    # Lấy host và port từ biến môi trường hoặc dùng giá trị mặc định
    host = os.environ.get('FLASK_RUN_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_RUN_PORT', 8080))
    
    # Chạy ứng dụng
    # debug=True chỉ nên dùng cho môi trường phát triển
    app.run(host=host, port=port, debug=True)