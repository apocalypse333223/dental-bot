"""
Repository-слой: единственное место в проекте, где выполняются
прямые запросы к базе данных (SELECT/INSERT/UPDATE).

Хендлеры бота и будущие API-эндпоинты не должны писать SQL/ORM-запросы
напрямую — они вызывают функции отсюда. Это упрощает тестирование
и позволяет позже поменять БД без изменения остального кода.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Patient, Request


async def get_or_create_patient(
    session: AsyncSession,
    telegram_id: int,
    first_name: str,
    username: str | None,
) -> Patient:
    """
    Находит пациента по telegram_id. Если его ещё нет в базе — создаёт.

    Возвращает объект Patient в любом случае.
    """
    result = await session.execute(
        select(Patient).where(Patient.telegram_id == telegram_id)
    )
    patient = result.scalar_one_or_none()

    if patient is not None:
        return patient

    patient = Patient(
        telegram_id=telegram_id,
        first_name=first_name,
        username=username,
    )
    session.add(patient)
    await session.commit()
    await session.refresh(patient)
    return patient


async def create_request(
    session: AsyncSession,
    patient_id: int,
    raw_message: str,
    category: str,
    summary: str | None,
    needs_human: bool,
) -> Request:
    """Создаёт новую заявку (обработанное AI сообщение пациента)."""
    request = Request(
        patient_id=patient_id,
        raw_message=raw_message,
        category=category,
        summary=summary,
        needs_human=needs_human,
        status="new",
    )
    session.add(request)
    await session.commit()
    await session.refresh(request)
    return request


async def get_request_by_id(session: AsyncSession, request_id: int) -> Request | None:
    """Возвращает заявку вместе с данными пациента (для админ-панели)."""
    result = await session.execute(
        select(Request)
        .options(selectinload(Request.patient))
        .where(Request.id == request_id)
    )
    return result.scalar_one_or_none()


async def list_requests_by_status(
    session: AsyncSession, status: str, limit: int = 20
) -> list[Request]:
    """Возвращает последние заявки с заданным статусом (для команды /requests)."""
    result = await session.execute(
        select(Request)
        .options(selectinload(Request.patient))
        .where(Request.status == status)
        .order_by(Request.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def update_request_status(
    session: AsyncSession, request_id: int, status: str
) -> Request | None:
    """Меняет статус заявки. Возвращает обновлённую заявку или None, если не найдена."""
    request = await get_request_by_id(session, request_id)
    if request is None:
        return None
    request.status = status
    await session.commit()
    await session.refresh(request)
    return request


async def set_request_reply(
    session: AsyncSession, request_id: int, reply_text: str
) -> Request | None:
    """Сохраняет текст ответа администратора и переводит заявку в статус 'answered'."""
    request = await get_request_by_id(session, request_id)
    if request is None:
        return None
    request.admin_reply = reply_text
    request.status = "answered"
    await session.commit()
    await session.refresh(request)
    return request
