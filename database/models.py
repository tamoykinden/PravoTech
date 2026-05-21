import datetime

from sqlalchemy import BigInteger, Computed, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database.base import Base


class User(Base):
    """Модель пользователя."""

    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, comment='ID пользователя в Telegram')
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment='Дата и время регистрации'
    )
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment='Последняя активность'
    )

    def __repr__(self) -> str:
        return f'Пользователь {self.id}'


class CaseCategory(Base):
    """Модель категории кейсов."""

    __tablename__ = 'case_categories'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        comment='Название категории'
    )

    def __repr__(self) -> str:
        return f'Категория {self.name}'


class Case(Base):
    """Кейс (пошаговое решение)."""

    __tablename__ = 'cases'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment='Название кейса'
    )
    solution: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Пошаговое решение с ссылками на НПА'
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey(CaseCategory.id),
        nullable=False,
        comment='Категория'
    )
    search_vector: Mapped[TSVECTOR] = mapped_column(
        TSVECTOR,
        Computed(
            "to_tsvector('russian', coalesce(title, '') || ' ' || coalesce(solution, ''))",
            persisted=True
        ),
        nullable=True
    )

    def __repr__(self) -> str:
        return f'Кейс {self.title}'


class Document(Base):
    """Модель шаблона документов."""

    __tablename__ = 'documents'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment='Название шаблона'
    )
    case_id: Mapped[int] = mapped_column(
        ForeignKey(Case.id),
        nullable=False,
        comment='Кейс'
    )
    file_id: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment='Telegram file_id документа'
    )

    def __repr__(self) -> str:
        return f'Шаблон {self.title}'


class UserRequest(Base):
    """История просмотров кейсов пользователем."""

    __tablename__ = 'user_requests'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey(User.id),
        nullable=False,
        comment='Пользователь'
    )
    case_id: Mapped[int] = mapped_column(
        ForeignKey(Case.id),
        nullable=False,
        comment='Кейс'
    )
    viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment='Дата и время просмотра'
    )

    def __repr__(self) -> str:
        return f'Запрос пользователя {self.user_id} к кейсу {self.case_id}'


class Feedback(Base):
    """Модель обратной связи от пользователей."""

    __tablename__ = 'feedback'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey(User.id),
        nullable=False,
        comment='Пользователь'
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Текст обращения'
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment='Дата и время отправки'
    )

    def __repr__(self) -> str:
        return f'Обращение от пользователя {self.user_id}'
