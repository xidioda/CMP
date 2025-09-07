from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str | None = None
    env: str = "development"
    
    # JWT Authentication Configuration
    jwt_secret_key: str | None = None
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # Zoho Books API Configuration
    zoho_client_id: str | None = None
    zoho_client_secret: str | None = None
    zoho_access_token: str | None = None
    zoho_refresh_token: str | None = None
    zoho_organization_id: str | None = None
    zoho_base_url: str = "https://www.zohoapis.com/books/v3"  # Default to US data center
    
    # Emirates NBD API Souq Configuration (Real UAE Bank API)
    emirates_nbd_api_key: str | None = None
    emirates_nbd_client_id: str | None = None
    emirates_nbd_base_url: str = "https://api.emiratesnbd.com/v1"  # API Souq platform
    emirates_nbd_account_number: str | None = None
    
    # Bank file import configuration (for banks without APIs)
    bank_import_directory: str = "local_storage/bank_statements"
    
    # Legacy Wio Bank - now using file import method
    wio_account_number: str | None = None  # For file naming and identification
    
    # API Rate Limiting
    api_rate_limit: int = 100  # requests per minute
    api_timeout: int = 30  # seconds

    class Config:
        env_file = ".env"
        env_prefix = ""
        case_sensitive = False

settings = Settings()
