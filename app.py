from flask import Flask, render_template

# Khởi tạo ứng dụng Flask
app = Flask(__name__)

# Định nghĩa một route cho trang chủ
@app.route('/')
def home():
    """
    Hàm này sẽ được gọi khi người dùng truy cập vào trang chủ.
    Nó sẽ render file 'index.html' từ thư mục 'templates'.
    """
    return render_template('index.html')

# Chạy ứng dụng khi file này được thực thi trực tiếp
if __name__ == '__main__':
    # Bật chế độ debug để tự động tải lại khi có thay đổi
    app.run(debug=True)