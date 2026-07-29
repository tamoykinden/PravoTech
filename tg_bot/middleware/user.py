from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot_client import BackendClient, RemoteUserCRUD


class UserMiddleware(BaseMiddleware):
    """Middleware для загрузки пользователя из БД."""

    def __init__(self, backend: BackendClient):
        """
        Инициализация middleware.

        Args:
            backend: Авторизованный клиент центрального API.
        """

        self.backend = backend
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Обработка входящего события.

        Args:
            - handler: Функция-обработчик следующего уровня;
            - event: Событие от Telegram;
            - data: Словарь с данными.

        Returns:
            Any: Результат вызова обработчика.
        """

        if isinstance(event, (Message, CallbackQuery)):
            telegram_id = event.from_user.id
        else:
            return await handler(event, data)

        user = await self.backend.get_or_create_user(telegram_id)
        data['user'] = user
        data['session'] = self.backend
        data['user_crud'] = RemoteUserCRUD(self.backend)
        return await handler(event, data)
