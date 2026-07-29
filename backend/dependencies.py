"""Зависимости FastAPI для БД и авторизации клиентов."""

import hmac
from collections.abc import AsyncIterator

from fastapi import Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas import Platform
from config import BackendConfig


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Выдаёт транзакционную сессию БД на время одного запроса."""

    async with request.app.state.database.session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def require_client(
    platform: Platform,
    x_api_key: str = Header(default='', alias='X-API-Key'),
) -> Platform:
    """Проверяет отдельный ключ клиента с constant-time сравнением."""

    try:
        expected = BackendConfig.client_api_key(platform)
    except ValueError as error:
        raise HTTPException(status_code=503, detail='Клиент API не настроен') from error
    if not x_api_key or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Неверный API-ключ',
        )
    return platform
