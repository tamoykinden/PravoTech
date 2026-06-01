from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import CategoryCRUD
from database.models import CaseCategory
from vk_bot.services.base import BaseService


class CategoryService(BaseService):
    """Сервис для работы с категориями."""

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.crud = CategoryCRUD(session)

    async def get_all_categories(self) -> List[CaseCategory]:
        return await self.crud.get_all()

    async def get_category_by_id(self, category_id: int) -> Optional[CaseCategory]:
        return await self.crud.get_by_id(category_id)
