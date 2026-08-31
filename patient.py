"""
Хендлеры для сообщений от пациентов.

Полный цикл (с Этапа 4):
1. Сохранить/найти пациента в БД.
2. Классифицировать сообщение через AI и сохранить как заявку.
3. Если needs_human=true — уведомить администраторов.
4. Ответить пациенту подтверждением.
"""

import logging

from aiogram import Bot, Router
from aiogram.types import Message

from app.config import settings
from app.db.database import async_session_factory
from app.db.repository import get_or_create_patient
from app.services.notification import notify_admins_about_request
from app.services.request_service import process_patient_message

logger = logging.getLogger(__name__)

router = Router(name="patient")


@router.message()
async def handle_patient_message(message: Message, bot: Bot) -> None:
    """Срабатывает на любое текстовое сообщение от пациента."""
    if message.from_user is None or message.text is None:
        # Игнорируем сообщения без текста (стикеры, фото и т.п.) на этом этапе MVP
        return

    # Администраторские сообщения никогда не должны попадать в patient-flow.
    if message.from_user.id in settings.admin_ids_list:
        return

    if len(message.text) > 4000:
        await message.answer("Сообщение слишком длинное. Пожалуйста, сократите его до 4000 символов.")
        return

    try:
        async with async_session_factory() as session:
            patient = await get_or_create_patient(
                session=session,
                telegram_id=message.from_user.id,
                first_name=message.from_user.first_name or "Без имени",
                username=message.from_user.username,
            )

            request = await process_patient_message(
                session=session,
                patient=patient,
                raw_message=message.text,
            )
    except Exception:
        logger.exception("Ошибка при обработке сообщения пациента")
        await message.answer(
            "Извините, произошла техническая ошибка. Мы уже разбираемся, "
            "попробуйте написать чуть позже."
        )
        return

    if request.needs_human:
        try:
            await notify_admins_about_request(bot, request, patient)
        except Exception:
            # Заявка уже сохранена в БД — сбой уведомления не должен
            # приводить к ошибке для пациента, админ всё равно увидит
            # заявку через /requests.
            logger.exception("Не удалось уведомить админов о заявке #%s", request.id)

    await message.answer(
        f"Спасибо, {patient.first_name}! Ваше сообщение принято "
        f"(заявка #{request.id}).\n\nМы скоро свяжемся с вами."
    )
