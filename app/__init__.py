import os
from flask import Flask, render_template
from dotenv import load_dotenv
from .utils.cache import cache
from .blueprints.crypto import crypto_bp

def create_app():
    """
    Hàm factory để tạo và cấu hình ứng dụng Flask.
    """
    load_dotenv()

    app = Flask(__name__)

    # Cấu hình cache dựa trên môi trường
    if 'KV_URL' in os.environ:
        config = {
            "CACHE_TYPE": "RedisCache",
            "CACHE_DEFAULT_TIMEOUT": 3600,
            "CACHE_REDIS_URL": os.environ['KV_URL']
        }
    else:
        config = {
            "CACHE_TYPE": "SimpleCache",
            "CACHE_DEFAULT_TIMEOUT": 3600
        }
    app.config.from_mapping(config)

    # Khởi tạo cache với ứng dụng
    cache.init_app(app)

    @app.route('/')
    def index():
        """Phục vụ file index.html từ thư mục templates."""
        return render_template('index.html')

    # Đăng ký blueprint cho các route API
    app.register_blueprint(crypto_bp, url_prefix='/api/crypto')

    return app

