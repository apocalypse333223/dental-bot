"""
Уведомления администраторов.

Сервис не привязан к конкретному хендлеру — принимает готовый объект
Bot и данные заявки, поэтому его можно вызвать откуда угодно
(из хендлера бота, из будущего API-эндпоинта, из фоновой задачи).
"""

import html
import logging

from aiogram import Bot

from app.bot.keyboards import request_actions_keyboard
from app.config import settings
from app.db.models import Patient, Request

logger = logging.getLogger(__name__)


def _format_request_card(request: Request, patient: Patient) -> str:
    username_part = f"@{html.escape(patient.username)}" if patient.username else "нет username"
    return (
        f"<b>Заявка #{request.id}</b>\n"
        f"Пациент: {html.escape(patient.first_name)} ({username_part})\n"
        f"Категория: <b>{request.category}</b>\n"
        f"Требует внимания: {'да ⚠️' if request.needs_human else 'нет'}\n\n"
        f"<b>Суть:</b> {html.escape(request.summary or '—')}\n\n"
        f"<b>Исходное сообщение:</b>\n{html.escape(request.raw_message)}"
    )


async def notify_admins_about_request(
    bot: Bot, request: Request, patient: Patient
) -> None:
    """
    Рассылает карточку заявки всем администраторам из settings.admin_ids_list.

    Не бросает исключение наружу при сбое отправки одному из админов —
    логирует и пытается отправить остальным (один заблокировавший бота
    админ не должен ронять уведомление для всех).
    """
    admin_ids = settings.admin_ids_list
    if not admin_ids:
        logger.warning(
            "ADMIN_TELEGRAM_IDS не настроен в .env — некому отправлять уведомление о заявке #%s",
            request.id,
        )
        return

    text = _format_request_card(request, patient)
    keyboard = request_actions_keyboard(request.id)

    for admin_id in admin_ids:
        try:
            await bot.send_message(chat_id=admin_id, text=text, reply_markup=keyboard)
        except Exception:
            logger.exception("Не удалось отправить уведомление админу id=%s", admin_id)
