import random

from vkbottle.bot import MessageEvent
from vkbottle.dispatch.rules.base import FuncRule


def random_id() -> int:
    return random.randint(1, 2_147_483_647)


def action_rule(action: str) -> FuncRule:
    """Правило для inline-кнопок с указанным action в payload."""

    async def checker(event: MessageEvent) -> bool:
        payload = event.payload
        return isinstance(payload, dict) and payload.get('action') == action

    return FuncRule(checker)
