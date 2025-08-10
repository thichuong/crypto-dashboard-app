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
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
        print("INFO: Connecting to Postgres database")
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
