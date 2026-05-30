from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from vkbottle import ABCAPI
from vkbottle.tools import DocUploader

from database.crud import DocumentCRUD
from database.models import Document
from vk_bot.handlers.helpers import random_id
from vk_bot.services.base import BaseService


class DocumentService(BaseService):
    """Сервис для работы с документами в VK."""

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.crud = DocumentCRUD(session)

    async def get_vk_documents(self, case_id: int) -> list[Document]:
        return await self.crud.get_vk_by_case(case_id)

    async def send_document(
        self,
        api: ABCAPI,
        peer_id: int,
        document: Document,
    ) -> None:
        """
        Отправляет документ по сохранённому VK attachment.

        Файл уже лежит в документах VK — повторная загрузка не нужна.
        """
        if not document.vk_attachment:
            raise ValueError('У документа не задан vk_attachment')

        await api.messages.send(
            peer_id=peer_id,
            message=f'📄 {document.title}',
            attachment=document.vk_attachment,
            random_id=random_id(),
        )

    async def upload_to_vk(
        self,
        api: ABCAPI,
        file_path: str,
        group_id: int,
        title: Optional[str] = None,
    ) -> str:
        """
        Одноразовая загрузка файла в документы сообщества VK.

        Returns:
            Строка attachment вида doc{owner_id}_{id} для сохранения в БД.
        """
        uploader = DocUploader(api)
        return await uploader.upload(
            file_path,
            group_id=group_id,
            title=title,
        )

    async def upload_and_save(
        self,
        api: ABCAPI,
        doc_id: int,
        file_path: str,
        group_id: int,
    ) -> Document:
        """Загружает файл в VK и сохраняет attachment в БД."""

        document = await self.crud.get_by_id(doc_id)
        if not document:
            raise ValueError(f'Документ {doc_id} не найден')

        attachment = await self.upload_to_vk(
            api,
            file_path,
            group_id=group_id,
            title=document.title,
        )
        updated = await self.crud.set_vk_attachment(doc_id, attachment)
        if not updated:
            raise ValueError(f'Не удалось сохранить attachment для документа {doc_id}')
        return updated
