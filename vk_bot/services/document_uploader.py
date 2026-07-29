"""Безопасная загрузка документов во вложения сообщений VK."""

import asyncio
from pathlib import Path
from urllib.parse import urlparse

import aiohttp
from vkbottle import ABCAPI


class VKDocumentUploadError(RuntimeError):
    """Документ не удалось загрузить в VK."""


class VKMessageDocumentUploader:
    """Загружает документ через API-объект VK без прямого доступа к токену."""

    def __init__(self, attempts: int = 3, retry_delay: float = 2.0) -> None:
        if attempts < 1:
            raise ValueError('Количество попыток должно быть положительным')
        self._attempts = attempts
        self._retry_delay = retry_delay

    async def upload(
        self,
        api: ABCAPI,
        file_path: Path,
        peer_id: int,
        title: str,
    ) -> str:
        """Загружает DOCX и возвращает attachment вида ``docOWNER_ID_ID``."""

        for attempt in range(self._attempts):
            try:
                return await self._upload_once(api, file_path, peer_id, title)
            except Exception:
                if attempt + 1 == self._attempts:
                    raise VKDocumentUploadError(
                        'Не удалось загрузить документ в VK'
                    ) from None
                await asyncio.sleep(self._retry_delay)

        raise VKDocumentUploadError('Не удалось загрузить документ в VK')

    async def _upload_once(
        self,
        api: ABCAPI,
        file_path: Path,
        peer_id: int,
        title: str,
    ) -> str:
        server = await api.request(
            'docs.getMessagesUploadServer',
            {'type': 'doc', 'peer_id': peer_id},
        )
        upload_url = server['response']['upload_url']
        parsed_url = urlparse(upload_url)
        if parsed_url.scheme != 'https' or not parsed_url.hostname:
            raise VKDocumentUploadError(
                'VK вернул небезопасный адрес загрузки'
            )

        timeout = aiohttp.ClientTimeout(total=60, connect=10)
        async with aiohttp.ClientSession(timeout=timeout) as http:
            with file_path.open('rb') as source:
                form = aiohttp.FormData()
                form.add_field(
                    'file',
                    source,
                    filename=file_path.name,
                    content_type=(
                        'application/vnd.openxmlformats-officedocument.'
                        'wordprocessingml.document'
                    ),
                )
                async with http.post(upload_url, data=form) as response:
                    if response.status != 200:
                        raise VKDocumentUploadError(
                            'Сервер загрузки VK отклонил документ'
                        )
                    upload_result = await response.json(content_type=None)

        saved = await api.request(
            'docs.save',
            {
                'file': upload_result['file'],
                'title': title,
            },
        )
        document = saved['response']['doc']
        return f"doc{document['owner_id']}_{document['id']}"
