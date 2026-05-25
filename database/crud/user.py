from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from database.crud.base import BaseCRUD
from database.models import User


class UserCRUD(BaseCRUD):
    """CRUD для пользователей."""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_or_create(self, telegram_id: int) -> User:
        """
        Получить пользователя по telegram_id или создать нового.
        При получении обновляет last_activity.
        """

        user = await self.get_by_telegram_id(telegram_id)
        if user:
            await self.update(user.id, last_activity=func.now())
            return user
        return await self.create(telegram_id=telegram_id)

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по telegram_id."""

        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
