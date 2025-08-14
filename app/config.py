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

    # --- CẤU HÌNH DATABASE ---
    # Prefer POSTGRES_URL for local development, then DATABASE_URL for hosting platforms
    db_env = os.getenv('POSTGRES_URL') or os.getenv('DATABASE_URL')
    if db_env:
        # Normalize scheme for SQLAlchemy (older URLs may use postgres://)
        db_url = db_env.replace("postgres://", "postgresql://", 1)
        
        # Determine if this is local development or production
        is_local_postgres = 'localhost' in db_url or '127.0.0.1' in db_url
        
        # Configure SSL based on environment
        if is_local_postgres:
            # Local PostgreSQL typically doesn't require SSL
            if "?" not in db_url:
                db_url += "?sslmode=disable"
            elif "sslmode" not in db_url:
                db_url += "&sslmode=disable"
        else:
            # Production/hosted PostgreSQL requires SSL
            if "?" not in db_url:
                db_url += "?sslmode=require"
            elif "sslmode" not in db_url:
                db_url += "&sslmode=require"
        
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
        
        # Connection pooling and engine options
        connect_args = {
            "connect_timeout": 60 if not is_local_postgres else 10,
            "application_name": "crypto_dashboard_app"
        }
        
        # Add SSL mode to connect_args
        if is_local_postgres:
            connect_args["sslmode"] = "disable"
        else:
            connect_args["sslmode"] = "require"
        
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'pool_timeout': 30,
            'max_overflow': 10,
            'echo': False,
            'connect_args': connect_args
        }
        
        source = 'POSTGRES_URL' if os.getenv('POSTGRES_URL') else 'DATABASE_URL'
        print(f"INFO: Connecting to Postgres database from env var: {source}")
        
        # Debug info for Railway (only show host, not full URL for security)
        try:
            import urllib.parse
            parsed = urllib.parse.urlparse(db_url)
            print(f"INFO: Database host: {parsed.hostname}")
        except:
            pass
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
