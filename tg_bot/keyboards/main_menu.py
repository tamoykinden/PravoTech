from __future__ import annotations

from aiogram.types import KeyboardButton

from tg_bot.keyboards.base import BaseReplyKeyboard


class MainMenuKeyboard(BaseReplyKeyboard):
    """Клавиатура главного меню."""

    def get_markup(self):
        """Возвращает готовую клавиатуру главного меню."""

        buttons = [
            [KeyboardButton(text='Список кейсов')],
            [
                KeyboardButton(text='Поиск кейса'),
                KeyboardButton(text='Категории'),
            ],
            [KeyboardButton(text='Обратная связь')],
        ]

        return self._build_reply_markup(buttons)
