# Crypto Dashboard & AI Report Generator

Ứng dụng Flask cung cấp dashboard thị trường tiền mã hoá thời gian thực và bộ tạo báo cáo AI tự động.

Tính năng chính:
- Dashboard real-time (WebSocket/Socket.IO) với biểu đồ SVG.
- Trình tạo báo cáo AI sử dụng workflow (LangGraph) để nghiên cứu, xác thực và sinh nội dung báo cáo.
- Xuất báo cáo sang HTML/PDF (A4) với hỗ trợ in ấn và layout tối ưu.
- Hỗ trợ PWA: cài đặt trên thiết bị, offline cache và push notifications.
- Hỗ trợ song ngữ (Tiếng Việt / English) cho nội dung báo cáo và giao diện chính.

Nhanh chóng (Quick start):

1. Tải mã nguồn

```bash
git clone https://github.com/thichuong/Crypto-Dashboard-and-AI-ReportGenerator.git
cd Crypto-Dashboard-and-AI-ReportGenerator
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Cấu hình môi trường (ví dụ `.env`)

```env
FLASK_ENV=development
GEMINI_API_KEY=your_gemini_key
ENABLE_AUTO_REPORT_SCHEDULER=true
DATABASE_URL=sqlite:///instance/local_dev.db
```

3. Chạy ứng dụng

```bash
python run.py
```

Thư mục quan trọng:
- `app/` — mã nguồn Flask (routes, services, templates)
- `app/services/` — logic sinh báo cáo và workflow
- `app/templates/` — HTML templates (bao gồm `index.html` và `pdf_template.html`)
- `static/` — tài nguyên CSS/JS và module chart

Góp phần:
- Mọi đóng góp, báo lỗi, đề xuất tính năng: mở Issue trên GitHub.

License: MIT
# 📊 Crypto Dashboard & AI Report Generator

Ứng dụng Flask hiện đại với **WebSocket real-time updates** và **Progressive Web App (PWA)** hỗ trợ, cung cấp dashboard thị trường crypto và AI report generator sử dụng LangGraph workflow.

**🔗 Demo:** [ai-crypto-reports.up.railway.app](https://ai-crypto-reports.up.railway.app/)

## ✨ Tính Năng Nổi Bật

### 🚀 **Real-time Architecture**
* **⚡ WebSocket Updates**: Instant data updates với < 1s latency
* **� Smart Fallback**: Auto-switch từ WebSocket sang polling khi cần
* **📱 PWA Support**: Installable app với offline functionality
* **🔔 Push Notifications**: Background alerts cho report completion

### 📈 **Crypto Dashboard**
* **Real-time Data**: BTC price, market cap, Fear & Greed Index, RSI
* **Live Charts**: SVG charts với real-time price updates
* **Mobile Optimized**: Responsive design với dark/light theme
* **Offline Mode**: Cached data availability khi offline

### 🤖 **AI Report Generator** 
* **LangGraph Workflow**: 6-node pipeline với state management
* **File Upload**: Support .docx, .odt, .pdf files
* **Auto Reports**: Scheduled background report generation
* **Smart Retry**: Exponential backoff với dual retry system

### 📱 **Progressive Web App Features**
* **App Installation**: Add to home screen on mobile/desktop
* **Offline Functionality**: Works without internet connection
* **Background Sync**: Data synchronization when back online
* **Native Experience**: App-like UI/UX với service worker support

## 🔄 LangGraph Workflow


### LangGraph V2 Pipeline (component-based)

**Pipeline các bước:**
`prepare_data` → `research_deep` → `validate_report` → `generate_report_content` → `create_html` → `create_javascript` → `create_css` → `translate_content` → `save_database`

**Chi tiết các bước:**
- **prepare_data**: Chuẩn bị dữ liệu đầu vào, session và `api_key`
- **research_deep**: Nghiên cứu chuyên sâu (thực thi với retry routing khi cần)
- **validate_report**: Kiểm tra chất lượng báo cáo; bước này có routing thông minh có thể dẫn về `research_deep` để retry, tiếp tục sang `generate_report_content`, hoặc kết thúc workflow
- **generate_report_content**: Sinh nội dung báo cáo (text)
- **create_html**: Tạo HTML cho báo cáo; có conditional retry riêng (tăng `html_attempt` mỗi lần)
- **create_javascript**: Sinh mã JavaScript cho dashboard; có conditional retry riêng (tăng `js_attempt` mỗi lần)
- **create_css**: Sinh CSS cho giao diện; có conditional retry riêng (tăng `css_attempt` mỗi lần)
- **translate_content**: (tùy chọn) Dịch/nối nội dung trước khi lưu
- **save_database**: Lưu kết quả cuối cùng vào database

**Logic retry & routing:**
- `validate_report` có thể trả về một trong: `retry` → quay lại `research_deep`, `continue` → sang `generate_report_content`, hoặc `end` → kết thúc workflow
- Các bước giao diện (`create_html`, `create_javascript`, `create_css`) có conditional edges riêng: `retry_html`/`retry_js`/`retry_css` để lặp lại bước tương ứng, `continue` để chuyển bước, hoặc `end` để dừng workflow
- `max_attempts` (mặc định 3) được truyền vào workflow; các bước interface tăng các counters `html_attempt`, `js_attempt`, `css_attempt` trong trạng thái
- Nếu vượt quá số lần retry cho một bước, workflow có thể kết thúc với trạng thái lỗi

**Progress tracking:**
- Workflow V2 dùng `progress_tracker` và bắt đầu với `total_steps=10` (một tiến trình theo `session_id`)
- `session_id` được tạo tự động nếu không cung cấp; tiến trình được cập nhật (ví dụ: step 0 = initializing)

**Return shape / metadata:**
Workflow luôn trả về một dict có các khóa dự đoán được, bao gồm:
- `success` (bool)
- `session_id` (str)
- `report_id` (str | None)
- `html_content`, `css_content`, `js_content`, `research_content` (str)
- `error_messages` (list[str])
- `execution_time` (float, giây)
- `validation_result` (str)
- `html_attempt`, `js_attempt`, `css_attempt` (int) — số lần thử cho từng bước giao diện

**Fallback / local dev behaviour:**
- Nếu `langgraph` không có sẵn, workflow sử dụng một stub implementation hữu dụng cho development và test; stub đảm bảo trả về các khóa trên (ví dụ `report_id`, `html_content`, `research_content`) để caller có thể xử lý đồng nhất

**Backward compatibility / wrappers:**
- Có các wrapper để duy trì tương thích với API cũ: `create_report_workflow()` (legacy factory) và `generate_auto_research_report_langgraph()` là alias cho `generate_auto_research_report_langgraph_v2()`

**Tích hợp:**
- Google Gemini API vẫn được sử dụng cho research step khi cấu hình API key
- Cache và injection dữ liệu từ nhiều nguồn API tiếp tục được hỗ trợ

## 🛠️ Tech Stack

**Backend:** Flask, Flask-SocketIO, SQLAlchemy, LangGraph, Google Gemini API  
**Frontend:** WebSocket Client, Service Worker, Tailwind CSS, Custom SVG Charts  
**Real-time:** Socket.IO, WebSocket with polling fallback  
**PWA:** Service Worker, Web App Manifest, Push Notifications API  
**Database:** PostgreSQL (prod) / SQLite (dev)  
**Deployment:** Railway cloud platform

### 🏗️ **Modern Architecture**
```
┌─────────────────────────────────────────────────────────────┐
│                    PWA CRYPTO DASHBOARD                     │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Frontend      │   Backend       │   Infrastructure        │
├─────────────────┼─────────────────┼─────────────────────────┤
│ • WebSocket     │ • Socket.IO     │ • Service Worker        │
│   Client        │   Server        │ • Push Notifications    │
│ • PWA Manager   │ • Event         │ • Background Sync       │
│ • Offline Cache │   Broadcasting  │ • Cache API             │
│ • Push Handler  │ • Redis Pub/Sub │ • IndexedDB             │
└─────────────────┴─────────────────┴─────────────────────────┘
```

## 🚀 Quick Start

```bash
git clone https://github.com/thichuong/crypto-dashboard-app.git
cd crypto-dashboard-app
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python run.py
```

**Environment Setup:**
```env
GEMINI_API_KEY=your_gemini_key          # Required for AI reports
ENABLE_AUTO_REPORT_SCHEDULER=true       # Auto reports every 3 hours
COINGECKO_API_KEY=optional              # Higher rate limits

