from __future__ import annotations

from typing import Optional

from aiogram import Bot
from aiogram.types import Message


class BaseHandlers:
    """
    Базовый класс для всех обработчиков бота.

    Содержит общие методы для удаления сообщений.
    """

    async def safe_delete_message(self, bot: Bot, chat_id: int, message_id: int) -> bool:
        """
        Безопасно удаляет сообщение, игнорируя ошибки.

        Args:
            bot: Экземпляр бота.
            chat_id: ID чата.
            message_id: ID сообщения для удаления.

        Returns:
            True если удаление успешно, False в противном случае.
        """

        try:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
            return True
        except Exception:
            return False

    async def cleanup_current_and_previous(self, message: Message, bot: Optional[Bot] = None) -> None:
        """Удаляет текущее сообщение пользователя и предыдущее сообщение бота."""

        try:
            await message.delete()
        except Exception:
            pass

        effective_bot = bot or message.bot
        await self.safe_delete_message(
            effective_bot,
            chat_id=message.chat.id,
            message_id=message.message_id - 1,
        )
