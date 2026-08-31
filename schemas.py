"""
Схема данных, которую мы ожидаем получить от LLM.

Используем Pydantic для валидации: если модель вернёт "кривой" JSON
или несуществующую категорию — мы это поймаем на этапе валидации,
а не где-то глубже в коде.
"""

from enum import StrEnum

from pydantic import BaseModel, Field


class MessageCategory(StrEnum):
    APPOINTMENT = "appointment"
    RESCHEDULE = "reschedule"
    CANCEL = "cancel"
    PRICE = "price"
    SERVICES = "services"
    GENERAL = "general"
    OTHER = "other"


class ClassificationResult(BaseModel):
    category: MessageCategory
    summary: str = Field(max_length=500)
    needs_human: bool
