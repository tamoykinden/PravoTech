from typing import List, Optional

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

    async def get_vk_by_case(self, case_id: int) -> List[Document]:
        """Получить документы кейса, доступные для отправки в VK."""

        result = await self.session.execute(
            select(Document).where(
                Document.case_id == case_id,
                Document.vk_attachment.isnot(None),
            )
        )
        return result.scalars().all()

    async def set_vk_attachment(
        self,
        doc_id: int,
        vk_attachment: str,
    ) -> Optional[Document]:
        """Сохранить VK attachment после загрузки файла."""

        return await self.update(doc_id, vk_attachment=vk_attachment)
