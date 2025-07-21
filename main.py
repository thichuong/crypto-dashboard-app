# main.py
from flask import Flask

# Cấu hình Flask để phục vụ các tệp từ thư mục 'static'
# static_url_path='' có nghĩa là file trong 'static' sẽ được truy cập từ URL gốc
# Ví dụ: file 'static/index.html' sẽ có thể được truy cập tại địa chỉ '/'
app = Flask(__name__, static_folder='static', static_url_path='')

@app.route('/')
def index():
    """Phục vụ file index.html từ thư mục static."""
    return app.send_static_file('index.html')

# Không cần thêm route cho report.html vì Flask sẽ tự động phục vụ nó
# khi index.html yêu cầu thông qua fetch('report.html')

# Dòng này chỉ dùng khi chạy trực tiếp file main.py trên máy tính của bạn
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)