import json
from typing import Any

from vkbottle import ABCAPI
from vkbottle.bot import Message, MessageEvent

from config import MessageConfig
from vk_bot.handlers.helpers import random_id
from vk_bot.keyboards.main_menu import PDAgreementKeyboard

PD_CALLBACK_ACTIONS = frozenset({'pd_agree', 'pd_disagree', 'pd_retry'})
START_TEXTS = frozenset({'/start', 'Начать', 'Старт', 'начать', 'старт'})
HELP_TEXTS = frozenset({'/help', 'Помощь', 'помощь'})


def _parse_payload(payload: Any) -> dict | None:
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, str):
        try:
            parsed = json.loads(payload)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None
    return None


def is_pd_exempt(event: Any) -> bool:
    """События, доступные без согласия на обработку ПДн."""

    if isinstance(event, dict):
        event_type = event.get('type')
        obj = event.get('object', {})

        if event_type == 'message_new':
            text = (obj.get('message') or {}).get('text', '').strip()
            return text in START_TEXTS or text in HELP_TEXTS

        if event_type == 'message_event':
            payload = _parse_payload(obj.get('payload'))
            return payload is not None and payload.get('action') in PD_CALLBACK_ACTIONS

        return False

    text = getattr(event, 'text', None)
    if text and text.strip() in START_TEXTS | HELP_TEXTS:
        return True

    payload = _parse_payload(getattr(event, 'payload', None))
    if payload and payload.get('action') in PD_CALLBACK_ACTIONS:
        return True

    return False


async def send_pd_agreement_prompt(event: Any, api: ABCAPI | None = None) -> None:
    """Отправляет пользователю запрос согласия на ПДн."""

    keyboard = PDAgreementKeyboard().get_markup()

    if isinstance(event, Message):
        await event.answer(
            MessageConfig.PD_AGREEMENT_TEXT,
            keyboard=keyboard,
            random_id=random_id(),
        )
        return

    if isinstance(event, MessageEvent):
        await event.send_empty_answer()
        await event.send_message(
            MessageConfig.PD_AGREEMENT_TEXT,
            keyboard=keyboard,
            random_id=random_id(),
        )
        return

    if isinstance(event, dict) and api is not None:
        obj = event.get('object', {})
        peer_id = obj.get('peer_id') or obj.get('user_id')
        if peer_id is None:
            return
        await api.messages.send(
            peer_id=peer_id,
            message=MessageConfig.PD_AGREEMENT_TEXT,
            keyboard=keyboard,
            random_id=random_id(),
        )
