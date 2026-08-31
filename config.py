"""
Единая точка загрузки конфигурации проекта.

Все настройки берутся из переменных окружения (.env файл).
Нигде в коде проекта не должно быть захардкоженных токенов/ключей —
только обращение к объекту `settings` из этого модуля.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Telegram
    bot_token: str

    # Database
    database_url: str = "sqlite+aiosqlite:///./dental_bot.db"

    # LLM API (используется начиная с этапа 3)
    llm_api_key: str = ""
    llm_api_base_url: str = ""
    llm_model: str = ""

    # Список telegram_id администраторов, через запятую в .env
    admin_telegram_ids: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def admin_ids_list(self) -> list[int]:
        """Преобразует строку "123,456" в список чисел [123, 456]."""
        if not self.admin_telegram_ids.strip():
            return []
        return [
            int(item.strip())
            for item in self.admin_telegram_ids.split(",")
            if item.strip()
        ]


# Единственный экземпляр настроек, который импортируется во всём проекте.
settings = Settings()
