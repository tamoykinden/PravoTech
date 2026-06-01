from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from vkbottle.bot import Message

if TYPE_CHECKING:
    from vkbottle.bot import MessageEvent

from vk_bot.keyboards.main_menu import MainMenuKeyboard
from vk_bot.support.dispatch import VkDispatchSupport


class BaseHandlers:
    """Базовый класс для всех обработчиков VK-бота."""

    async def safe_answer_event(self, event: MessageEvent) -> None:
        await VkDispatchSupport.safe_send_empty_answer(event)

    async def _delete_by_cmid(
        self,
        api,
        peer_id: int,
        conversation_message_id: int,
    ) -> bool:
        try:
            await api.messages.delete(
                peer_id=peer_id,
                cmids=[conversation_message_id],
                delete_for_all=True,
            )
            return True
        except Exception:
            return False

    async def safe_delete_message(
        self,
        message: Message,
        conversation_message_id: int,
    ) -> bool:
        return await self._delete_by_cmid(
            message.ctx_api,
            message.peer_id,
            conversation_message_id,
        )

    async def safe_delete_event_message(self, event: MessageEvent) -> bool:
        if not event.conversation_message_id:
            return False
        return await self._delete_by_cmid(
            event.ctx_api,
            event.peer_id,
            event.conversation_message_id,
        )

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
        return await message.answer(
            text,
            keyboard=keyboard,
            random_id=VkDispatchSupport.random_id(),
        )

    async def send_inline_message(
        self,
        message: Message,
        text: str,
        keyboard: str,
    ):
        """Отправляет одно сообщение с inline-клавиатурой (reply-меню скрывается через one_time)."""

        return await message.answer(
            text,
            keyboard=keyboard,
            random_id=VkDispatchSupport.random_id(),
        )

    async def restore_main_menu(
        self,
        peer_id: int,
        api,
        text: str,
    ):
        """Восстанавливает reply-клавиатуру главного меню."""

        await api.messages.send(
            peer_id=peer_id,
            message=text,
            keyboard=MainMenuKeyboard().get_markup(),
            random_id=VkDispatchSupport.random_id(),
        )
