# app/config.py

import os
from dotenv import load_dotenv


def configure_app(app):
    """
    Cấu hình ứng dụng Flask với database và cache.
    """
    load_dotenv()
    app.secret_key = os.getenv('SECRET_KEY', 'a_very_secret_key')
    
    # --- DETECT ENVIRONMENT ---
    is_production = os.getenv('FLASK_ENV') == 'production'
    
    if is_production:
        print("INFO: Running in production mode")
    else:
        print("INFO: Running in development mode")

    # --- CẤU HÌNH DATABASE ĐỘNG ---
    if postgres_url := os.getenv('POSTGRES_URL'):
        db_url = postgres_url.replace("postgres://", "postgresql://", 1)
        
        # Thêm SSL parameters cho Railway PostgreSQL
        if "?" not in db_url:
            db_url += "?sslmode=require&sslrootcert=DISABLE"
        elif "sslmode" not in db_url:
            db_url += "&sslmode=require&sslrootcert=DISABLE"
            
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
        
        # Cấu hình connection pool và retry cho Railway
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,  # Test connection trước khi sử dụng
            'pool_recycle': 300,    # Recycle connection sau 5 phút
            'pool_timeout': 30,     # Timeout khi lấy connection từ pool
            'max_overflow': 10,     # Tối đa 10 connection overflow
            'echo': False,          # Tắt SQL logging cho production
            'connect_args': {
                "sslmode": "require",
                "connect_timeout": 30,
                "application_name": "crypto_dashboard_app"
            }
        }
        print("INFO: Connecting to Postgres database with SSL optimization")
    else:
        db_path = os.path.join(app.instance_path, 'local_dev.db')
        os.makedirs(app.instance_path, exist_ok=True)
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        print("INFO: Connecting to local SQLite database")

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # --- CẤU HÌNH CACHING ĐỘNG ---
    if redis_url := os.getenv('REDIS_URL'):
        app.config['CACHE_TYPE'] = 'RedisCache'
        app.config['CACHE_REDIS_URL'] = redis_url
        print("INFO: Connecting to Redis for caching.")
    else:
        app.config['CACHE_TYPE'] = 'SimpleCache'
        print("INFO: Using in-memory SimpleCache. For production, set REDIS_URL.")
