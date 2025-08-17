# app/__init__.py

import os
from flask import Flask

# Import các phần mở rộng và model
from .extensions import db
from .models import CryptoReport as Report

# Import các blueprints và services khác
from .utils.cache import cache
from .blueprints.crypto import crypto_bp
from .services.auto_report_scheduler import start_auto_report_scheduler

# Import WebSocket manager và progress tracker
from .websocket.manager import websocket_manager
from .services.progress_tracker import progress_tracker

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
    
    # Initialize WebSocket manager
    websocket_manager.init_app(app)
    
    # Connect progress tracker to WebSocket manager
    progress_tracker.set_websocket_manager(websocket_manager)

    # Initialize database tables in a non-blocking way for Railway
    def init_database():
        try:
            with app.app_context():
                print("INFO: Initializing database tables...")
                db.create_all()
                print("INFO: Database tables initialized.")
        except Exception as e:
            print(f"WARNING: Database initialization failed: {e}")
            print("INFO: App will continue running without database initialization")
    
    # For Railway, defer database initialization to prevent blocking startup
    if os.getenv('RAILWAY_ENVIRONMENT'):
        # In production (Railway), defer database initialization
        import threading
        db_thread = threading.Thread(target=init_database)
        db_thread.daemon = True
        db_thread.start()
        print("INFO: Database initialization deferred to background thread")
    else:
        # In development, initialize immediately
        init_database()

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