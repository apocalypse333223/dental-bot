"""
Запуск бота: python run_bot.py

Отдельный файл в корне проекта нужен для того, чтобы Python
правильно резолвил импорты вида `from app...` (запуск как модуль
из корня, а не изнутри пакета app/bot/).
"""

from app.bot.main import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
