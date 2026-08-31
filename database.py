"""
Подключение к базе данных.

Используем async SQLAlchemy, потому что aiogram работает асинхронно —
если делать синхронные запросы к БД, они будут блокировать event loop бота.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings
from app.db.models import Base

engine = create_async_engine(settings.database_url, echo=False)

async_session_factory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Создаёт все таблицы, если их ещё нет. Вызывается один раз при старте."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Генератор сессии БД. Используется как контекстный менеджер:

        async with async_session_factory() as session:
            ...

    Позже, при добавлении FastAPI, эта же функция подойдёт как Depends().
    """
    async with async_session_factory() as session:
        yield session
