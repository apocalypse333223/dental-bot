"""
Хендлеры администратора.

Доступ ко всем командам/колбэкам здесь ограничен списком
ADMIN_TELEGRAM_IDS из .env — обычный пациент их не увидит и не
сможет вызвать (проверка is_admin в каждом хендлере через фильтр).
"""

import html
import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import (
    STATUS_LABELS,
    request_actions_keyboard,
    requests_list_keyboard,
)
from app.bot.states import AdminStates
from app.config import settings
from app.db.database import async_session_factory
from app.db.repository import (
    get_request_by_id,
    list_requests_by_status,
    set_request_reply,
    update_request_status,
)

logger = logging.getLogger(__name__)

router = Router(name="admin")


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids_list


# Все хендлеры этого роутера дополнительно защищены фильтром is_admin,
# чтобы обычные пациенты не могли вызвать админ-команды.
router.message.filter(lambda message: message.from_user is not None and is_admin(message.from_user.id))
router.callback_query.filter(lambda cq: cq.from_user is not None and is_admin(cq.from_user.id))


def _format_request_card(request) -> str:  # noqa: ANN001 - Request с подгруженным patient
    patient = request.patient
    username_part = f"@{html.escape(patient.username)}" if patient.username else "нет username"
    return (
        f"<b>Заявка #{request.id}</b>\n"
        f"Статус: {STATUS_LABELS.get(request.status, request.status)}\n"
        f"Пациент: {html.escape(patient.first_name)} ({username_part})\n"
        f"Категория: <b>{request.category}</b>\n"
        f"Требует внимания: {'да ⚠️' if request.needs_human else 'нет'}\n\n"
        f"<b>Суть:</b> {html.escape(request.summary or '—')}\n\n"
        f"<b>Исходное сообщение:</b>\n{html.escape(request.raw_message)}"
        + (f"\n\n<b>Ответ администратора:</b>\n{request.admin_reply}" if request.admin_reply else "")
    )


@router.message(Command("requests"))
async def cmd_requests(message: Message) -> None:
    """Показывает список новых заявок (статус 'new')."""
    async with async_session_factory() as session:
        requests = await list_requests_by_status(session, status="new")

    if not requests:
        await message.answer("Новых заявок нет 👍")
        return

    await message.answer(
        f"Новых заявок: {len(requests)}",
        reply_markup=requests_list_keyboard([r.id for r in requests]),
    )


@router.callback_query(F.data.startswith("view:"))
async def cb_view_request(callback: CallbackQuery) -> None:
    """Показывает детальную карточку заявки по кнопке из списка."""
    request_id = int(callback.data.split(":")[1])

    async with async_session_factory() as session:
        request = await get_request_by_id(session, request_id)

    if request is None:
        await callback.answer("Заявка не найдена (возможно, устарела)", show_alert=True)
        return

    await callback.message.answer(
        _format_request_card(request),
        reply_markup=request_actions_keyboard(request.id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_status:"))
async def cb_set_status(callback: CallbackQuery) -> None:
    """Меняет статус заявки по нажатию кнопки."""
    _, request_id_str, new_status = callback.data.split(":")
    request_id = int(request_id_str)

    async with async_session_factory() as session:
        request = await update_request_status(session, request_id, new_status)

    if request is None:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    await callback.answer(f"Статус изменён: {STATUS_LABELS.get(new_status, new_status)}")
    try:
        await callback.message.edit_text(
            _format_request_card(request),
            reply_markup=request_actions_keyboard(request.id),
        )
    except Exception:
        # Сообщение могло не измениться (например, статус тот же) — не критично.
        logger.debug("Не удалось обновить текст карточки заявки #%s", request.id)


@router.callback_query(F.data.startswith("reply:"))
async def cb_start_reply(callback: CallbackQuery, state: FSMContext) -> None:
    """Запускает FSM-сценарий: следующее сообщение админа уйдёт пациенту."""
    request_id = int(callback.data.split(":")[1])

    async with async_session_factory() as session:
        request = await get_request_by_id(session, request_id)

    if request is None:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_for_reply)
    await state.update_data(
        request_id=request.id,
        patient_telegram_id=request.patient.telegram_id,
    )

    await callback.message.answer(
        f"Напишите ответ для заявки #{request.id}. "
        f"Он будет отправлен пациенту от имени клиники.\n\n"
        f"Для отмены отправьте /cancel"
    )
    await callback.answer()


@router.message(Command("cancel"), AdminStates.waiting_for_reply)
async def cmd_cancel_reply(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Отменено.")


@router.message(AdminStates.waiting_for_reply)
async def process_admin_reply(message: Message, state: FSMContext, bot: Bot) -> None:
    """Получает текст ответа от админа и пересылает его пациенту."""
    if message.text is None:
        await message.answer("Пожалуйста, отправьте текстовое сообщение.")
        return

    data = await state.get_data()
    request_id = data["request_id"]
    patient_telegram_id = data["patient_telegram_id"]

    try:
        await bot.send_message(
            chat_id=patient_telegram_id,
            text=f"Ответ от клиники:\n\n{html.escape(message.text)}",
        )
    except Exception:
        logger.exception(
            "Не удалось отправить ответ пациенту telegram_id=%s (заявка #%s)",
            patient_telegram_id,
            request_id,
        )
        await message.answer(
            "Не удалось отправить сообщение пациенту (возможно, он заблокировал бота)."
        )
        await state.clear()
        return

    async with async_session_factory() as session:
        await set_request_reply(session, request_id, message.text)

    await state.clear()
    await message.answer(f"Ответ отправлен пациенту. Заявка #{request_id} переведена в статус 'answered'.")
