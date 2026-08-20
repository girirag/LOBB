import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "URL Shortener API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    BASE_URL: str = ""

    # Database URL
    DATABASE_URL: str = "sqlite+aiosqlite:///./urlshortener.db"

    # Short code configuration
    SHORT_CODE_LENGTH: int = 6

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def is_vercel(self) -> bool:
        return bool(os.getenv("VERCEL") or os.getenv("VERCEL_ENV") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))

    @property
    def async_database_url(self) -> str:
        url = self.DATABASE_URL
        
        # If running on Vercel and no Postgres DATABASE_URL provided (or local SQLite path), use /tmp directory
        if self.is_vercel and (url.startswith("sqlite") or "localhost" in url):
            if "localhost" in url:
                # If pointing to localhost on Vercel without a real remote DB, fallback to /tmp sqlite
                return "sqlite+aiosqlite:////tmp/urlshortener.db"
            return "sqlite+aiosqlite:////tmp/urlshortener.db"

        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("sqlite://") and not url.startswith("sqlite+aiosqlite://"):
            url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)

        # Handle asyncpg sslmode parameter if from Neon/Supabase
        if "postgresql+asyncpg://" in url and "sslmode=" in url:
            url = url.replace("sslmode=", "ssl=")
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()

