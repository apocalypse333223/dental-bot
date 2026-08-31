"""
Инлайн-клавиатуры для админ-интерфейса.

callback_data формата "действие:request_id[:значение]" — короткий
и легко парсится в хендлере колбэков.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

STATUSES = ["new", "in_progress", "answered", "closed"]

STATUS_LABELS = {
    "new": "🆕 Новая",
    "in_progress": "⏳ В работе",
    "answered": "✅ Отвечено",
    "closed": "🔒 Закрыта",
}


def request_actions_keyboard(request_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для карточки одной заявки: ответить + сменить статус."""
    status_buttons = [
        InlineKeyboardButton(
            text=STATUS_LABELS[status],
            callback_data=f"set_status:{request_id}:{status}",
        )
        for status in STATUSES
    ]

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✍️ Ответить пациенту", callback_data=f"reply:{request_id}")],
            status_buttons[:2],
            status_buttons[2:],
        ]
    )


def requests_list_keyboard(request_ids: list[int]) -> InlineKeyboardMarkup:
    """Клавиатура-список для команды /requests — каждая заявка отдельной кнопкой."""
    buttons = [
        [InlineKeyboardButton(text=f"Заявка #{rid}", callback_data=f"view:{rid}")]
        for rid in request_ids
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
