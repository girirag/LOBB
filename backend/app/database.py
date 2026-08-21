from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from app.config import get_settings


class Base(DeclarativeBase):
    pass


_engine: Optional[AsyncEngine] = None
_sessionmaker: Optional[async_sessionmaker[AsyncSession]] = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        engine_kwargs = {
            "echo": settings.DEBUG and settings.APP_ENV != "production",
            "future": True,
        }
        if settings.is_serverless:
            engine_kwargs["poolclass"] = NullPool
        _engine = create_async_engine(settings.async_database_url, **engine_kwargs)
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        eng = get_engine()
        _sessionmaker = async_sessionmaker(
            bind=eng,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _sessionmaker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions."""
    sm = get_sessionmaker()
    async with sm() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    try:
        eng = get_engine()
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        import logging
        logging.warning(f"Failed to init DB: {e}")
