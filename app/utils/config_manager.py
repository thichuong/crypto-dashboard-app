"""
Advanced Configuration Management với Environment-specific settings
"""
import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class CacheConfig:
    """Cache configuration"""
    redis_url: Optional[str] = None
    default_timeout: int = 300
    max_timeout: int = 3600
    memory_backup_enabled: bool = True
    file_backup_enabled: bool = True
    backup_max_age_hours: int = 24
    
    # Redis specific
    redis_socket_timeout: int = 5
    redis_socket_connect_timeout: int = 5
    redis_retry_on_timeout: bool = True
    redis_health_check_interval: int = 30

@dataclass
class APIConfig:
    """API configuration"""
    coingecko_requests_per_minute: int = 50
    taapi_requests_per_minute: int = 1
    alternative_me_requests_per_minute: int = 30
    
    # Timeout configurations
    default_timeout: float = 10.0
    parallel_timeout: float = 15.0
    critical_api_timeout: float = 20.0
    
    # Circuit breaker
    circuit_failure_threshold: int = 3
    circuit_timeout: int = 60
    
    # Retry configuration
    max_retries: int = 3
    retry_backoff_multiplier: float = 1.5

@dataclass
class DatabaseConfig:
    """Database configuration"""
    connection_timeout: int = 30
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 300
    pool_pre_ping: bool = True
    
    # SSL configuration
    ssl_mode: str = "require"
    ssl_root_cert: str = "DISABLE"

@dataclass
class PerformanceConfig:
    """Performance optimization configuration"""
    # Threading
    max_workers: int = 4
    
    # Caching strategy
    aggressive_caching: bool = False
    cache_warming_enabled: bool = True
    
    # Response optimization
    compress_responses: bool = True
    enable_etag: bool = True
    
    # Background tasks
    cleanup_interval: int = 3600  # 1 hour
    health_check_interval: int = 300  # 5 minutes

@dataclass
class AppConfig:
    """Complete application configuration"""
    environment: Environment
    debug: bool
    secret_key: str
    
    # Service configurations
    cache: CacheConfig
    api: APIConfig
    database: DatabaseConfig
    performance: PerformanceConfig
    
    # API Keys
    gemini_api_key: Optional[str] = None
    taapi_secret: Optional[str] = None
    coingecko_api_key: Optional[str] = None

