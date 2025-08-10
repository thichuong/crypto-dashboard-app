# app/routes/__init__.py

from .main_routes import register_main_routes
from .report_routes import register_report_routes
from .api_routes import register_api_routes


def register_all_routes(app):
    """
    Đăng ký tất cả routes cho ứng dụng Flask.
    """
    register_main_routes(app)
    register_report_routes(app)
    register_api_routes(app)
