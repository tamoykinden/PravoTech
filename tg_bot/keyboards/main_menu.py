from __future__ import annotations

from aiogram.types import KeyboardButton

from config import ButtonConfig
from tg_bot.keyboards.base import BaseReplyKeyboard


class MainMenuKeyboard(BaseReplyKeyboard):
    """Клавиатура главного меню."""

    def get_markup(self):
        """Возвращает готовую клавиатуру главного меню."""

        buttons = [
            [KeyboardButton(text=ButtonConfig.CASES)],
            [
                KeyboardButton(text=ButtonConfig.SEARCH),
                KeyboardButton(text=ButtonConfig.CATEGORIES),
            ],
            [KeyboardButton(text=ButtonConfig.FEEDBACK)],
        ]

        return self._build_reply_markup(buttons)
