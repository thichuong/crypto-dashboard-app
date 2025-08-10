# app/__init__.py

from flask import Flask

# Import các phần mở rộng và model
from .extensions import db
from .models import Report

# Import các blueprints và services khác
from .utils.cache import cache
from .blueprints.crypto import crypto_bp
from .services.auto_report_scheduler import start_auto_report_scheduler

# Import các module đã tách
from .config import configure_app
from .routes import register_all_routes
from .error_handlers import register_error_handlers
from .template_helpers import register_template_helpers

def create_app():
    """
    Hàm factory để tạo và cấu hình ứng dụng Flask.
    """
    app = Flask(__name__)
    
    # Cấu hình ứng dụng
    configure_app(app)

    # Khởi tạo các phần mở rộng
    db.init_app(app)
    cache.init_app(app)

    with app.app_context():
        print("INFO: Initializing database tables...")
        db.create_all()
        print("INFO: Database tables initialized.")

    # Khởi động auto report scheduler
    start_auto_report_scheduler(app)

    # Đăng ký routes
    register_all_routes(app)
    
    # Đăng ký blueprint
    app.register_blueprint(crypto_bp, url_prefix='/api/crypto')

    # Đăng ký template helpers
    register_template_helpers(app)

    # Đăng ký error handlers
    register_error_handlers(app)

    return app