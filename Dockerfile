# Sử dụng một image Python chính thức làm nền
FROM python:3.9-slim

# Đặt thư mục làm việc trong container
WORKDIR /app

# Sao chép file requirements.txt vào trước để tận dụng cache của Docker
COPY requirements.txt requirements.txt

# Cài đặt các thư viện cần thiết
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn của bạn vào container
COPY . .

# Gunicorn là một WSGI server mạnh mẽ cho production
# Thay thế "app:app" nếu file chính hoặc biến app của bạn có tên khác
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "api.index:app"]