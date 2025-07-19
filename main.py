from flask import Flask, render_template

# Khởi tạo ứng dụng Flask
app = Flask(__name__)

# Tạo một route (đường dẫn) cho trang chủ
@app.route('/')
def home():
    """
    Hàm này sẽ được gọi khi người dùng truy cập vào địa chỉ gốc ('/').
    Nó sẽ tìm và trả về tệp 'index.html' từ thư mục 'templates'.
    """
    return render_template('index.html')

# Dòng này để đảm bảo máy chủ chỉ chạy khi bạn thực thi trực tiếp tệp main.py
# và cần thiết để App Engine hoạt động

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)