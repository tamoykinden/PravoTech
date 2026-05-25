from __future__ import annotations

from aiogram.types import KeyboardButton

from config import ButtonConfig
from tg_bot.keyboards.base import BaseReplyKeyboard


class BackKeyboard(BaseReplyKeyboard):
    """Клавиатура с кнопкой 'Назад'."""

    def get_markup(self):
        """Возвращает готовую клавиатуру с кнопкой 'Назад'."""

        buttons = [[KeyboardButton(text=ButtonConfig.BACK)]]
        return self._build_reply_markup(buttons)
