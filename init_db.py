"""
Скрипт для создания таблиц в базе данных.

Запуск: python init_db.py

Это же будет нашим тестом для Этапа 1: если скрипт отрабатывает
без ошибок и создаёт файл dental_bot.db с нужными таблицами — значит,
конфиг и модели настроены правильно.
"""

import asyncio

from app.db.database import init_db


async def main() -> None:
    print("Создаю таблицы...")
    await init_db()
    print("Готово. Таблицы patients и requests созданы.")


if __name__ == "__main__":
    asyncio.run(main())
