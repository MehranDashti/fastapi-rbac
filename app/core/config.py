from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Server
    SERVER_LISTEN_IP: str = "0.0.0.0"
    SERVER_LISTEN_PORT: int = 8000
    SERVER_WORKERS: int = 1
    PRODUCTION: bool = False

    # App
    APP_NAME: str = "MyApp"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # DB
    DATABASE_URL: str = "sqlite:///./dev.db"

    # Logging
    LOG_LEVEL: str = "INFO"
    SYSLOG_HOST: str = "localhost"
    SYSLOG_PORT: int = 514

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()