from typing import List

from pydantic_settings import BaseSettings


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
    DATABASE_URL: str = "mysql+aiomysql://user:pass@localhost:3306/mydb"

    # Logging
    LOG_LEVEL: str = "INFO"
    SYSLOG_HOST: str = "localhost"
    SYSLOG_PORT: int = 514

    # JWT
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Seed (only used by seed.py — not used at runtime)
    SEED_ADMIN_EMAIL: str = "admin@example.com"
    SEED_ADMIN_USERNAME: str = "admin"
    SEED_ADMIN_FULLNAME: str = "System Administrator"
    SEED_ADMIN_PASSWORD: str = "Admin1234"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()