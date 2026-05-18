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
    DATABASE_URL: str = "postgresql://user:pass@localhost:5432/mydb"

    # Logging
    LOG_LEVEL: str = "INFO"
    SYSLOG_HOST: str = "localhost"
    SYSLOG_PORT: int = 514

    # JWT
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()