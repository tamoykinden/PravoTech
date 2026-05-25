from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker

from database.crud import UserCRUD


class UserMiddleware(BaseMiddleware):
    """Middleware для загрузки пользователя из БД."""

    def __init__(self, session_maker: async_sessionmaker):
        """
        Инициализация middleware.

        Args:
            session_maker: Фабрика для создания сессий БД.
        """

        self.session_maker = session_maker
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

        async with self.session_maker() as session:
            user_crud = UserCRUD(session)
            user = await user_crud.get_or_create(telegram_id=telegram_id)

            data['user'] = user
            data['session'] = session
            data['user_crud'] = user_crud

            return await handler(event, data)
