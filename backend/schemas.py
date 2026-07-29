"""Валидируемые контракты клиентского API."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Platform = Literal['telegram', 'vk']


class ORMModel(BaseModel):
    """Базовая схема, читающая данные из SQLAlchemy-моделей."""

    model_config = ConfigDict(from_attributes=True)


class CategoryRead(ORMModel):
    """Категория правовых кейсов."""

    id: int
    name: str


class DocumentRead(ORMModel):
    """Метаданные шаблона документа без секретов хранилища."""

    id: int
    title: str
    case_id: int


class CaseRead(ORMModel):
    """Правовой кейс с прикреплёнными документами."""

    id: int
    title: str
    solution: str
    category_id: int
    documents: list[DocumentRead] = Field(default_factory=list)


class UserRead(ORMModel):
    """Пользователь клиентской платформы."""

    id: int
    external_id: int
    pd_agreed: bool
    registered_at: datetime


class ConsentUpdate(BaseModel):
    """Новое состояние согласия на обработку данных."""

    agreed: bool


class FeedbackCreate(BaseModel):
    """Обратная связь с ограничением размера входных данных."""

    user_id: int = Field(gt=0)
    message: str = Field(min_length=5, max_length=4000)


class ViewCreate(BaseModel):
    """Событие просмотра кейса."""

    user_id: int = Field(gt=0)
    case_id: int = Field(gt=0)


class StatusRead(BaseModel):
    """Результат операции без возвращаемых данных."""

    status: Literal['ok'] = 'ok'
