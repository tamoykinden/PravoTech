import os
import tempfile
from pathlib import Path

import aiohttp
from vkbottle import ABCAPI

from backend.schemas import DocumentRead
from config import MessageConfig
from vk_bot.services.base import BaseService
from vk_bot.support.dispatch import VkDispatchSupport


class DocumentService(BaseService):
    """Сервис для работы с документами в VK."""

    def __init__(self, session):
        super().__init__(session)
        self.crud = self

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
            attachment = await self._upload_for_message(
                api,
                str(tmp_path),
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

    async def _upload_for_message(self, api: ABCAPI, file_path: str, peer_id: int, title: str) -> str:
        """Загружает файл через docs.getMessagesUploadServer с повторами."""
        token = api.token_generator.token if hasattr(api.token_generator, 'token') else api.token_generator.generate()

        async with aiohttp.ClientSession() as http:
            for attempt in range(3):
                try:
                    async with http.get('https://api.vk.com/method/docs.getMessagesUploadServer', params={
                        'access_token': token, 'v': '5.199', 'type': 'doc', 'peer_id': peer_id,
                    }) as resp:
                        data = await resp.json()
                        if 'error' in data:
                            raise RuntimeError(f"getMessagesUploadServer error: {data['error']}")
                        upload_url = data['response']['upload_url']

                    with open(file_path, 'rb') as f:
                        form = aiohttp.FormData()
                        form.add_field('file', f, filename=os.path.basename(file_path))
                        async with http.post(upload_url, data=form) as resp:
                            text = await resp.text()
                            import json
                            upload_result = json.loads(text)

                    async with http.get('https://api.vk.com/method/docs.save', params={
                        'access_token': token, 'v': '5.199',
                        'file': upload_result['file'], 'title': title,
                    }) as resp:
                        save_result = await resp.json()
                        if 'error' in save_result:
                            raise RuntimeError(f"docs.save error: {save_result['error']}")
                        doc = save_result['response']['doc']
                        return f"doc{doc['owner_id']}_{doc['id']}"

                except Exception as e:
                    if attempt < 2:
                        import asyncio
                        await asyncio.sleep(2)
                    else:
                        raise
