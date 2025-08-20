from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str | None = None
    env: str = "development"

    class Config:
        env_file = ".env"
        env_prefix = ""
        case_sensitive = False

settings = Settings()
