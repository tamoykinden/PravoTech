from __future__ import annotations

import random
from typing import Any

from vkbottle.bot import MessageEvent
from vkbottle.dispatch.dispenser.builtin import BuiltinStateDispenser
from vkbottle.dispatch.rules.base import FuncRule


class VkDispatchSupport:
    """Вспомогательные методы для dispatch VK-бота."""

    RANDOM_ID_MAX = 2_147_483_647

    @classmethod
    def random_id(cls) -> int:
        return random.randint(1, cls.RANDOM_ID_MAX)

    @classmethod
    def sent_message_cmid(cls, response: Any) -> int | None:
        return getattr(response, 'conversation_message_id', None)

    @classmethod
    async def safe_delete_state(
        cls,
        state_dispenser: BuiltinStateDispenser,
        peer_id: int,
    ) -> None:
        if peer_id in state_dispenser.dictionary:
            await state_dispenser.delete(peer_id)

    @classmethod
    async def safe_send_empty_answer(cls, event: MessageEvent) -> None:
        try:
            await event.send_empty_answer()
        except Exception:
            pass

    @classmethod
    def action_rule(cls, action: str) -> FuncRule:
        async def checker(event: MessageEvent) -> bool:
            payload = event.payload
            return isinstance(payload, dict) and payload.get('action') == action

        return FuncRule(checker)