# WebSocket & PWA Settings (Optional)
SOCKETIO_ASYNC_MODE=threading           # SocketIO async mode
REDIS_URL=redis://localhost:6379        # Redis for scaling (optional)
VAPID_PUBLIC_KEY=your_vapid_public      # Push notifications
VAPID_PRIVATE_KEY=your_vapid_private    # Push notifications
```

### 🔗 **WebSocket Connection**
The app automatically connects via WebSocket for real-time updates. If WebSocket fails, it gracefully falls back to polling mode ensuring continuous functionality.

### 📱 **PWA Installation**  
1. Visit the app in Chrome/Edge/Safari
2. Look for "Install" button in address bar
3. Click "Install" for native app experience
4. Enable notifications for background updates

## 📖 Cách Sử Dụng

### 📊 **Real-time Dashboard**
1. **Live Updates**: Dữ liệu crypto cập nhật real-time qua WebSocket
2. **Connection Status**: Hiển thị trạng thái kết nối (WebSocket/Polling)
3. **Offline Mode**: Xem cached data khi mất kết nối internet
4. **PWA Features**: Install app để có trải nghiệm native

### 📝 **Report Generation**  
1. **Manual Reports**: Upload file (.docx, .odt, .pdf) tại `/upload`
2. **Auto Reports**: Enable scheduler trong `.env` cho báo cáo tự động
3. **Real-time Progress**: Live progress tracking qua WebSocket
4. **Push Notifications**: Nhận thông báo khi báo cáo hoàn thành

### 📱 **PWA Experience**
1. **Install App**: Click "Install" button hoặc browser prompt
2. **Offline Access**: App works offline với cached data
3. **Background Sync**: Data tự động sync khi back online
4. **Push Alerts**: Notifications cho report completion (background)

## 🔧 Project Structure

```
crypto-dashboard-app/
├── 📁 app/                              # Main application package
│   ├── __init__.py                      # Flask app factory
│   ├── config.py                        # Application configuration
│   ├── extensions.py                    # Flask extensions
│   ├── models.py                        # Database models
│   ├── error_handlers.py                # Error handling
│   ├── template_helpers.py              # Template utilities
│   ├── 📁 routes/                       # Route modules (NEW)
│   │   ├── main_routes.py               # Main page routes
│   │   ├── report_routes.py             # Report generation
│   │   └── api_routes.py                # API endpoints
│   ├── 📁 services/                     # Business logic
│   │   ├── coingecko.py                 # CoinGecko API
│   │   ├── report_workflow.py           # LangGraph workflow
│   │   └── auto_report_scheduler.py     # Background scheduler
│   ├── 📁 static/                       # CSS, JS, charts
│   └── 📁 templates/                    # HTML templates
├── 📁 create_report/                    # AI prompt templates
├── 📁 tests/                           # Testing tools
└── 📄 requirements.txt                 # Dependencies
```

**Modular Architecture Benefits:**
* Routes phân chia theo chức năng (main, report, API)
* Easy maintenance với separated concerns
* Better scalability cho team development

## 🆕 Recent Updates

### v2.9.0 - Advanced Prompt Engineering & AI Tuning (Current)
* **🧠 Advanced Prompt Engineering**: Tái cấu trúc prompt nghiên cứu cốt lõi để bao gồm các nguồn dữ liệu đa tầng (Tier 1: Bloomberg, Reuters; Tier 2: Tài liệu học thuật, hồ sơ SEC), tăng cường chiều sâu phân tích.
* **🐋 Whale & Institutional Tracking**: Tích hợp các từ khóa và chiến lược cụ thể để giám sát các động thái của cá voi, thay đổi trong kho bạc của các công ty và dòng vốn của các quỹ tổ chức.
* **⚡ Breaking News Analysis**: Thêm một module chuyên dụng để xác thực và đánh giá tác động của các tin tức nóng trong thời gian thực.
* **⚙️ AI Configuration Optimization**: Tinh chỉnh các tham số `temperature` và `candidate_count` để ưu tiên độ chính xác thực tế và hiệu quả chi phí thay vì các kết quả sáng tạo (nhưng rủi ro).
* **📚 Multi-dimensional Expert Analysis**: Mở rộng prompt để tham chiếu chéo thông tin chi tiết từ các nhà phân tích Phố Wall, chuyên gia crypto-native và nghiên cứu học thuật.

### v2.8.0 - Modular Architecture Refactoring
* **🏗️ Modular Structure**: Tách `app/__init__.py` thành các module riêng biệt
* **📁 Route Organization**: Phân chia routes thành `main_routes.py`, `report_routes.py`, `api_routes.py`
* **🔧 Clean Architecture**: Separation of concerns và single responsibility principle

### Previous Versions
* **v2.7.0**: Print & PDF Export với A4 layout optimization
* **v2.6.0**: Combined Research + Validation với Google Gemini
* **v2.5.0**: LangGraph integration với state management

---

## � Support & Contact

**🔗 Demo**: [Live Application](https://ai-crypto-reports.up.railway.app/)  
**� Issues**: [GitHub Issues](https://github.com/thichuong/crypto-dashboard-app/issues)  
**� License**: MIT License

**⭐ Nếu project này hữu ích, hãy star repo để support development!**

### v2.7.0 - Print & PDF Export Features
* **�️ Print Templates**: Tối ưu A4 layout với PDF template chuyên nghiệp
* **📄 Auto-expand Details**: Tự động mở tất cả accordion/details elements khi in
* **🎨 Typography Optimization**: Font sizes, line heights và spacing chuẩn cho in ấn
* **� Chart Preservation**: SVG charts giữ nguyên chất lượng cao khi export PDF
* **⚙️ Smart Page Breaks**: Intelligent page break control để tránh cắt nội dung
* **📱 Print Controls**: In-browser print controls với preview A4 real-time
* **🔧 JavaScript Modules**: Report initialization modules cho visual components

### Previous Versions
* **v2.6.0**: Combined Research + Validation với thinking budget 30,000
* **v2.5.0**: Simplified UI với button loading states
* **v2.4.0**: Enhanced validation system với fallback logic
* **v2.3.0**: LangGraph integration với state management
* **v2.2.0**: Auto report scheduler với background tasks
* **v2.1.0**: Combined chart system với SVG optimization

## 🚀 Performance & Scalability

### ⚡ Performance Metrics
* **Dashboard load time**: < 2s on 3G connection
* **Chart rendering**: < 500ms cho complex charts
* **API response time**: < 1s với caching
* **Report generation**: 3-5 minutes cho complete workflow
* **Print preparation**: < 1s cho A4 layout optimization
* **PDF export quality**: Vector-based charts với crisp text
* **Mobile performance**: 90+ Lighthouse score

### 📈 Scalability Features
* **Horizontal scaling**: Stateless design cho multiple instances
* **Database optimization**: Indexed queries và lazy loading
* **Caching strategy**: Multi-layer caching (Redis + browser)
* **API rate limiting**: Smart throttling cho sustainable usage
* **Resource management**: Memory-efficient chart rendering

## 🛡️ Security & Privacy

### 🔒 Security Measures
* **API Key protection**: Server-side storage, không expose client
* **Input validation**: File type checking và content sanitization
* **Rate limiting**: Protection against abuse và DoS
* **CSRF protection**: Flask-WTF integration
* **Secure headers**: Security headers cho production

### 🔐 Privacy Policy
* **No data collection**: Không lưu trữ personal data
* **API keys**: Chỉ dùng cho session, không persist
* **File processing**: Files được xóa sau processing
* **Analytics**: Không track user behavior
* **GDPR compliant**: EU privacy regulation compliance

## 🤝 Contributing

### 💡 Ways to Contribute
1. **🐛 Bug Reports**: Submit issues với detailed reproduction steps
2. **✨ Feature Requests**: Suggest improvements với use cases
3. **📝 Documentation**: Improve README, comments, hoặc tutorials
4. **🧪 Testing**: Add test cases hoặc improve test coverage
5. **🎨 Design**: UI/UX improvements và accessibility

### � Development Setup
```bash
# Fork repo và clone
git clone https://github.com/your-username/crypto-dashboard-app.git
cd crypto-dashboard-app

