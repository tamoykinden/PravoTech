"""Типизированный асинхронный клиент центрального API."""

from typing import Any

import httpx

from backend.schemas import CaseRead, CategoryRead, Platform, UserRead
from config import BackendConfig


class BackendError(RuntimeError):
    """Ошибка доступности или контракта центрального backend."""


class BackendClient:
    """Единая точка доступа бот-клиента к бизнес-данным."""

    def __init__(self, platform: Platform) -> None:
        self.platform = platform
        self._client = httpx.AsyncClient(
            base_url=f'{BackendConfig.URL}/api/v1/{platform}',
            headers={'X-API-Key': BackendConfig.client_api_key(platform)},
            timeout=httpx.Timeout(15.0, connect=5.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )

    async def close(self) -> None:
        """Закрывает пул HTTP-соединений."""

        await self._client.aclose()

    async def healthcheck(self) -> None:
        """Проверяет доступность backend перед запуском polling."""

        await self._request('GET', '/categories')

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = await self._client.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as error:
            detail = error.response.text[:300]
            raise BackendError(f'Backend вернул {error.response.status_code}: {detail}') from error
        except httpx.HTTPError as error:
            raise BackendError(f'Ошибка соединения с backend: {error}') from error

    async def get_or_create_user(self, external_id: int) -> UserRead:
        return UserRead.model_validate(await self._request('POST', f'/users/{external_id}'))

    async def update_consent(self, user_id: int, agreed: bool) -> UserRead:
        data = await self._request('PATCH', f'/users/{user_id}/consent', json={'agreed': agreed})
        return UserRead.model_validate(data)

    async def get_categories(self) -> list[CategoryRead]:
        return [CategoryRead.model_validate(item) for item in await self._request('GET', '/categories')]

    async def get_category(self, category_id: int) -> CategoryRead | None:
        return next((item for item in await self.get_categories() if item.id == category_id), None)

    async def get_cases(self, category_id: int | None = None) -> list[CaseRead]:
        params = {'category_id': category_id} if category_id is not None else None
        return [CaseRead.model_validate(item) for item in await self._request('GET', '/cases', params=params)]

    async def get_case(self, case_id: int) -> CaseRead:
        return CaseRead.model_validate(await self._request('GET', f'/cases/{case_id}'))

    async def search_cases(self, query: str) -> list[CaseRead]:
        data = await self._request('GET', '/cases/search', params={'q': query})
        return [CaseRead.model_validate(item) for item in data]

    async def create_feedback(self, user_id: int, message: str) -> None:
        await self._request('POST', '/feedback', json={'user_id': user_id, 'message': message})

    async def create_view(self, user_id: int, case_id: int) -> None:
        await self._request('POST', '/views', json={'user_id': user_id, 'case_id': case_id})

    async def download_document(self, document_id: int) -> bytes:
        """Получает документ через backend без доступа к хранилищу."""

        try:
            response = await self._client.get(f'/documents/{document_id}')
            response.raise_for_status()
            return response.content
        except httpx.HTTPError as error:
            raise BackendError(f'Не удалось получить документ: {error}') from error


class RemoteUserCRUD:
    """Совместимый фасад обновления пользователя для обработчиков."""

    def __init__(self, client: BackendClient) -> None:
        self.client = client

    async def update(self, user_id: int, **values: Any) -> UserRead:
        """Обновляет только разрешённое поле согласия."""

        if set(values) != {'pd_agreed'}:
            raise BackendError('Клиенту разрешено менять только согласие пользователя')
        return await self.client.update_consent(user_id, bool(values['pd_agreed']))
