from __future__ import annotations

import json
from typing import Any

from vkbottle import ABCAPI
from vkbottle.bot import Message, MessageEvent

from config import MenuConfig, MessageConfig, PdConfig
from vk_bot.keyboards.main_menu import PDAgreementKeyboard
from vk_bot.support.dispatch import VkDispatchSupport


class PdAgreementService:
    """Согласие на обработку ПДн для VK-бота."""

    @classmethod
    def parse_payload(cls, payload: Any) -> dict | None:
        if isinstance(payload, dict):
            return payload
        if isinstance(payload, str):
            try:
                parsed = json.loads(payload)
                return parsed if isinstance(parsed, dict) else None
            except json.JSONDecodeError:
                return None
        return None

    @classmethod
    def is_exempt(cls, event: Any) -> bool:
        if isinstance(event, dict):
            event_type = event.get('type')
            obj = event.get('object', {})

            if event_type == 'message_new':
                text = (obj.get('message') or {}).get('text', '').strip()
                return text in MenuConfig.START_TEXTS | MenuConfig.HELP_TEXTS

            if event_type == 'message_event':
                payload = cls.parse_payload(obj.get('payload'))
                return (
                    payload is not None
                    and payload.get('action') in PdConfig.CALLBACK_ACTIONS
                )

            return False

        text = getattr(event, 'text', None)
        if text and text.strip() in MenuConfig.START_TEXTS | MenuConfig.HELP_TEXTS:
            return True

        payload = cls.parse_payload(getattr(event, 'payload', None))
        return payload is not None and payload.get('action') in PdConfig.CALLBACK_ACTIONS

    @classmethod
    async def send_prompt(cls, event: Any, api: ABCAPI | None = None) -> None:
        keyboard = PDAgreementKeyboard().get_markup()

        if isinstance(event, Message):
            await event.answer(
                MessageConfig.PD_AGREEMENT_TEXT,
                keyboard=keyboard,
                random_id=VkDispatchSupport.random_id(),
            )
            return

        if isinstance(event, MessageEvent):
            await VkDispatchSupport.safe_send_empty_answer(event)
            await event.send_message(
                MessageConfig.PD_AGREEMENT_TEXT,
                keyboard=keyboard,
                random_id=VkDispatchSupport.random_id(),
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
                random_id=VkDispatchSupport.random_id(),
            )
