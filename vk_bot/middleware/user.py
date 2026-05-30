from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from vkbottle.dispatch.middlewares import BaseMiddleware

from database.crud import VKUserCRUD
from vk_bot.middleware.pd_agreement import is_pd_exempt, send_pd_agreement_prompt


def extract_user_id(event: Any) -> int | None:
    """Извлекает ID пользователя VK из события."""

    if isinstance(event, dict):
        event_type = event.get('type')
        obj = event.get('object', {})
        if event_type == 'message_event':
            return obj.get('user_id')
        if event_type == 'message_new':
            return obj.get('message', {}).get('from_id')
        return None

    return getattr(event, 'from_id', None) or getattr(event, 'user_id', None)


def make_user_middleware(session_maker: async_sessionmaker, bot=None):
    """Фабрика middleware для загрузки пользователя VK из БД."""

    class UserMiddleware(BaseMiddleware):
        def __init__(self, event, view=None):
            super().__init__(event, view)
            self._session_ctx = None

        async def pre(self) -> None:
            user_id = extract_user_id(self.event)
            if user_id is None:
                return

            self._session_ctx = session_maker()
            session: AsyncSession = await self._session_ctx.__aenter__()
            user_crud = VKUserCRUD(session)
            user = await user_crud.get_or_create(vk_id=user_id)

            if not user.pd_agreed and not is_pd_exempt(self.event):
                api = bot.api if bot is not None else None
                await send_pd_agreement_prompt(self.event, api=api)
                await self._session_ctx.__aexit__(None, None, None)
                self._session_ctx = None
                self.stop('PD agreement required')
                return

            self.send(context_update={
                'user': user,
                'session': session,
                'user_crud': user_crud,
            })

        async def post(self) -> None:
            if self._session_ctx is not None:
                await self._session_ctx.__aexit__(None, None, None)

    return UserMiddleware


def make_bot_middleware(bot):
    """Фабрика middleware для доступа к экземпляру бота и state_dispenser."""

    class BotMiddleware(BaseMiddleware):
        async def pre(self) -> None:
            self.send(context_update={
                'bot': bot,
                'state_dispenser': bot.state_dispenser,
            })

    return BotMiddleware
