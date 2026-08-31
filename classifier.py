"""
Классификация сообщений пациента через AI.

Ключевой принцип безопасности: если LLM вернула что-то, что не удалось
распарсить/провалидировать — НЕ падаем и НЕ теряем сообщение, а
возвращаем безопасный fallback: category="other", needs_human=True.
Лучше лишний раз побеспокоить администратора, чем потерять заявку
или показать пациенту ошибку.
"""

import json
import logging

from pydantic import ValidationError

from app.ai.client import chat_completion
from app.ai.prompts import SYSTEM_PROMPT, build_user_prompt
from app.ai.schemas import ClassificationResult, MessageCategory

logger = logging.getLogger(__name__)


def _fallback_result(reason: str) -> ClassificationResult:
    logger.warning("Использую fallback-классификацию: %s", reason)
    return ClassificationResult(
        category=MessageCategory.OTHER,
        summary="Не удалось автоматически классифицировать сообщение",
        needs_human=True,
    )


def _strip_markdown_fences(raw: str) -> str:
    """LLM иногда оборачивает JSON в ```json ... ``` несмотря на просьбу не делать этого."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    return text.strip()


async def classify_message(patient_message: str) -> ClassificationResult:
    """
    Классифицирует сообщение пациента через LLM.

    Всегда возвращает валидный ClassificationResult — либо реальный
    результат от AI, либо безопасный fallback при любой ошибке.
    """
    user_prompt = build_user_prompt(patient_message)

    try:
        raw_response = await chat_completion(SYSTEM_PROMPT, user_prompt)
    except Exception:
        logger.exception("Ошибка при обращении к LLM API")
        return _fallback_result("ошибка вызова LLM API")

    cleaned = _strip_markdown_fences(raw_response)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("LLM вернула невалидный JSON: %r", raw_response)
        return _fallback_result("невалидный JSON от LLM")

    try:
        return ClassificationResult.model_validate(data)
    except ValidationError as e:
        logger.warning("LLM вернула JSON, не прошедший валидацию: %s", e)
        return _fallback_result("JSON не прошёл валидацию схемы")
