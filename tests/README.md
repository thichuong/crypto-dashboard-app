# 🧪 Thư mục Tests

Thư mục này chứa các file test và debug cho các component biểu đồ của ứng dụng crypto dashboard.

## 📁 Danh sách các file test:

### 🎯 **chart_tester.html**
- **Mục đích**: Test toàn diện cho tất cả các loại biểu đồ
- **Tính năng**:
  - Test 4 loại biểu đồ: Gauge, Doughnut, Line, Bar
  - Nhập dữ liệu thủ công hoặc tạo ngẫu nhiên
  - Theme switcher (dark/light mode)
  - UI responsive và thân thiện với người dùng
  - Kiểm tra tương tác hover mượt mà

### 🍩 **test_doughnut_hover.html**
- **Mục đích**: Test chuyên biệt cho hover effects của Doughnut Chart
- **Tính năng**:
  - 3 test cases khác nhau (basic, many segments, small values)
  - Debug logging trong console
  - Test hover interaction giữa segments và legend
  - Kiểm tra hiệu ứng scale và brightness mới
  - Tối ưu hóa performance với will-change property

## 🚀 Cách sử dụng:

1. **Chạy từ thư mục gốc của project**:
   ```bash
   # Mở các file test trong trình duyệt
   open tests/chart_tester.html
   open tests/test_doughnut_hover.html
   ```

2. **Hoặc sử dụng local server** (khuyến khích):
   ```bash
   # Từ thư mục gốc
   python -m http.server 8000
   # Sau đó truy cập:
   # http://localhost:8000/tests/chart_tester.html
   # http://localhost:8000/tests/test_doughnut_hover.html
   ```

## ✨ Các cải tiến mới nhất:

### 🎨 **Hover Effects được tối ưu hóa**:
- **Transition mượt mà**: Sử dụng cubic-bezier với bounce effect tự nhiên (0.3s)
- **Scale tối ưu**: 112% thay vì 115% để mượt mà hơn
- **Brightness filter**: Tăng độ sáng nhẹ khi hover (105%)
- **Performance**: Will-change property cho hardware acceleration
- **Transform-origin**: Đảm bảo phóng to từ tâm segment

### 🔧 **Technical Improvements**:
- Loại bỏ drop-shadow để tập trung vào chuyển động
- Tối ưu easing function cho cảm giác tự nhiên
- Separate transition cho transform, opacity, và filter

## 🔍 Debug và Troubleshooting:

### Nếu gặp lỗi "File not found":
- Đảm bảo chạy từ thư mục gốc của project (`crypto-dashboard-app/`)
- Kiểm tra đường dẫn relative đến các file CSS/JS
- Sử dụng local server thay vì mở file trực tiếp

### Nếu biểu đồ không hiển thị:
1. Mở Developer Tools (F12)
2. Kiểm tra Console tab để xem lỗi JavaScript
3. Kiểm tra Network tab để xem file nào không load được
4. Verify rằng các file dependencies (utils.js, chart modules) được load

### Nếu hover không hoạt động:
1. Kiểm tra console có error về event listeners không
2. Verify CSS classes `.highlight` và `.is-highlighted` được apply
3. Kiểm tra transform và opacity values trong DevTools
4. Test với `chart_tester.html` để so sánh

## 🎯 Testing Tips:

### Kiểm tra Performance:
- Mở DevTools > Performance tab
- Record trong khi hover để xem animation smoothness
- Check GPU usage và frame rate

### CSS Debugging:
- Inspect element trong khi hover
- Kiểm tra computed styles cho transform values
- Verify transition properties được apply đúng

## 📝 Notes:

- **File paths**: Tất cả đường dẫn đã được cập nhật để hoạt động từ thư mục `tests/`
- **Independence**: Files test độc lập với ứng dụng chính, có thể chạy riêng biệt
- **Development**: Sử dụng để test trong quá trình phát triển và debugging
- **Browser compatibility**: Test trên Chrome/Firefox/Safari để đảm bảo tương thích
- **Performance**: Hover effects được tối ưu cho 60fps smooth animation
