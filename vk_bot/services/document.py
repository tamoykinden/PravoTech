import tempfile
from pathlib import Path

from vkbottle import ABCAPI

from backend.schemas import DocumentRead
from bot_client import BackendClient
from config import MessageConfig
from vk_bot.services.base import BaseService
from vk_bot.services.document_uploader import VKMessageDocumentUploader
from vk_bot.support.dispatch import VkDispatchSupport


class DocumentService(BaseService):
    """Сервис для работы с документами в VK."""

    def __init__(self, session: BackendClient):
        super().__init__(session)
        self._uploader = VKMessageDocumentUploader()

    async def get_vk_documents(self, case_id: int) -> list[DocumentRead]:
        return (await self.session.get_case(case_id)).documents

    async def get_by_id(self, document_id: int) -> DocumentRead | None:
        """Находит документ по метаданным доступных кейсов."""

        cases = await self.session.get_cases()
        return next((doc for case in cases for doc in case.documents if doc.id == document_id), None)

    async def send_document(
        self,
        api: ABCAPI,
        peer_id: int,
        document: DocumentRead,
    ) -> None:
        """Получает документ из backend и загружает его в VK."""

        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            tmp_path.write_bytes(await self.session.download_document(document.id))
            attachment = await self._uploader.upload(
                api,
                tmp_path,
                peer_id,
                document.title,
            )
        finally:
            tmp_path.unlink(missing_ok=True)

        await api.messages.send(
            peer_id=peer_id,
            message=MessageConfig.DOCUMENT_TITLE.format(title=document.title),
            attachment=attachment,
            random_id=VkDispatchSupport.random_id(),
        )
