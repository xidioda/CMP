from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Application Configuration
    debug: bool = False
    environment: str = "development"
    secret_key: Optional[str] = None
    allowed_hosts: str = "localhost,127.0.0.1"
    
    # Database Configuration
    database_url: Optional[str] = None
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "cmp"
    db_user: str = "cmp"
    db_password: Optional[str] = None
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # JWT Authentication Configuration
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # Zoho Books API Configuration
    zoho_client_id: Optional[str] = None
    zoho_client_secret: Optional[str] = None
    zoho_redirect_uri: str = "http://localhost:8000/settings/integrations/zoho/callback"
    zoho_access_token: Optional[str] = None
    zoho_refresh_token: Optional[str] = None
    zoho_organization_id: Optional[str] = None
    zoho_accounts_url: str = "https://accounts.zoho.com"
    zoho_books_url: str = "https://www.zohoapis.com/books/v3"
    zoho_base_url: str = "https://www.zohoapis.com/books/v3"  # Backward compatibility
    
    # Bank API Configuration
    emirates_nbd_api_key: Optional[str] = None
    emirates_nbd_client_id: Optional[str] = None
    emirates_nbd_account_number: Optional[str] = None
    emirates_nbd_base_url: str = "https://api.emiratesnbd.com/v1"
    
    # WIO Bank Configuration (File Import)
    wio_account_number: Optional[str] = None
    wio_account_name: Optional[str] = None
    
    # GitHub Integration Configuration
    github_token: Optional[str] = None
    github_owner: str = "xidioda"
    github_repo: str = "CMP"
    github_project_management: bool = True
    bank_import_directory: str = "local_storage/bank_statements"
    
    # File Storage Configuration
    upload_dir: str = "local_storage"
    max_file_size: int = 10485760  # 10MB
    allowed_extensions: str = ".csv,.xlsx,.pdf,.png,.jpg,.jpeg"
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "logs/cmp.log"
    log_max_size: int = 10485760  # 10MB
    log_backup_count: int = 5
    
    # Email Configuration
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None
    smtp_use_tls: bool = True
    
    # AI/ML Configuration
    openai_api_key: Optional[str] = None
    ml_model_storage_path: str = "local_storage/ml_models"
    
    # Security Configuration
    cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000"
    csrf_secret: Optional[str] = None
    session_cookie_secure: bool = False
    session_cookie_httponly: bool = True
    session_cookie_samesite: str = "lax"
    
    # API Rate Limiting
    api_rate_limit: int = 100  # requests per minute
    api_timeout: int = 30  # seconds
    
    # Monitoring Configuration
    prometheus_enabled: bool = False
    grafana_enabled: bool = False
    health_check_interval: int = 30
    
    # Docker Configuration
    compose_project_name: str = "cmp"
    postgres_password: Optional[str] = None
    redis_password: Optional[str] = None
    
    # Backup Configuration
    backup_enabled: bool = False
    backup_schedule: str = "0 2 * * *"
    backup_retention_days: int = 30
    backup_s3_bucket: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    
    # SSL/TLS Configuration
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None
    ssl_redirect: bool = False
    
    # Rate Limiting Configuration
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600
    
    # Cache Configuration
    cache_ttl: int = 3600
    cache_max_size: int = 1000
    
    # Worker Configuration
    worker_processes: int = 2
    worker_connections: int = 1000
    worker_timeout: int = 30
    worker_keepalive: int = 2

    class Config:
        env_file = ".env"
        env_prefix = ""
        case_sensitive = False
        # Allow extra fields for forward compatibility
        extra = "ignore"
        # Fix Pydantic warnings
        protected_namespaces = ('settings_',)

settings = Settings()
