"""Получение кейсов Telegram через backend."""

from backend.schemas import CaseRead, DocumentRead
from tg_bot.services.base import BaseService


class CaseService(BaseService):
    """Сервис работы с правовыми кейсами."""

    async def get_all_cases(self) -> list[CaseRead]:
        return await self.session.get_cases()

    async def get_cases_by_category(self, category_id: int) -> list[CaseRead]:
        return await self.session.get_cases(category_id)

    async def get_case_with_documents(self, case_id: int) -> tuple[CaseRead, list[DocumentRead]]:
        case = await self.session.get_case(case_id)
        return case, case.documents

    async def format_case_text(self, case: CaseRead) -> str:
        return f'<b>{case.title}</b>\n\n{case.solution}'
