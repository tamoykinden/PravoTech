from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from database.models import User


class UserCRUD:
    """CRUD операции для модели User."""

    def __init__(self, session: AsyncSession):
        """
        Инициализация CRUD для пользователей.

        Args:
            session: Сессия SQLAlchemy для работы с БД.
        """

        self.session = session

    async def get_or_create(self, telegram_id: int) -> User:
        """
        Получить пользователя по telegram_id или создать нового.

        Если пользователь существует, обновляет last_activity.

        Если пользователя нет создает нового.

        Args:
            telegram_id: ID пользователя в Telegram.

        Returns:
            User: Объект пользователя.
        """

        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            stmt = (
                update(User)
                .where(User.telegram_id == telegram_id)
                .values(last_activity=func.now())
            )

            await self.session.execute(stmt)
            await self.session.commit()

            result = await self.session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
        else:
            user = User(telegram_id=telegram_id)
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)

        return user

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Получить пользователя по его ID в БД.

        Args:
            user_id: ID пользователя в базе данных.

        Returns:
            User or None: Объект пользователя или None, если не найден.
        """

        return await self.session.get(User, user_id)

    async def update_activity(self, user_id: int) -> None:
        """
        Обновить время последней активности пользователя.

        Args:
            user_id: ID пользователя в базе данных.
        """

        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(last_activity=func.now())
        )
        await self.session.execute(stmt)
        await self.session.commit()
