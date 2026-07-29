"""Безопасный поиск VK через backend."""

from backend.schemas import CaseRead
from vk_bot.services.base import BaseService


class SearchService(BaseService):
    """Сервис полнотекстового поиска кейсов."""

    async def search_cases(self, query: str) -> list[CaseRead]:
        if not query or len(query.strip()) < 2:
            return []
        return await self.session.search_cases(query.strip())
