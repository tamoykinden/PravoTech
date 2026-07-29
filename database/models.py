from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Computed,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database.base import Base


class TGUser(Base):
    """Модель пользователя Telegram."""

    __tablename__ = 'tg_users'

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
    pd_agreed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment='Согласие на обработку персональных данных'
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
    __table_args__ = (
        Index('ix_cases_search_vector', 'search_vector', postgresql_using='gin'),
    )

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
    tg_file_id: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment='Telegram file_id документа',
    )
    vk_attachment: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment='VK attachment для быстрой отправки (doc{owner_id}_{id})',
    )

    def __repr__(self) -> str:
        return f'Шаблон {self.title}'


class TGUserRequest(Base):
    """История просмотров кейсов пользователем Telegram."""

    __tablename__ = 'tg_user_requests'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey(TGUser.id),
        nullable=False,
        comment='Пользователь Telegram'
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


class TGFeedback(Base):
    """Модель обратной связи от пользователей Telegram."""

    __tablename__ = 'tg_feedback'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey(TGUser.id),
        nullable=False,
        comment='Пользователь Telegram'
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


class VKUser(Base):
    """Модель пользователя VK."""

    __tablename__ = 'vk_users'

    id: Mapped[int] = mapped_column(primary_key=True)
    vk_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, comment='ID пользователя VK')
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
    pd_agreed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment='Согласие на обработку персональных данных'
    )

    def __repr__(self) -> str:
        return f'Пользователь VK {self.id}'


class VKUserRequest(Base):
    """История просмотров кейсов пользователем VK."""

    __tablename__ = 'vk_user_requests'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey(VKUser.id),
        nullable=False,
        comment='Пользователь VK'
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
        return f'Запрос пользователя VK {self.user_id} к кейсу {self.case_id}'


class VKFeedback(Base):
    """Модель обратной связи от пользователей VK."""

    __tablename__ = 'vk_feedback'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey(VKUser.id),
        nullable=False,
        comment='Пользователь VK'
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
        return f'Обращение от пользователя VK {self.user_id}'