# Setup development environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run development server
flask run

# Create feature branch
git checkout -b feature/your-feature-name
```

### 📋 Coding Standards
* **Python**: Follow PEP 8 style guide
* **JavaScript**: ES6+ với consistent formatting
* **CSS**: Tailwind utility classes preferred
* **Comments**: Document complex logic và API integrations
* **Tests**: Add tests cho new features

## �🙏 Credits

- **🔗 APIs**: CoinGecko, Alternative.me cho market data
- **🤖 AI**: Google Gemini API cho intelligent report generation
- **☁️ Deployment**: Railway cho cloud hosting  
- **🎨 Frontend**: Tailwind CSS cho utility-first styling
- **📊 Charts**: Custom SVG library với d3.js inspiration
- **🔄 Workflow**: LangGraph cho AI workflow orchestration

### 🌟 Special Thanks
- **Open Source Community**: Inspiration từ các projects tương tự
- **Contributors**: All developers đã contribute code và feedback
- **Users**: Beta testers đã provide valuable feedback
- **Documentation**: Technical writers đã help improve docs

**⭐ Nếu project này hữu ích, hãy star repo để support development!**

---

## 📞 Support & Contact

**🐛 Issues**: [GitHub Issues](https://github.com/thichuong/crypto-dashboard-app/issues)  
**💬 Discussions**: [GitHub Discussions](https://github.com/thichuong/crypto-dashboard-app/discussions)  
**📧 Email**: thichuong@example.com  
**🔗 Demo**: [Live Application](https://ai-crypto-reports.up.railway.app/)

**📄 License**: MIT License - see LICENSE file for details
