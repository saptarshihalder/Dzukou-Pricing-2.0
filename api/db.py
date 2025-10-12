from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .settings import get_settings


class Base(DeclarativeBase):
    pass


_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def _create_engine(url: str) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(url, echo=False, future=True)
    Session = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    return engine, Session


def get_engine() -> AsyncEngine:
    global _engine, _sessionmaker
    if _engine is None:
        settings = get_settings()
        # Try primary DB first
        _engine, _sessionmaker = _create_engine(settings.DATABASE_URL)
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        get_engine()
    assert _sessionmaker is not None
    return _sessionmaker


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    Session = get_sessionmaker()
    async with Session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db(models_module) -> None:
    """Create tables if they do not exist."""
    settings = get_settings()
    global _engine, _sessionmaker
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(models_module.Base.metadata.create_all)
    except Exception:
        # Fallback to SQLite
        _engine, _sessionmaker = _create_engine(settings.SQLITE_URL)
        async with _engine.begin() as conn:
            await conn.run_sync(models_module.Base.metadata.create_all)


async def shutdown_db() -> None:
    engine = get_engine()
    await engine.dispose()
