"""
Точка входа Telegram-бота.

Здесь и только здесь создаётся объект Bot и Dispatcher —
остальной код про то, "что бот умеет", живёт в handlers/.

Порядок подключения роутеров важен: admin_router подключается
ПЕРВЫМ, потому что patient_router содержит catch-all хендлер
(@router.message() без фильтров), который иначе перехватил бы
все сообщения раньше, чем они дойдут до админ-хендлеров.
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ErrorEvent

from app.bot.handlers.admin import router as admin_router
from app.bot.handlers.patient import router as patient_router
from app.config import settings
from app.db.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("Инициализация базы данных...")
    await init_db()

    if not settings.admin_ids_list:
        logger.warning(
            "ADMIN_TELEGRAM_IDS не заполнен в .env — админ-функции и "
            "уведомления о заявках работать не будут."
        )

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(admin_router)
    dp.include_router(patient_router)

    @dp.errors()
    async def global_error_handler(event: ErrorEvent) -> bool:
        """
        Ловит любые необработанные исключения в хендлерах, чтобы бот
        не падал целиком из-за одной ошибки в одном апдейте.
        """
        logger.exception(
            "Необработанная ошибка при обработке апдейта: %s", event.exception
        )
        return True

    logger.info("Бот запускается...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
