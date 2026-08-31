"""
Бизнес-логика заявок: связывает AI-классификацию и сохранение в БД.

Это единственное место, которое вызывают и хендлеры бота, и (в будущем)
API-эндпоинты — чтобы логика создания заявки не дублировалась.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.classifier import classify_message
from app.db.models import Patient, Request
from app.db.repository import create_request

logger = logging.getLogger(__name__)


async def process_patient_message(
    session: AsyncSession,
    patient: Patient,
    raw_message: str,
) -> Request:
    """
    Полный цикл обработки сообщения пациента:
    1. Классифицировать через AI.
    2. Сохранить как заявку в БД.

    Возвращает созданную заявку (с уже проставленными category/summary/needs_human).
    """
    classification = await classify_message(raw_message)

    request = await create_request(
        session=session,
        patient_id=patient.id,
        raw_message=raw_message,
        category=classification.category.value,
        summary=classification.summary,
        # Для медицинского бота на MVP каждый запрос дополнительно проверяет человек.
        # Это защищает от ситуации, когда LLM ошибочно решит, что оператор не нужен.
        needs_human=True,
    )

    logger.info(
        "Создана заявка id=%s, категория=%s, needs_human=%s",
        request.id,
        request.category,
        request.needs_human,
    )
    return request
