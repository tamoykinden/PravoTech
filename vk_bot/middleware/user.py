from __future__ import annotations

from typing import Any

from vkbottle import Bot
from vkbottle.dispatch.middlewares import BaseMiddleware

from bot_client import BackendClient, RemoteUserCRUD
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

    _backend: BackendClient | None = None
    _bot: Bot | None = None

    @classmethod
    def configure(cls, backend: BackendClient, bot: Bot) -> None:
        cls._backend = backend
        cls._bot = bot

    def __init__(self, event, view=None):
        super().__init__(event, view)

    async def pre(self) -> None:
        user_id = EventUserExtractor.extract(self.event)
        if user_id is None or self._backend is None:
            return
        user = await self._backend.get_or_create_user(user_id)

        if not user.pd_agreed and not PdAgreementService.is_exempt(self.event):
            api = self._bot.api if self._bot is not None else None
            await PdAgreementService.send_prompt(self.event, api=api)
            self.stop('PD agreement required')
            return

        self.send(context_update={
            'user': user,
            'session': self._backend,
            'user_crud': RemoteUserCRUD(self._backend),
        })

    async def post(self) -> None:
        return None


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
