from __future__ import annotations

from aiogram.types import KeyboardButton

from tg_bot.keyboards.base import BaseReplyKeyboard


class BackKeyboard(BaseReplyKeyboard):
    """Клавиатура с кнопкой 'Назад'."""

    def get_markup(self):
        """Возвращает готовую клавиатуру с кнопкой 'Назад'."""

        buttons = [[KeyboardButton(text='🔙 Назад')]]
        return self._build_reply_markup(buttons)