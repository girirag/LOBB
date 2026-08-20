from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "URL Shortener API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    BASE_URL: str = "http://localhost:8000"

    # Database URL
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/urlshortener"

    # Short code configuration
    SHORT_CODE_LENGTH: int = 6

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def async_database_url(self) -> str:
        url = self.DATABASE_URL
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
