from typing import List

from sqlalchemy import select
from sqlalchemy.sql import func

from database.models import Case
from vk_bot.services.base import BaseService


class SearchService(BaseService):
    """Сервис для полнотекстового поиска кейсов."""

    async def search_cases(self, query: str) -> List[Case]:
        if not query or len(query.strip()) < 2:
            return []

        words = query.strip().split()
        tsquery = ' & '.join(words)

        stmt = (
            select(Case)
            .where(
                Case.search_vector.op('@@')(func.to_tsquery('russian', tsquery))
            )
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()