class ConfigManager:
    """Advanced configuration manager"""
    
    def __init__(self):
        self._config: Optional[AppConfig] = None
        self._load_config()
    
    def _detect_environment(self) -> Environment:
        """Detect current environment"""
        env = os.getenv('FLASK_ENV', 'development').lower()
        
        if env == 'production':
            return Environment.PRODUCTION
        elif env == 'staging':
            return Environment.STAGING
        else:
            return Environment.DEVELOPMENT
    
    def _get_cache_config(self, env: Environment) -> CacheConfig:
        """Get cache configuration based on environment"""
        redis_url = os.getenv('REDIS_URL')
        
        if env == Environment.PRODUCTION:
            return CacheConfig(
                redis_url=redis_url,
                default_timeout=600,  # 10 minutes for production
                max_timeout=7200,     # 2 hours max
                memory_backup_enabled=True,
                file_backup_enabled=False,  # No file backup in production
                backup_max_age_hours=48,
                redis_socket_timeout=10,
                redis_health_check_interval=60
            )
        elif env == Environment.STAGING:
            return CacheConfig(
                redis_url=redis_url,
                default_timeout=300,  # 5 minutes for staging
                max_timeout=3600,
                memory_backup_enabled=True,
                file_backup_enabled=True,
                backup_max_age_hours=24
            )
        else:  # Development
            return CacheConfig(
                redis_url=redis_url,
                default_timeout=120,  # 2 minutes for development
                max_timeout=1800,
                memory_backup_enabled=True,
                file_backup_enabled=True,
                backup_max_age_hours=6
            )
    
    def _get_api_config(self, env: Environment) -> APIConfig:
        """Get API configuration based on environment"""
        if env == Environment.PRODUCTION:
            return APIConfig(
                coingecko_requests_per_minute=45,  # Conservative for production
                taapi_requests_per_minute=1,
                alternative_me_requests_per_minute=25,
                default_timeout=15.0,
                parallel_timeout=20.0,
                critical_api_timeout=30.0,
                circuit_failure_threshold=2,  # More sensitive in production
                circuit_timeout=120,
                max_retries=5
            )
        elif env == Environment.STAGING:
            return APIConfig(
                coingecko_requests_per_minute=30,
                taapi_requests_per_minute=1,
                alternative_me_requests_per_minute=20,
                default_timeout=12.0,
                parallel_timeout=18.0,
                critical_api_timeout=25.0,
                circuit_failure_threshold=3,
                circuit_timeout=90
            )
        else:  # Development
            return APIConfig(
                coingecko_requests_per_minute=60,  # More lenient for development
                taapi_requests_per_minute=2,
                alternative_me_requests_per_minute=40,
                default_timeout=8.0,
                parallel_timeout=12.0,
                critical_api_timeout=20.0,
                circuit_failure_threshold=5,
                circuit_timeout=60
            )
    
    def _get_database_config(self, env: Environment) -> DatabaseConfig:
        """Get database configuration based on environment"""
        if env == Environment.PRODUCTION:
            return DatabaseConfig(
                connection_timeout=45,
                pool_size=10,
                max_overflow=20,
                pool_timeout=45,
                pool_recycle=300,
                pool_pre_ping=True
            )
        elif env == Environment.STAGING:
            return DatabaseConfig(
                connection_timeout=30,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=300,
                pool_pre_ping=True
            )
        else:  # Development
            return DatabaseConfig(
                connection_timeout=20,
                pool_size=3,
                max_overflow=5,
                pool_timeout=20,
                pool_recycle=600,
                pool_pre_ping=False  # Not needed for SQLite
            )
    
    def _get_performance_config(self, env: Environment) -> PerformanceConfig:
        """Get performance configuration based on environment"""
        if env == Environment.PRODUCTION:
            return PerformanceConfig(
                max_workers=6,
                aggressive_caching=True,
                cache_warming_enabled=True,
                compress_responses=True,
                enable_etag=True,
                cleanup_interval=1800,  # 30 minutes
                health_check_interval=180   # 3 minutes
            )
        elif env == Environment.STAGING:
            return PerformanceConfig(
                max_workers=4,
                aggressive_caching=False,
                cache_warming_enabled=True,
                compress_responses=True,
                enable_etag=True,
                cleanup_interval=3600,  # 1 hour
                health_check_interval=300   # 5 minutes
            )
        else:  # Development
            return PerformanceConfig(
                max_workers=2,
                aggressive_caching=False,
                cache_warming_enabled=False,
                compress_responses=False,
                enable_etag=False,
                cleanup_interval=7200,  # 2 hours
                health_check_interval=600   # 10 minutes
            )
    
    def _load_config(self):
        """Load complete configuration"""
        env = self._detect_environment()
        
        # Load from environment variables
        secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
        
        self._config = AppConfig(
            environment=env,
            debug=(env != Environment.PRODUCTION),
            secret_key=secret_key,
            cache=self._get_cache_config(env),
            api=self._get_api_config(env),
            database=self._get_database_config(env),
            performance=self._get_performance_config(env),
            
            # API Keys
            gemini_api_key=os.getenv('GEMINI_API_KEY'),
            taapi_secret=os.getenv('TAAPI_SECRET'),
            coingecko_api_key=os.getenv('COINGECKO_API_KEY')
        )
    
    @property
    def config(self) -> AppConfig:
        """Get current configuration"""
        if self._config is None:
            self._load_config()
        return self._config
    
    def reload(self):
        """Reload configuration from environment"""
        self._load_config()
    
    def get_flask_config(self) -> Dict[str, Any]:
        """Get Flask-compatible configuration dictionary"""
        config = self.config
        
        flask_config = {
            'SECRET_KEY': config.secret_key,
            'DEBUG': config.debug,
            
            # Database
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            
            # Cache
            'CACHE_DEFAULT_TIMEOUT': config.cache.default_timeout,
        }
        
        # Database URL
        if postgres_url := os.getenv('POSTGRES_URL'):
            db_url = postgres_url.replace("postgres://", "postgresql://", 1)
            
            # Add SSL parameters for Railway PostgreSQL
            if "?" not in db_url:
                db_url += f"?sslmode={config.database.ssl_mode}&sslrootcert={config.database.ssl_root_cert}"
            elif "sslmode" not in db_url:
                db_url += f"&sslmode={config.database.ssl_mode}&sslrootcert={config.database.ssl_root_cert}"
            
            flask_config['SQLALCHEMY_DATABASE_URI'] = db_url
            
            # Database engine options
            flask_config['SQLALCHEMY_ENGINE_OPTIONS'] = {
                'pool_pre_ping': config.database.pool_pre_ping,
                'pool_recycle': config.database.pool_recycle,
                'pool_timeout': config.database.pool_timeout,
                'max_overflow': config.database.max_overflow,
                'echo': config.debug,
                'connect_args': {
                    "sslmode": config.database.ssl_mode,
                    "connect_timeout": config.database.connection_timeout,
                    "application_name": "crypto_dashboard_app"
                }
            }
        else:
            # SQLite for development
            flask_config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/local_dev.db'
        
        # Cache configuration
        if config.cache.redis_url:
            flask_config.update({
                'CACHE_TYPE': 'RedisCache',
                'CACHE_REDIS_URL': config.cache.redis_url,
                'CACHE_OPTIONS': {
                    'socket_timeout': config.cache.redis_socket_timeout,
                    'socket_connect_timeout': config.cache.redis_socket_connect_timeout,
                    'retry_on_timeout': config.cache.redis_retry_on_timeout,
                    'health_check_interval': config.cache.redis_health_check_interval
                }
            })
        else:
            flask_config['CACHE_TYPE'] = 'SimpleCache'
        
        return flask_config
    
    def export_config(self) -> str:
        """Export configuration as JSON for debugging"""
        config_dict = asdict(self.config)
        # Convert enum to string
        config_dict['environment'] = config_dict['environment'].value
        return json.dumps(config_dict, indent=2, ensure_ascii=False)

# Global configuration manager
config_manager = ConfigManager()

# Convenience functions
def get_config() -> AppConfig:
    return config_manager.config

def get_flask_config() -> Dict[str, Any]:
    return config_manager.get_flask_config()

def is_production() -> bool:
    return config_manager.config.environment == Environment.PRODUCTION

def is_development() -> bool:
    return config_manager.config.environment == Environment.DEVELOPMENT
