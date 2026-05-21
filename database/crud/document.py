from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.base import BaseCRUD
from database.models import Document


class DocumentCRUD(BaseCRUD):
    """CRUD для документов."""

    def __init__(self, session: AsyncSession):
        super().__init__(Document, session)

    async def get_by_case(self, case_id: int) -> List[Document]:
        """Получить все документы по кейсу."""

        result = await self.session.execute(
            select(Document).where(Document.case_id == case_id)
        )
        return result.scalars().all()
