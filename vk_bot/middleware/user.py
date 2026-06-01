from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from vkbottle import Bot
from vkbottle.dispatch.middlewares import BaseMiddleware

from database.crud import VKUserCRUD
from vk_bot.services.pd_agreement import PdAgreementService


class EventUserExtractor:
    """Извлечение VK user id из события."""

    @staticmethod
    def extract(event: Any) -> int | None:
        if isinstance(event, dict):
            event_type = event.get('type')
            obj = event.get('object', {})
            if event_type == 'message_event':
                return obj.get('user_id')
            if event_type == 'message_new':
                return obj.get('message', {}).get('from_id')
            return None

        return getattr(event, 'from_id', None) or getattr(event, 'user_id', None)


class UserMiddleware(BaseMiddleware):
    """Загрузка пользователя VK из БД и проверка согласия на ПДн."""

    _session_maker: async_sessionmaker | None = None
    _bot: Bot | None = None

    @classmethod
    def configure(cls, session_maker: async_sessionmaker, bot: Bot) -> None:
        cls._session_maker = session_maker
        cls._bot = bot

    def __init__(self, event, view=None):
        super().__init__(event, view)
        self._session_ctx = None

    async def pre(self) -> None:
        user_id = EventUserExtractor.extract(self.event)
        if user_id is None or self._session_maker is None:
            return

        self._session_ctx = self._session_maker()
        session: AsyncSession = await self._session_ctx.__aenter__()
        user_crud = VKUserCRUD(session)
        user = await user_crud.get_or_create(vk_id=user_id)

        if not user.pd_agreed and not PdAgreementService.is_exempt(self.event):
            api = self._bot.api if self._bot is not None else None
            await PdAgreementService.send_prompt(self.event, api=api)
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


class BotMiddleware(BaseMiddleware):
    """Передача экземпляра бота и state_dispenser в обработчики."""

    _bot: Bot | None = None

    @classmethod
    def configure(cls, bot: Bot) -> None:
        cls._bot = bot

    async def pre(self) -> None:
        if self._bot is None:
            return
        self.send(context_update={
            'bot': self._bot,
            'state_dispenser': self._bot.state_dispenser,
        })
