"""
Тонкая обёртка над LLM API.

Изолирует весь проект от конкретного SDK. Если завтра понадобится
сменить провайдера — менять нужно только этот файл.

Работает с любым OpenAI-совместимым API: достаточно указать
LLM_API_BASE_URL в .env, если провайдер не OpenAI.
"""

import logging

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    """Ленивая инициализация клиента (чтобы не падать при импорте без ключа)."""
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_api_base_url or None,
        )
    return _client


async def chat_completion(system_prompt: str, user_prompt: str) -> str:
    """
    Отправляет запрос к LLM и возвращает сырой текст ответа.

    Не занимается парсингом/валидацией JSON — это ответственность
    вызывающего кода (classifier.py).
    """
    client = get_client()

    response = await client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    content = response.choices[0].message.content
    if content is None:
        raise ValueError("LLM вернула пустой ответ")

    return content
