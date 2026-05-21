from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.base import BaseCRUD
from database.models import Case


class CaseCRUD(BaseCRUD):
    """CRUD для кейсов."""

    def __init__(self, session: AsyncSession):
        super().__init__(Case, session)

    async def get_by_category(self, category_id: int) -> List[Case]:
        """Получить все кейсы по категории."""

        result = await self.session.execute(
            select(Case).where(Case.category_id == category_id)
        )
        return result.scalars().all()
