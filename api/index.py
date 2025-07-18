from flask import Flask, render_template

# Khởi tạo ứng dụng Flask
# Vercel sẽ tự động tìm biến 'app' này.
app = Flask(__name__, template_folder='../templates')

@app.route('/')
def home():
    """
    Render trang chủ từ file index.html trong thư mục templates.
    Lưu ý: template_folder được trỏ về thư mục gốc.
    """
    return render_template('index.html')

# Bạn không cần dòng `if __name__ == '__main__':` nữa
# vì Vercel sẽ xử lý việc chạy ứng dụng.