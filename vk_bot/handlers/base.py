from __future__ import annotations

from typing import Optional

from vkbottle.bot import Message


class BaseHandlers:
    """Базовый класс для всех обработчиков VK-бота."""

    async def safe_delete_message(
        self,
        message: Message,
        conversation_message_id: int,
    ) -> bool:
        try:
            await message.ctx_api.messages.delete(
                peer_id=message.peer_id,
                cmids=[conversation_message_id],
                delete_for_all=True,
            )
            return True
        except Exception:
            return False

    async def cleanup_current_and_previous(self, message: Message) -> None:
        """Удаляет текущее сообщение пользователя и предыдущее сообщение бота."""

        if message.conversation_message_id:
            await self.safe_delete_message(message, message.conversation_message_id)

        if message.conversation_message_id and message.conversation_message_id > 1:
            await self.safe_delete_message(
                message,
                message.conversation_message_id - 1,
            )

    async def send_message(
        self,
        message: Message,
        text: str,
        keyboard: Optional[str] = None,
    ):
        from vk_bot.handlers.helpers import random_id

        return await message.answer(text, keyboard=keyboard, random_id=random_id())
