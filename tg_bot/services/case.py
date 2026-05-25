from typing import List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import CaseCRUD, DocumentCRUD
from database.models import Case, Document
from tg_bot.services.base import BaseService


class CaseService(BaseService):
    """Сервис для работы с кейсами."""

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.case_crud = CaseCRUD(session)
        self.document_crud = DocumentCRUD(session)

    async def get_all_cases(self) -> List[Case]:
        """Получить все кейсы."""

        return await self.case_crud.get_all()

    async def get_cases_by_category(self, category_id: int) -> List[Case]:
        """Получить кейсы по категории."""

        return await self.case_crud.get_by_category(category_id)

    async def get_case_with_documents(self, case_id: int) -> Tuple[Case, List[Document]]:
        """Получить кейс и его документы."""

        case = await self.case_crud.get_by_id(case_id)
        documents = await self.document_crud.get_by_case(case_id)
        return case, documents

    async def format_case_text(self, case: Case) -> str:
        """Форматирует текст кейса для отправки."""

        return f'<b>{case.title}</b>\n\n{case.solution}'
