from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from database.crud.base import BaseCRUD
from database.models import TGUser, TGUserRequest, VKUser, VKUserRequest


class TGUserCRUD(BaseCRUD):
    """CRUD для пользователей Telegram."""

    def __init__(self, session: AsyncSession):
        super().__init__(TGUser, session)

    async def get_or_create(self, telegram_id: int) -> TGUser:
        """Получить пользователя по telegram_id или создать нового."""

        user = await self.get_by_telegram_id(telegram_id)
        if user:
            await self.update(user.id, last_activity=func.now())
            return user
        return await self.create(telegram_id=telegram_id)

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[TGUser]:
        """Получить пользователя по telegram_id."""

        result = await self.session.execute(
            select(TGUser).where(TGUser.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()


class VKUserCRUD(BaseCRUD):
    """CRUD для пользователей VK."""

    def __init__(self, session: AsyncSession):
        super().__init__(VKUser, session)

    async def get_or_create(self, vk_id: int) -> VKUser:
        """Получить пользователя по vk_id или создать нового."""

        user = await self.get_by_vk_id(vk_id)
        if user:
            await self.update(user.id, last_activity=func.now())
            return user
        return await self.create(vk_id=vk_id)

    async def get_by_vk_id(self, vk_id: int) -> Optional[VKUser]:
        """Получить пользователя по vk_id."""

        result = await self.session.execute(
            select(VKUser).where(VKUser.vk_id == vk_id)
        )
        return result.scalar_one_or_none()


class TGUserRequestCRUD(BaseCRUD):
    """CRUD для истории просмотров кейсов пользователями Telegram."""

    def __init__(self, session: AsyncSession):
        super().__init__(TGUserRequest, session)

    async def create_request(self, user_id: int, case_id: int) -> TGUserRequest:
        """Записать просмотр кейса."""

        return await self.create(user_id=user_id, case_id=case_id)


class VKUserRequestCRUD(BaseCRUD):
    """CRUD для истории просмотров кейсов пользователями VK."""

    def __init__(self, session: AsyncSession):
        super().__init__(VKUserRequest, session)

    async def create_request(self, user_id: int, case_id: int) -> VKUserRequest:
        """Записать просмотр кейса."""

        return await self.create(user_id=user_id, case_id=case_id)


UserCRUD = TGUserCRUD
